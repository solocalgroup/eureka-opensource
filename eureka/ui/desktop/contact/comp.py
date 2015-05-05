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

from nagare import security, editor
from nagare.i18n import _

from eureka.infrastructure import mail
from eureka.infrastructure import event_management, registry, validators
from eureka.ui.common.yui2 import flashmessage


class Contact(editor.Editor):
    """Contact form"""
    def __init__(self, parent, subject=None, body=None):
        event_management._register_listener(parent, self)
        self.sender_email = editor.Property(u'').validate(validators.email)
        self.subject = editor.Property(subject or u'').validate(validators.non_empty_string)
        self.message = editor.Property(body or u'').validate(validators.non_empty_string)

    @property
    def user(self):
        user = security.get_user()
        if user:
            return user.entity

    def commit(self):
        properties = ('subject', 'message')
        if not self.user:
            properties += ('sender_email',)

        if not self.is_validated(properties):
            return False  # failure

        subject = _(u'Eureka : Contact (%s)') % self.subject()
        message = self.message()

        sender = self.user.email if self.user else self.sender_email.value
        mailer = mail.get_mailer()
        recipient = mailer.support_sender
        mailer.send_mail(subject, sender, [recipient], message)

        confirmation = _(u'Your request has been sent to the IPS team that will answer it as soon as possible')
        flashmessage.set_flash(confirmation)
        event_management._emit_signal(self, "VIEW_FRONTDESK")
        return True  # success
