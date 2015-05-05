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

import re
import time

from nagare import log

from eureka.infrastructure import crypto
from datetime import datetime


class TokenGenerator(object):
    """Generate or check time-stamped tokens"""
    signature = "vy1ZLamRVfu3EF5r683iySz61suBRjZ0"

    def __init__(self, encryption_key, expiration_delay):
        """Create a token generator"""
        self.encryption_key = encryption_key
        self.expiration_delay = expiration_delay

    @property
    def log(self):
        return log.get_logger('.' + __name__)

    def create_token(self):
        """Create a time-stamped token"""
        timestamp = int(time.time())
        message = '%s:%s' % (timestamp, self.signature)
        return crypto.encrypt(message, self.encryption_key)

    def check_token(self, token):
        """Check that the token is valid"""
        message = crypto.decrypt(token, self.encryption_key)
        match = re.match(r"^(\d+):%s$" % self.signature, message)
        if match:
            timestamp = int(match.group(1))
            token_date = datetime.fromtimestamp(timestamp)
            deadline = token_date + self.expiration_delay
            now = datetime.now()
            self.log.debug('Token date: %s' % token_date)
            if (now > token_date) and (now < deadline):
                return True

        return False
