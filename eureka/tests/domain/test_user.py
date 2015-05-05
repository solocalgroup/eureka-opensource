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

import pickle
from cStringIO import StringIO

from eureka.domain.models import RoleType, UnpicklableError
from eureka.domain.repositories import UserRepository
from eureka.tests import DatabaseEnabledTestCase
from eureka.tests.domain import create_user
from nagare.database import session
from PIL import Image


class TestUsers(DatabaseEnabledTestCase):
    def setUp(self):
        super(TestUsers, self).setUp()
        self.user_repository = UserRepository()

    def test_unpicklable(self):
        user = create_user(uid=u'jdoe', firstname=u'John', lastname=u'Doe')
        self.assertRaises(UnpicklableError, lambda: pickle.dumps(user))

    def test_creation(self):
        uid = u'jdoe'
        firstname = u'John'
        lastname = u'Doe'
        create_user(uid=uid, firstname=firstname, lastname=lastname)
        session.flush()
        user = self.user_repository.get_by_uid(uid)
        self.assertEquals(user.uid, uid)
        self.assertEquals(user.firstname, firstname)
        self.assertEquals(user.lastname, lastname)
        self.assert_(user.enabled)

    def test_creation_not_enabled(self):
        uid = u'login'
        create_user(uid=uid, enabled=False)
        session.flush()
        user = self.user_repository.get_by_uid(uid)
        self.assert_(not user.enabled)

    def test_set_firstname_and_lastname(self):
        uid = u'jdoe'
        user = create_user(uid=uid)
        firstname = u'John'
        lastname = u'Doe'
        user.firstname = firstname
        user.lastname = lastname
        session.flush()
        user = self.user_repository.get_by_uid(uid)
        self.assertEquals(user.firstname, firstname)
        self.assertEquals(user.lastname, lastname)

    def test_enabled(self):
        uid = u'jdoe'
        create_user(uid=uid)
        session.flush()
        user = self.user_repository.get_by_uid(uid)
        self.assert_(user.enabled)  # this is what we want most of the time
        user.enabled = False
        session.flush()
        user = self.user_repository.get_by_uid(uid)
        self.assert_(not user.enabled)

    def test_by_uid(self):
        user = create_user(
            uid=u'jdoe',
            firstname=u'John',
            lastname=u'Doe',
        )
        self.assert_(
            self.user_repository.get_by_uid(user.uid) is not None)
        self.assert_(
            self.user_repository.get_by_uid(user.uid + u'XXX') is None)

    def test_by_email(self):
        email = u'jdoe@email.com'
        create_user(
            uid=u'jdoe',
            firstname=u'John',
            lastname=u'Doe',
            email=email,
        )
        user = self.user_repository.get_by_email(email)
        self.assert_(user is not None)
        self.assertEquals(email, user.email)
        self.assert_(
            self.user_repository.get_by_email(user.email + u'XXX') is None)

    def test_store_password(self):
        user = create_user(
            uid=u'jdoe',
            firstname=u'John',
            lastname=u'Doe',
            password=u'password',
        )
        self.assertEqual(user.password, user.encrypt_password(u'password'))
        self.assert_(not user.should_change_password())

    def test_validate_password(self):
        user = create_user(
            uid=u'jdoe',
            firstname=u'John',
            lastname=u'Doe',
            password=u'password',
        )
        self.assert_(user.validate_password('newpass') is None)
        self.assert_(isinstance(user.validate_password('a'), basestring))

    def test_change_password_success(self):
        user = create_user(
            uid=u'jdoe',
            firstname=u'John',
            lastname=u'Doe',
            password=u'password'
        )
        new_password = u'newpass'
        user.change_password(new_password)
        session.flush()
        self.assertEqual(user.password, user.encrypt_password(new_password))

    def test_change_password_failure(self):
        user = create_user(
            uid=u'jdoe',
            firstname=u'John',
            lastname=u'Doe',
            password=u'password',
        )
        new_password = u'a'
        with self.assertRaises(ValueError):
            user.change_password(new_password)

    def test_reset_password(self):
        user = create_user(
            uid=u'jdoe',
            firstname=u'John',
            lastname=u'Doe',
            password=u'password',
        )
        new_password = user.reset_password()
        self.assertEqual(user.password, user.encrypt_password(new_password))
        self.assert_(user.should_change_password())

    def test_set_fi(self):
        user = create_user()
        fi = create_user()
        user.fi = fi
        self.assertEquals(fi, user.fi)

    def test_add_role(self):
        user = create_user()
        user.add_role(RoleType.Facilitator)
        self.assert_(user.has_role(RoleType.Facilitator))

    def test_remove_missing_role(self):
        user = create_user()
        user.add_role(RoleType.Facilitator)
        user.remove_role(RoleType.Developer)
        self.assert_(user.has_role(RoleType.Facilitator))
        self.assert_(not user.has_role(RoleType.Developer))

    def test_deleting_a_user_also_remove_her_roles(self):
        user = create_user()
        user.add_role(RoleType.Facilitator)
        session.flush()
        user_uid = user.uid
        user.delete()
        session.flush()
        facilitators_uids = [
            u.uid for u in self.user_repository.get_facilitators()
        ]
        self.assertFalse(user_uid in facilitators_uids)

    def test_remove_existing_role(self):
        user = create_user()
        user.add_role(RoleType.Facilitator)
        session.flush()
        user.remove_role(RoleType.Facilitator)
        self.assert_(not user.has_role(RoleType.Facilitator))
        session.flush()
        facilitators = self.user_repository.get_facilitators()
        self.assert_(user not in facilitators)

    def test_get_by_role(self):
        user = create_user()
        create_user()
        user.add_role(RoleType.Facilitator)
        session.flush()
        facilitators = self.user_repository.get_facilitators()
        self.assertTrue(user in facilitators)

    def create_photo(self, size=100):
        out = StringIO()
        image = Image.new("RGB", (size, size))
        image.save(out, "PNG")
        return out.getvalue()

    def test_photo(self):
        user = create_user()
        photo = self.create_photo(50)
        user.photo = photo
        session.flush()
        self.assertTrue(user.photo is not None)
        user.photo = None
        self.assertTrue(user.photo is None)
