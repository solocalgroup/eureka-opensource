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

import binascii

from Crypto.Cipher import Blowfish


class Crypto(object):
    def __init__(self, key, padding_char='='):
        self._cipher = Blowfish.new(key, Blowfish.MODE_ECB)
        self.padding_char = padding_char

    def _pad(self, text):
        if text.endswith(self.padding_char):
            raise ValueError("text should not finish with %s characters" % self.padding_char)
        return text + (8 - len(text) % 8) * self.padding_char

    def _unpad(self, text):
        return text.rstrip(self.padding_char)

    def encrypt(self, clear_text):
        """Encrypt a string"""
        encrypted = self._cipher.encrypt(self._pad(clear_text))
        return binascii.b2a_hex(encrypted)

    def decrypt(self, encrypted_text):
        """Decrypt a string"""
        try:
            encrypted = binascii.a2b_hex(encrypted_text)
            return self._unpad(self._cipher.decrypt(encrypted))
        except (TypeError, ValueError):
            return ""


def encrypt(text, key):
    return Crypto(key).encrypt(text)


def decrypt(text, key):
    return Crypto(key).decrypt(text)
