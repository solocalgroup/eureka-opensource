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

from cStringIO import StringIO
from textwrap import dedent

from elixir import session

from PIL import Image

from eureka.domain.models import OrganizationData, OrganizationType
from eureka.infrastructure.vcard import generate_vcard

from eureka.tests import DatabaseEnabledTestCase
from eureka.tests.domain import create_user


class TestVCard(DatabaseEnabledTestCase):
    def create_photo(self):
        out = StringIO()
        image = Image.new("RGB", (100, 100))
        image.save(out, "PNG")
        return out.getvalue()

    def create_user(self):
        user = create_user(
            uid=u'jcdusse',
            firstname=u'Jean-Claude',
            lastname=u'Dusse',
            email=u'jean-claude.dusse@localhost',
            work_phone=u'0212345678',
            mobile_phone=u'0612345678',
            position=u'Bronzé',
            corporation=OrganizationData(label=u'PagesJaunes', type=OrganizationType(u'Corporation')),
            direction=OrganizationData(label=u'Dir. Communication', type=OrganizationType(u'Direction')),
            service=OrganizationData(label=u'Direction de la Communication', type=OrganizationType(u'Service')),
            site=OrganizationData(label=u'Sèvres', type=OrganizationType(u'Site')),
        )
        user.photo = self.create_photo()
        session.flush()
        return user

    def test_generate_vcard(self):
        vcard = generate_vcard(self.create_user(),
                               u'https://localhost/vcards/jcdusse',
                               u'https://localhost/profile/jcdusse')

        expected_vcard = """
        BEGIN:VCARD
        VERSION:2.1
        UID:https://localhost/vcards/jcdusse
        N:Dusse;Jean-Claude
        FN:Jean-Claude Dusse
        EMAIL:jean-claude.dusse@localhost
        TITLE;ENCODING=8BIT;CHARSET=UTF-8:Bronzé
        ORG:PagesJaunes;Dir. Communication
        TEL;WORK:0212345678
        TEL;CELL:0612345678
        URL:https://localhost/profile/jcdusse
        PHOTO;ENCODING=BASE64;TYPE=image/jpeg:/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBg
         cGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC
         4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMj
         IyMjIyMjIyMjIyMjIyMjL/wAARCABBAEEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAA
         ECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0
         KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3
         R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19
         jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8
         QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRCh
         YkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhY
         aHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6O
         nq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD5/ooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKK
         ACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooA
         KKKKACiiigAooooA//2Q==
        END:VCARD
        """
        expected_vcard = dedent(expected_vcard).strip()
        self.assertEqual(expected_vcard, vcard)
