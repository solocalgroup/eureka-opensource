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

from datetime import timedelta
import hashlib

from nagare import editor
from nagare.i18n import _

from eureka.domain.repositories import UserRepository
from eureka.infrastructure.urls import get_url_service
from eureka.infrastructure.token_generator import TokenGenerator
from eureka.infrastructure.tools import is_string
from eureka.ui.common.yui2 import flashmessage


class ResetPasswordEvent(object):
    """Answer returned when a user wants to reset his password"""


class ResetPassword(editor.Editor):
    def __init__(self):
        super(ResetPassword, self).__init__(None)
        self.login = editor.Property(u'').validate(self._validate_user)

    def commit(self):
        if not super(ResetPassword, self).commit((), ('login',)):
            return False

        uid = self.login.value
        password_reset_url = get_url_service().expand_url(['password_reset', uid], relative=False)
        ResetPasswordConfirmation(uid).send_email(password_reset_url)
        flashmessage.set_flash(_(u"A password reset email has been sent to your contact email address."))

        return True

    def _validate_user(self, login):
        user = UserRepository().get_by_uid(login)
        if user is None:
            raise ValueError(_(u"This user does not exist"))

        if not user.enabled:
            raise ValueError(_(u"This user account is disabled"))

        return login


class ResetPasswordConfirmation(object):
    """Confirm a password reset by sending a confirmation email, then acknowledge the
    success/failure of the operation"""

    def __init__(self, user, expiration_delay=timedelta(days=1)):
        self.uid = user if is_string(user) else user.uid
        self.token_generator = TokenGenerator(self._encryption_key(), expiration_delay)

    def _encryption_key(self):
        secret = 'eOMI5oa6ByATXNIADwloIRgI6EOqqnvb'
        email = self.user.email
        return hashlib.md5(secret + email).hexdigest()

    @property
    def user(self):
        return UserRepository().get_by_uid(self.uid)

    def confirmation_url(self, base_url):
        token = self.token_generator.create_token()
        return '/'.join((base_url, token))

    def confirm_reset_password(self, token):
        return self.token_generator.check_token(token)

    def send_email(self, confirmation_base_url):
        confirmation_url = self.confirmation_url(confirmation_base_url)
        self.user.send_email('mail-password-reset.html', comment=confirmation_url)
