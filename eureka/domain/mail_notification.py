# -*- coding: utf-8 -*-
# =-
# Copyright Solocal Group (2015)
#
# eureka@solocal.com
#
# This software is a computer program whose purpose is to provide a full
# featured participative innovation solution within your organization.
#
# This software is governed by the CeCILL license under French law and
# abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# "http://www.cecill.info".
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and,  more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.
# =-

import os
import re
from lxml import etree
from datetime import datetime

from nagare.namespaces import xhtml
from nagare.i18n import _, format_date

from eureka.pkg import resource_stream
from eureka.infrastructure import mail
from eureka.infrastructure.urls import get_url_service
from eureka.infrastructure.tools import text_to_html, Enum


class DeliveryPriority(Enum):
    Low = "low"
    Normal = "normal"


# FIXME: all mails are sent in the author's locale instead of the target mail recipient locale. This should be fixed
def send(template_filename, to, delivery_priority=DeliveryPriority.Normal, attachments=None, **kw):
    from eureka.domain.models import MailDeliveryFrequency
    from eureka.domain.repositories import UserRepository

    user_repository = UserRepository()

    locale = to.locale if to else 'fr'

    # creates the email contents
    substitutions = _get_substitutions(to=to, **kw)
    content = _perform_substitutions(template_filename, locale, substitutions)

    # extracts and remove the metadata
    content, subject, sender, to_recipients, cc_recipients, bcc_recipients = _extract_metadata(content)

    # attachments
    attachments = attachments or ()

    # if there's no recipient, no need to send an email
    if not to_recipients:
        return

    mailer = mail.get_mailer()

    if (delivery_priority == DeliveryPriority.Normal) or attachments:
        # FIXME: for consistency, we should also send one email per recipient, using the target user locale
        # send now (one message with all the recipients)
        mailer.send_mail(subject, from_=sender, to=to_recipients, cc=cc_recipients, bcc=bcc_recipients,
                         content=content, type='html', attachments=attachments)
    elif delivery_priority == DeliveryPriority.Low:
        # send one message per user (since we need the examine the mail delivery setting of each user)
        for user_email in to_recipients + cc_recipients + bcc_recipients:
            user = user_repository.get_by_email(unicode(user_email))
            send_now = not user or user.mail_delivery_frequency == MailDeliveryFrequency.Immediately

            if send_now:
                # sends the email now
                mailer.send_mail(subject, from_=sender, to=[user_email], content=content, type='html')
            else:
                # add the message to the user's pending email messages
                user.add_pending_email_message(subject, content)


def _extract_metadata(content):
    tree = etree.fromstring(content)
    ns = {'xhtml': 'http://www.w3.org/1999/xhtml'}
    subject = tree.xpath('//xhtml:title', namespaces=ns)[0].text

    metadata_nodes = tree.xpath('//xhtml:meta', namespaces=ns)
    metadata_nodes = [n for n in metadata_nodes if 'name' in n.attrib]
    metadata = {}
    for node in metadata_nodes:
        metadata[node.attrib['name']] = node.attrib['content']

    for n in metadata_nodes:
        n.getparent().remove(n)

    content = etree.tostring(tree, pretty_print=True, encoding=unicode)

    sender = metadata.get('mail-sender', u'')
    to_recipients_txt = metadata.get('mail-to-recipients', u'')
    cc_recipients_txt = metadata.get('mail-cc-recipients', u'')
    bcc_recipients_txt = metadata.get('mail-bcc-recipients', u'')
    to_recipients = filter(None, re.split(r'\s*,\s*', to_recipients_txt))
    cc_recipients = filter(None, re.split(r'\s*,\s*', cc_recipients_txt))
    bcc_recipients = filter(None, re.split(r'\s*,\s*', bcc_recipients_txt))

    return content, subject, sender, to_recipients, cc_recipients, bcc_recipients


def render_link(name, url):
    r = xhtml.Renderer()
    link = r.a(name, href=url)
    return link.write_htmlstring(encoding=unicode)


def _get_substitutions(to, comment=None, idea=None, fi=None, previous_di=None, comment_author=None, **kw):

    # initialize useful values for substitutions
    base_url = get_url_service().base_url
    shop_url = get_url_service().expand_url(['shop'], relative=False)
    idea_url = get_url_service().expand_url(['idea', idea.id], relative=False) if idea else u''

    fi = fi or (idea.wf_context.assignated_fi if idea else None)
    di = idea.wf_context.assignated_di if idea else None

    mailer = mail.get_mailer()

    # creates the substitutions
    substitutions = {
        u'RECIPIENT_LOGIN': to.uid if to else u'',
        u'RECIPIENT_FIRSTNAME': to.firstname if to else u'',
        u'RECIPIENT_LASTNAME': to.lastname if to else u'',
        u'RECIPIENT_EMAIL': to.email or u'' if to else u'',

        u'FI_FIRSTNAME': fi.firstname if fi else u'',
        u'FI_LASTNAME': fi.lastname if fi else u'',
        u'FI_EMAIL': fi.email if fi and fi.email else u'',

        u'DI_FIRSTNAME': di.firstname if di else u'',
        u'DI_LASTNAME': di.lastname if di else u'',
        u'DI_EMAIL': di.email if di and di.email else u'',

        u'IDEA_ID': str(idea.id) if idea else u'',
        u'IDEA_TITLE': text_to_html(idea.title) if idea else u'',
        u'IDEA_LINK_HERE': render_link(_(u'here'), idea_url),

        u'SUBMISSION_DATE': format_date(datetime.today(), format='medium'),
        u'COMMENT': text_to_html(comment or u''),

        u'COMMENT_AUTHOR_FIRSTNAME': comment_author.firstname if comment_author else '',
        u'COMMENT_AUTHOR_LASTNAME': comment_author.lastname if comment_author else '',

        u'EUREKA_LINK': render_link(_(u'Eurêka'), base_url),
        u'EUREKA_URL_LINK': render_link(base_url, base_url),
        u'SHOP_LINK': render_link(_(u'shop'), shop_url),

        u'PREVIOUS_DI_EMAIL': (previous_di.email if (previous_di and previous_di.email) else u''),
        u'PREVIOUS_DI_FIRSTNAME': (previous_di.firstname if (previous_di and previous_di.firstname) else u''),
        u'PREVIOUS_DI_LASTNAME': (previous_di.lastname if (previous_di and previous_di.lastname) else u''),
    }

    substitutions.update(mailer.get_substitutions())

    substitutions.update({k.upper(): v for k, v in kw.iteritems()})

    return substitutions


def _perform_substitutions(template_filename, locale, substitutions):
    # gets the template path
    template_path = os.path.join('data', 'templates', locale, template_filename)
    template = resource_stream(template_path)

    # read unicode content from the template
    content = unicode(template.read(), encoding='utf-8')

    # perform substitutions
    for marker, value in substitutions.items():
        content = content.replace('@%s@' % marker, value)

    return content
