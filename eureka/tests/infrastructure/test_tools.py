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

from eureka.infrastructure.tools import Enum, text_to_html, fix_filename


class TestTools(unittest.TestCase):
    def test_text_to_html(self):
        # iso-transform when there's nothing special
        self.assertEquals('Text',
                          text_to_html('Text'))
        # we escape special html chars and do not let html tags pass
        self.assertEquals('David &amp; Goliath',
                          text_to_html('David & Goliath'))
        self.assertEquals('&lt;script&gt;I am a hacker&lt;/script&gt;',
                          text_to_html('<script>I am a hacker</script>'))
        # we deal with end of line characters
        self.assertEquals('First line<br/>Second line',
                          text_to_html('First line\nSecond line'))
        # we detect urls and transform them to <a> tags
        self.assertEquals('A http link <a href="http://www.google.fr">http://www.google.fr</a> with trailing text',
                          text_to_html('A http link http://www.google.fr with trailing text'))
        self.assertEquals('A https link <a href="https://www.google.fr">https://www.google.fr</a> with trailing text',
                          text_to_html('A https link https://www.google.fr with trailing text'))
        self.assertEquals(u'Le site &quot;<a href="http://www.google.fr">http://www.google.fr</a>&quot; est très bien',
                          text_to_html(u'Le site "http://www.google.fr" est très bien'))
        self.assertEquals('<a href="http://www.google.fr/site-production?param=valeur&amp;truc=muche">http://www.google.fr/site-production?param=valeur&amp;truc=muche</a>',
                          text_to_html('http://www.google.fr/site-production?param=valeur&truc=muche'))
        self.assertEquals('Url with port <a href="http://localhost:8080">http://localhost:8080</a> and with trailing text',
                          text_to_html('Url with port http://localhost:8080 and with trailing text'))
        self.assertEquals('Url with port <a href="http://localhost:8080/blabla,toto">http://localhost:8080/blabla,toto</a> and with trailing text',
                          text_to_html('Url with port http://localhost:8080/blabla,toto and with trailing text'))
        self.assertEquals('Url with port <a href="http://localhost:8080/blabla">http://localhost:8080/blabla</a>, and with trailing text',
                          text_to_html('Url with port http://localhost:8080/blabla, and with trailing text'))

    def test_fix_filename(self):
        self.assertEquals('meme.jpg', fix_filename(u'mémé.jpg'))
        self.assertEquals('meme bebe.jpg', fix_filename(u'mémé bébé@.jpg'))

    def test_enum_contains(self):
        class TestEnum(Enum):
            One = 'one'
            Two = 'two'

        self.assert_(TestEnum.One in TestEnum)
        self.assert_(TestEnum.Two in TestEnum)
        self.assert_('blabla' not in TestEnum)

    def test_enum_iter(self):
        class TestEnum(Enum):
            One = 'one'
            Two = 'two'

        self.assertEquals(['one', 'two'], [item for item in TestEnum])
