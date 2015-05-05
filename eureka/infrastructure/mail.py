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

import threading
import smtplib
from email.encoders import encode_base64
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.utils import COMMASPACE, formatdate

from nagare import log

from eureka.infrastructure.tools import is_string


class Mailer(object):
    spec = {
        'smtp_host': 'string(default="")',
        'smtp_port': 'integer(default=25)',
        'smtp_user': 'string(default=None)',
        'smtp_pass': 'string(default=None)',
        'timeout': 'float(default=0.0)',
        'reply_to': 'string(default=None)',
        'activated': 'boolean(default=False)',
        'hidden_recipients': 'string_list(default=list())',
        'security_sender': 'string',
        'info_sender': 'string',
        'support_sender': 'string',
        'ideasubmit_sender': 'string',
        'suggest_recipients': 'string_list(min=1)',
        'dsig_recipients': 'string_list(min=1)',
        'moderation_recipients': 'string_list(min=1)',
    }

    def __init__(self, smtp_host='', smtp_port=25, smtp_user=None,
                 smtp_pass=None, timeout=0.0, reply_to=None, activated=False,
                 hidden_recipients=None, security_sender='', info_sender='',
                 support_sender='', ideasubmit_sender='',
                 suggest_recipients=None, dsig_recipients=None,
                 moderation_recipients=None):

        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_pass = smtp_pass
        self.timeout = timeout
        self.reply_to = reply_to
        self.hidden_recipients = hidden_recipients or []
        self.activated = activated
        self.security_sender = security_sender
        self.info_sender = info_sender
        self.support_sender = support_sender
        self.ideasubmit_sender = ideasubmit_sender
        self.suggest_recipients = suggest_recipients or []
        self.dsig_recipients = dsig_recipients or []
        self.moderation_recipients = moderation_recipients or []

    def create_message(self, subject, from_, to, content, cc=None, bcc=None,
                       type='plain', mpart_type='mixed', attachments=()):
        """Sends an e-mail using the mail section configuration of
           the application.

        Parameters:
        * `subject` -- the subject of the mail,
        * `from_` -- the sender,
        * `to` -- the receiver or list of receivers,
        * `content` -- the content of the mail,
        * `cc` -- the eventual CC or list of CC,
        * `bcc` -- the eventual BCC or list of BCC,
        * `type` -- the eventual type of the email, either `'plain'`
                    or `'html'`.
        * `mpart_type` -- the eventual custom ``MIMEMultipart`` type
                          ('mixed' or 'related') (defaults to mixed)
        * `attachments` -- the eventual list of attachments to add
        """

        # converts recipients to list and provide an empty list for None
        to = [to] if is_string(to) else to
        cc = [cc] if is_string(cc) else (cc or [])
        bcc = [bcc] if is_string(bcc) else (bcc or [])

        # always adds the hidden recipients
        if self.hidden_recipients:
            bcc += self.hidden_recipients

        # creates the message envelop
        msg = MIMEMultipart(mpart_type)
        msg['Subject'] = subject
        msg['Date'] = formatdate(localtime=True)

        if self.reply_to:
            msg['From'] = self.reply_to
            msg['Reply-to'] = from_
        else:
            msg['From'] = from_

        msg['To'] = COMMASPACE.join(to)

        if cc:
            msg['Cc'] = COMMASPACE.join(cc)

        # attaches the mail content
        if isinstance(content, unicode):
            content = content.encode('UTF-8')
        msg.attach(MIMEText(content, type, _charset='UTF-8'))

        # eventually completes the message with attachments
        for attachment in attachments:
            self.add_file_attachment(msg, *attachment)

        # log the email
        logger = log.get_logger('.' + __name__)
        logger.debug('Sending mail: from=%r, to=%r, cc=%r, bcc=%r, subject=%r',
                     from_, to, cc, bcc, subject)
        logger.debug('Mail content:\n' + content)

        return msg

    def send_mail(self, subject, from_, to, content, cc=None, bcc=None,
                  type='plain', mpart_type='mixed', attachments=()):

        cc = cc or []
        bcc = bcc or []

        msg = self.create_message(subject, from_, to, content, cc, bcc,
                                  type, mpart_type, attachments)
        # send the email
        if self.activated:
            self._smtp_send(from_, to + cc + bcc, msg)

    def add_file_attachment(self, message, content_type, filename, data):
        maintype, subtype = content_type.split('/')
        attachment = MIMEBase(maintype, subtype)
        attachment.add_header('Content-Disposition', 'attachment',
                              filename=filename)
        attachment.set_payload(data)
        encode_base64(attachment)
        message.attach(attachment)

    def _smtp_send(self, from_, to, msg):

        smtp_server = smtplib.SMTP(
            self.smtp_host,
            self.smtp_port,
            **({'timeout': self.timeout} if self.timeout else {})
        )
        if self.smtp_user and self.smtp_pass is not None:
            smtp_server.login(self.smtp_user, self.smtp_pass)

        smtp_server.sendmail(from_, to, msg.as_string())
        smtp_server.quit()

    def get_substitutions(self):
        return {
            u'DSIG_EMAIL': u','.join(self.dsig_recipients),
            u'IPS_SECURITY_EMAIL': self.security_sender,
            u'IPS_INFO_EMAIL': self.info_sender,
            u'IPS_MODERATION_EMAIL': u','.join(self.moderation_recipients),
            u'IPS_SUGGESTION_EMAIL': u','.join(self.suggest_recipients)
        }


# -----------------------------------------------------------------------------


__mailer = None


def set_mailer(mailer):
    global __mailer
    __mailer = mailer


def get_mailer():
    return __mailer
