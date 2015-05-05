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

import unittest
from cStringIO import StringIO

from eureka.infrastructure.validators import validate_file, \
    remove_invalid_chars


class TestValidators(unittest.TestCase):
    class FileUpload(object):
        def __init__(self, filename, type, data):
            self.filename = filename
            self.type = type
            self.file = StringIO(data)
            self.done = 0

    def test_remove_invalid_chars(self):
        s = u'\x08\x09\x0B\t\n\x11blé\uf04a'
        self.assertEquals(u'\t\t\nblé', remove_invalid_chars(s))

    def test_validate_file_ok(self):
        self.assertEquals(dict(filename=u'test.txt', content_type=u'text/plain', filedata='1' * 1024),
                          validate_file(self.FileUpload(u'test.txt', u'text/plain', '1' * 1024), 1))

    def test_validate_file_too_big(self):
        self.assertRaises(ValueError,
                          lambda: validate_file(self.FileUpload('test.txt', 'text/plain', '1' * 1025), 1))

    def test_validate_file_with_unix_path_in_filename(self):
        self.assertEquals(dict(filename=u'test.txt', content_type=u'text/plain', filedata='123456'),
                          validate_file(self.FileUpload(u'/path/to/test.txt', u'text/plain', '123456'), 1))

    def test_validate_file_with_windows_path_in_filename(self):
        self.assertEquals(dict(filename=u'test.txt', content_type=u'text/plain', filedata='123456'),
                          validate_file(self.FileUpload(r'c:\Documents and Settings\user\test.txt', u'text/plain', '123456'), 1))
