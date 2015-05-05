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

import random
import string

from nagare.i18n import _


class PasswordPolicy(object):
    Cases = (string.ascii_lowercase,
             string.ascii_uppercase,
             string.digits,
             string.punctuation)

    def __init__(self, min_length=4, nb_cases=1, default_password=None,
                 expiration_delay=None):
        """Create a password policy. Passwords should have at least *min_length* characters and at least *nb_cases*
        different character cases. If *default_password* is set, this password is always returned when generating a
        password. Otherwise, a random password is generated"""
        self.min_length = min_length
        self.nb_cases = nb_cases
        self.default_password = default_password
        self.expiration_delay = expiration_delay

        if (self.nb_cases > len(self.Cases)) or (self.min_length < self.nb_cases):
            raise ValueError(_('Inconsistent settings'))

    def generate_password(self):
        """Generate a password that conforms to the policy"""
        if self.default_password:
            return self.default_password

        len = self.min_length
        chars = []
        for (i, case) in enumerate(self.Cases[:self.nb_cases]):
            if i == self.nb_cases - 1:
                n = len
            else:
                n = random.randint(1, len - (self.nb_cases - i - 1))
                len -= n
            chars.extend([random.choice(case) for __ in range(n)])

        random.shuffle(chars)
        return u''.join(chars)

    def validate_password(self, password):
        """Validate that the given password conforms to the policy.
        Return either None for success or an error message"""
        if self.default_password and self.default_password == password:
            return None

        if len(password) < self.min_length:
            return _(u"Password too short: should have at least %d "
                     u"characters") % self.min_length

        nb_cases = 0
        for case in self.Cases:
            if set(case).intersection(set(password)):
                nb_cases += 1

        if nb_cases < self.nb_cases:
            return _(u"Too few character cases in password: should have %d"
                     u" cases from lowercase letters, uppercase letters, "
                     u"digits and punctuation") % self.nb_cases

        return None  # no error
