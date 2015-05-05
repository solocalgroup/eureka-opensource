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

from base64 import b64encode, b64decode
from datetime import datetime
import hashlib

from nagare import security, log
from nagare.security import form_auth

from eureka.domain.repositories import UserRepository
from eureka.infrastructure.password_policy import PasswordPolicy


def get_current_user():
    current_user = security.get_user()
    if current_user:
        return current_user.entity


class User(security.common.User):
    def __init__(self, uid):
        super(User, self).__init__(uid)
        self.uid = uid

    @property
    def entity(self):
        """Get the underlying user entity"""
        return UserRepository().get_by_uid(self.uid)


class Rules(security.common.Rules):
    pass


class DatabaseAuthentication(form_auth.Authentication):
    _autoconnection_secret = "jGgyZ25cEOJwxvmJt3IhgH0wmUFt2Swt"

    def __init__(self, platform=None, cookie_max_age=None, secure_cookie=False, autoconnection_token_timeout=60, password_policy=None):
        self.platform = platform
        super(DatabaseAuthentication, self).__init__(max_age=cookie_max_age, secure=secure_cookie)
        self.autoconnection_token_timeout = autoconnection_token_timeout
        self.password_policy = password_policy or PasswordPolicy()

    @property
    def log(self):
        return log.get_logger('.' + __name__)

    def get_user_by_uid(self, uid):
        return UserRepository().get_by_uid(uid)

    def cookie_encode(self, *ids):
        # fix a nagare bug: the values were truncated due to base64 splitting the value into multiple lines
        # fixed in changeset http://hg.nagare.org/core/rev/f2793e81de0f but not released yet
        return ':'.join(b64encode(value.encode('utf-8')) for value in ids)

    def cookie_decode(self, cookie):
        # fix a nagare bug: the request crashes when the cookie is malformed
        # fixed in changeset http://hg.nagare.org/core/rev/f2793e81de0f but not released yet
        try:
            return [b64decode(s).decode('utf-8') for s in cookie.split(':')]
        except (TypeError, UnicodeDecodeError):
            # in case there's a problem when decoding the authentication cookie, fall back to unauthenticated
            return None, None

    def _get_ids(self, request, response):
        # remember the path to use for the authentication cookie
        self.path = request.script_name + '/'
        return super(DatabaseAuthentication, self)._get_ids(request, response)

    def get_ids(self, request, response):
        # is this an auto-connection requests from PagesJaunes Intranet?
        # warning: the auto-connection URL is not handled in a presentation.init_for rule because we
        #          encounter security cookie problems otherwise
        p = request.path.split('/')[1:]  # we are not interested by the part before the leading slash
        if len(p) == 1 and (p[0] == 'connect_secure'):
            uid = request.params.get('__ac_name')
            timestamp = request.params.get('__ac_date')
            token = request.params.get('__ac_token')
            if uid:
                return self._autoconnect_ids(uid, timestamp, token)

        # fall back to normal authentication
        return super(DatabaseAuthentication, self).get_ids(request, response)

    def get_ids_from_params(self, params):
        # encrypt the password coming from the form authentication, so that we can compare the encrypted passwords
        uid, password = super(DatabaseAuthentication, self).get_ids_from_params(params)
        user = self.get_user_by_uid(uid)
        if not user or not password:
            return None, None
        return uid, user.encrypt_password(password)

    def get_password(self, uid):
        user = self.get_user_by_uid(uid)
        return user.password if user else None

    def logout(self, location=''):
        if security.get_user() is not None:
            super(DatabaseAuthentication, self).logout(location)

    def update_current_user_credentials(self):
        current_user = security.get_user()
        if current_user:  # a user should be connected
            user = current_user.entity
            current_user.set_id(user.uid, user.password)

    def _autoconnection_token(self, uid, timestamp):
        """Compute the autoconnection token for a user"""
        def sha512(s):
            return hashlib.sha512(s).hexdigest()

        return sha512(sha512(self._autoconnection_secret + timestamp) + uid)

    def _is_valid_autoconnection_token(self, uid, timestamp, token):
        try:
            date = datetime.strptime(timestamp, '%Y%m%d%H%M%S')
        except (TypeError, ValueError):
            return False

        delta = datetime.now() - date
        elapsed = delta.seconds + delta.days * 24 * 3600

        if token != self._autoconnection_token(uid, timestamp):
            self.log.error('Invalid autoconnection token for %s' % uid)
            return False

        if (elapsed < 0) or (self.autoconnection_token_timeout is not None and elapsed > self.autoconnection_token_timeout):
            self.log.error('Invalid autoconnection timestamp for %s' % uid)
            return False

        return True

    def _autoconnect_ids(self, uid, timestamp, token):
        """Return the user ids for a user auto-connected from the Intranet"""
        password = self.get_password(uid) if self._is_valid_autoconnection_token(uid, timestamp, token) else None
        return uid, {'password': password}

    def _create_user(self, uid):
        user = self.get_user_by_uid(uid)
        if not user or not user.enabled:
            return None

        # triggers user related business rules on connection
        user.on_connection(platform=self.platform)
        return User(uid)


class SecurityManager(DatabaseAuthentication, Rules):
    def __init__(self, *args, **kwargs):
        DatabaseAuthentication.__init__(self, *args, **kwargs)
        Rules.__init__(self)
