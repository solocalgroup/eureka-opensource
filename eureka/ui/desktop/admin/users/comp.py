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

# -*- coding: UTF-8 -*-
# =-
# --
# Copyright (c) 2014 PagesJaunes.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --
# =-

from sqlalchemy import func, or_

from nagare import component, editor, security, log
from nagare.database import session
from nagare.i18n import _

from eureka.domain import mail_notification
from eureka.infrastructure.urls import get_url_service
from eureka.domain.models import UserData, RoleData, DomainData, RoleType
from eureka.domain.models import OrganizationData
from eureka.domain.repositories import (UserRepository, DomainRepository,
                                        IdeaRepository)
from eureka.infrastructure import event_management, validators, registry
from eureka.ui.common.yui2 import flashmessage
from eureka.ui.common.confirmation import Confirmation
from eureka.ui.common.box import PortalBox


# FIXME: move/merge these components with the ones in the user package

class UserEditor(editor.Editor):

    def __init__(self, uid=None, email_unique=True, mobile_access=False):
        """User's informations editor
        In:
            - ``uid`` -- the uid of the user to edit (if we are in edit mode)
            - ``email_unique`` -- do we have to check for the email uniqueness or not (default yes)
        """
        super(UserEditor, self).__init__(None)
        self.assignable_roles = [RoleType.Facilitator, RoleType.Developer]
        if mobile_access:
            self.assignable_roles.append(RoleType.MobileAccess)
        self.email_unique = email_unique
        self.uid = uid
        self.user_repository = UserRepository()
        self.reset_fields()

    @property
    def user(self):
        return self.user_repository.get_by_uid(self.uid)

    @property
    def profile_imported(self):
        return getattr(self.user, 'imported', False)

    @property
    def profile_url(self):
        return get_url_service().expand_url(['profile', self.uid])

    def view_profile(self):
        event_management._emit_signal(self, "VIEW_USER_PROFILE",
                                      user_uid=self.uid)

    @property
    def creation_mode(self):
        return self.uid is None

    def pre_action(self):
        self.clear_roles()

    def validate_login(self, value):
        if self.creation_mode or value != self.user.uid:
            value = validators.unused_uid(value, True)
        return value

    def validate_email(self, value):
        if not self.email_unique:  # We just check that a non empty email address has been supplied
            value = validators.non_empty_string(value)
        elif self.creation_mode or value != self.user.email:
            value = validators.unused_email(value, True)
        return value

    def reset_fields(self):
        user = self.user

        uid = user.uid if user else u''
        email = user.email if user else u''
        firstname = user.firstname if user else u''
        lastname = user.lastname if user else u''
        fi_uid = user.fi_uid if user else u''
        roles = [role for role in self.assignable_roles if
                 user.has_role(role)] if user else []
        work_phone = (user.work_phone or u'') if user else u''
        mobile_phone = (user.mobile_phone or u'') if user else u''
        position = user.position if user else u''
        corporation_id = (user.corporation_id or u'-1') if user else u'-1'
        direction_id = (user.direction_id or u'-1') if user else u'-1'
        service_id = (user.service_id or u'-1') if user else u'-1'
        site_id = (user.site_id or u'-1') if user else u'-1'
        subsite_id = (user.subsite_id or u'-1') if user else u'-1'
        enabled = user.enabled if user else True
        incorporated = user.incorporated if user else False

        self.login = editor.Property(uid).validate(self.validate_login)
        self.email = editor.Property(email).validate(self.validate_email)
        self.firstname = editor.Property(firstname).validate(
            validators.non_empty_string)
        self.lastname = editor.Property(lastname).validate(
            validators.non_empty_string)
        self.fi_uid = editor.Property(fi_uid).validate(
            validators.non_empty_string)
        self.roles = editor.Property(roles)
        self.work_phone = editor.Property(work_phone)
        self.mobile_phone = editor.Property(mobile_phone)
        self.position = editor.Property(position)
        self.corporation_id = editor.Property(corporation_id)
        self.direction_id = editor.Property(direction_id)
        self.service_id = editor.Property(service_id)
        self.site_id = editor.Property(site_id)
        self.subsite_id = editor.Property(subsite_id)
        self.enabled = editor.Property(enabled)
        self.incorporated = editor.Property(incorporated)

    def clear_roles(self):
        self.roles([])

    def add_role(self, role):
        self.roles().append(role)

    def change_corp(self):
        self.direction_id('-1')
        self.service_id('-1')
        self.site_id('-1')
        self.subsite_id('-1')

    def change_dir(self):
        self.service_id('-1')
        self.site_id('-1')
        self.subsite_id('-1')

    def change_service(self):
        self.site_id('-1')
        self.subsite_id('-1')

    def change_site(self):
        self.subsite_id('-1')

    def get_corporations(self):
        return OrganizationData.get_corporations()

    def get_directions(self):
        return OrganizationData.get_directions(parent_id=self.corporation_id())

    def get_services(self):
        return OrganizationData.get_services(parent_id=self.direction_id())

    def get_sites(self):
        return OrganizationData.get_sites(parent_id=self.service_id())

    def get_subsites(self):
        return OrganizationData.get_subsites(parent_id=self.site_id())

    def get_facilitators(self):
        return UserData.get_facilitators()

    def commit(self):
        if not super(UserEditor, self).commit(
                (),
                ('login', 'email', 'roles', 'fi_uid', 'work_phone',
                 'mobile_phone', 'firstname', 'lastname', 'position',
                 'corporation_id', 'direction_id', 'site_id', 'service_id')):
            return False

        # FIXME: use the OrganizationRepository
        get_organization = lambda id: OrganizationData.get(
            id) if id != -1 else None

        corporation = get_organization(self.corporation_id.value)
        direction = get_organization(self.direction_id.value)
        service = get_organization(self.service_id.value)
        site = get_organization(self.site_id.value)
        subsite = get_organization(self.subsite_id.value)
        facilitator = self.user_repository.get_by_uid(self.fi_uid.value)

        # create or update the user
        updates = dict(
            email=self.email.value,
            firstname=self.firstname.value,
            lastname=self.lastname.value,
            enabled=self.enabled.value,
            position=self.position.value,
            corporation=corporation,
            direction=direction,
            service=service,
            site=site,
            incorporated=self.incorporated.value,
            work_phone=self.work_phone.value,
            mobile_phone=self.mobile_phone.value,
            fi=facilitator,
            subsite=subsite,
        )

        if self.user:
            u = self.user
            u.set(**updates)
        else:
            u = self.user_repository.create(uid=self.login.value, **updates)
            password = u.reset_password()
            u.send_welcome_email(password)

        # roles
        for role in self.assignable_roles:
            if role in self.roles():
                u.add_role(role)
            else:
                u.remove_role(role)

        return True


# FIXME: merge with UserEditor
class UserLineEditor(editor.Editor):
    def __init__(self, uid, email_unique=True, mobile_access=False):
        super(UserLineEditor, self).__init__(None)

        self.email_unique = email_unique
        self.mobile_access = mobile_access
        self.uid = uid
        self.user_repository = UserRepository()
        self.reset()

    def reset(self):
        user = self.user_repository.get_by_uid(self.uid)
        self.orig_corp_id = user.corporation_id or -1L
        self.orig_dir_id = user.direction_id or -1L
        self.orig_service_id = user.service_id or -1L
        self.orig_site_id = user.site_id or -1L
        self.orig_subsite_id = user.subsite_id or -1L
        self.orig_enabled = user.enabled
        self.orig_fi_uid = (user.fi_uid or u'')
        self.corporation_id = editor.Property(self.orig_corp_id)
        self.direction_id = editor.Property(self.orig_dir_id)
        self.service_id = editor.Property(self.orig_service_id)
        self.site_id = editor.Property(self.orig_site_id)
        self.subsite_id = editor.Property(self.orig_subsite_id)
        self.enabled = editor.Property(user.enabled)
        self.fi_uid = editor.Property(user.fi_uid or u'').validate(
            validators.non_empty_string)
        self.firstname = user.firstname
        self.lastname = user.lastname

    @property
    def profile_imported(self):
        return getattr(self.user_repository.get_by_uid(self.uid), 'imported', False) if self.uid else False

    @property
    def fullname(self):
        return u' '.join((self.firstname, self.lastname))

    def need_update(self):
        new_corporation_id = long(self.corporation_id()) if self.corporation_id() else None
        if self.orig_corp_id != new_corporation_id:
            return True
        new_direction_id = long(self.direction_id()) if self.direction_id() else None
        if new_direction_id != self.orig_dir_id:
            return True
        new_service_id = long(self.service_id()) if self.service_id() else None
        if new_service_id != self.orig_service_id:
            return True
        new_site_id = long(self.site_id()) if self.site_id() else None
        if new_site_id != self.orig_site_id:
            return True
        new_subsite_id = long(self.subsite_id()) if self.subsite_id() else None
        if new_subsite_id != self.orig_subsite_id:
            return True
        return self.orig_enabled != bool(self.enabled()) or self.orig_fi_uid != unicode(self.fi_uid())

    def change_corp(self):
        self.direction_id('-1')
        self.service_id('-1')
        self.site_id('-1')
        self.subsite_id('-1')

    def change_dir(self):
        self.service_id('-1')
        self.site_id('-1')
        self.subsite_id('-1')

    def change_service(self):
        self.site_id('-1')
        self.subsite_id('-1')

    def change_site(self):
        self.subsite_id('-1')

    def update_user(self):
        # checks the other fields and updates data
        if super(UserLineEditor, self).commit((), ('corporation_id', 'direction_id', 'site_id', 'service_id', 'fi_uid', 'enabled')):

            # FIXME: use the OrganizationRepository
            get_orga = lambda id: OrganizationData.get(
                id) if id != -1 else None

            u = self.user_repository.get_by_uid(self.uid)
            u.corporation = get_orga(self.corporation_id())
            u.direction = get_orga(self.direction_id())
            u.service = get_orga(self.service_id())
            u.site = get_orga(self.site_id())
            u.subsite = get_orga(self.subsite_id())
            u.enabled = self.enabled()
            u.fi_uid = self.fi_uid()

            session.flush()

            self.orig_corp_id = u.corporation_id or -1L
            self.orig_dir_id = u.direction_id or -1L
            self.orig_service_id = u.service_id or -1L
            self.orig_site_id = u.site_id or -1L
            self.orig_subsite_id = u.subsite_id or -1L
            self.orig_enabled = u.enabled
            self.orig_fi_uid = u.fi_uid

            flashmessage.set_flash(_(u'User modified'))

            return True

    def get_fi_name(self):
        ci = self.user_repository.get_by_uid(self.fi_uid.value)
        if ci:
            return ci.fullname
        return u""

    # Refactor

    def get_corporations(self):
        return OrganizationData.get_corporations()

    def get_directions(self):
        return OrganizationData.get_directions(parent_id=self.corporation_id())

    def get_services(self):
        return OrganizationData.get_services(parent_id=self.direction_id())

    def get_sites(self):
        return OrganizationData.get_sites(parent_id=self.service_id())

    def get_subsites(self):
        return OrganizationData.get_subsites(parent_id=self.site_id())

    def edit_user(self, comp):
        message = comp.call(UserEditor(self.uid, email_unique=self.email_unique, mobile_access=self.mobile_access))
        self.reset()
        if message:
            flashmessage.set_flash(message)

    def get_facilitators(self):
        return UserData.get_facilitators()

    def delete(self):
        UserRepository().delete(self.uid)


class UserFilter(editor.Editor):
    def __init__(self):
        editor.Editor.__init__(self, None)
        self.user_repository = UserRepository()

        self.uid = editor.Property(u'')
        self.corporation_id = editor.Property(-1).validate(validators.integer)
        self.direction_id = editor.Property(-1).validate(validators.integer)
        self.service_id = editor.Property(-1).validate(validators.integer)
        self.site_id = editor.Property(-1).validate(validators.integer)
        self.subsite_id = editor.Property(-1).validate(validators.integer)
        self.enabled = editor.Property('-1')
        self.fi_uid = editor.Property('-1')

    def __repr__(self):
        args = ['%s=%s' % (attr, getattr(self, attr)())
                for attr in ('uid', 'corporation_id', 'direction_id', 'service_id', 'site_id', 'subsite_id', 'enabled', 'fi_uid')]
        return '<UserFilter(%s)>' % ', '.join(args)

    def initialize_from_user_organization(self, user):
        self.corporation_id(user.corporation_id or -1)
        self.direction_id(user.direction_id or -1)
        self.service_id(user.service_id or -1)
        self.site_id(user.site_id or -1)
        self.subsite_id(user.subsite_id or -1)
        self._restore_organization_consistency()

    def _restore_organization_consistency(self):
        """Call this after you change one of the organization properties in to restore the consistency (because
        properties are inter-dependent)"""
        reset_others = False  # reset the following properties
        for name, get_values in (('corporation_id', self.get_corporations),
                                 ('direction_id', self.get_directions),
                                 ('service_id', self.get_services),
                                 ('site_id', self.get_sites),
                                 ('subsite_id', self.get_subsites)):
            prop = getattr(self, name)
            value = prop.value
            values = [item[1] for item in get_values()]
            if reset_others or value not in values or value == -1:
                prop('-1')
                reset_others = True

    post_action = _restore_organization_consistency

    # Refactor
    def get_corporations(self):
        return ([(_(u'All corporations'), -1)] +
                OrganizationData.get_corporations())

    def get_directions(self):
        return ([(_(u'All directions'), -1)] +
                OrganizationData.get_directions(parent_id=self.corporation_id()))

    def get_services(self):
        return ([(_(u'All services'), -1)] +
                OrganizationData.get_services(parent_id=self.direction_id()))

    def get_sites(self):
        return ([(_(u'All sites'), -1)] +
                OrganizationData.get_sites(parent_id=self.service_id()))

    def get_subsites(self):
        return ([(_(u'All subsites'), -1)] +
                OrganizationData.get_subsites(parent_id=self.site_id()))

    def get_facilitators(self):
        return UserData.get_facilitators()

    def apply(self, query):
        if self.corporation_id.value != -1:
            query = query.filter(UserData.corporation_id == self.corporation_id.value)

        if self.direction_id.value != -1:
            query = query.filter(UserData.direction_id == self.direction_id.value)

        if self.service_id.value != -1:
            query = query.filter(UserData.service_id == self.service_id.value)

        if self.site_id.value != -1:
            query = query.filter(UserData.site_id == self.site_id.value)

        if self.subsite_id.value != -1:
            query = query.filter(UserData.subsite_id == self.subsite_id.value)

        if self.enabled() != '-1':
            query = query.filter(
                UserData.enabled == (self.enabled() == _(u'Enabled')))

        if self.fi_uid() != '-1':
            if self.fi_uid() == '':
                query = query.filter(UserData.fi_uid == None)
            else:
                query = query.filter(UserData.fi_uid == self.fi_uid())

        if self.uid():
            search_pattern = u"%%%s%%" % self.uid().lower()
            query = query.filter(or_(
                func.lower(UserData.lastname).like(search_pattern),
                func.lower(UserData.firstname).like(search_pattern),
                func.lower(UserData.uid).like(search_pattern)))

        return query


class UserAdmin(object):

    def __init__(self, email_unique=True, can_delete_users=False, mobile_access=False):
        self.email_unique = email_unique
        self.mobile_access = mobile_access
        self.user_repository = UserRepository()

        self.create_user = component.Component(UserEditor(email_unique=self.email_unique, mobile_access=self.mobile_access))
        self.create_user.on_answer(lambda v: self.create_user().reset_fields())
        event_management._register_listener(self, self.create_user())

        self.start = 0
        self.batch_size = 10
        self.radius = 3

        self.filter = component.Component(UserFilter())
        self.with_delete = can_delete_users

    def increase(self):
        self.start += self.batch_size

    def decrease(self):
        self.start -= self.batch_size

    def goto_page(self, page_num):
        self.start = (page_num - 1) * self.batch_size

    def get_users_query(self, apply_filters=True):
        query = session.query(UserData.uid).order_by(UserData.lastname,
                                                     UserData.firstname)
        if apply_filters:
            query = self.filter().apply(query)
        return query

    def get_users(self):
        query = self.get_users_query()
        query = query.offset(self.start).limit(self.batch_size + 1)
        return query

    def get_users_comp(self, roles=None):
        # FIXME: use an appropriate method of the UserRepository
        query = self.get_users_query()
        if roles:
            query = query.outerjoin(UserData.roles).filter(
                RoleData.type.in_(roles)).distinct()
        query = query.offset(self.start).limit(self.batch_size + 1)
        return [component.Component(UserLineEditor(q.uid, email_unique=self.email_unique, mobile_access=self.mobile_access)) for q in query]

    def get_nb_users(self):
        query = self.get_users_query()
        return query.count()

    def delete(self, uid):
        if self.with_delete:
            log.info('User %r deleted by %r', uid, security.get_user().uid)
            UserRepository().delete(uid)


# --------- facilitator administration ---------

class FIAdmin(object):
    def __init__(self):
        self.user_repository = UserRepository()

    def _users(self):
        return self.user_repository.get_facilitators().order_by(
            UserData.lastname, UserData.firstname)

    def confirm_delete_fi(self, uid, comp):
        full_name = self.user_repository.get_by_uid(uid).fullname

        confirm = PortalBox(Confirmation(
            _(u'The facilitator role of user "%s" will be removed. '
              u'You must confirm this change.') % full_name,
            _(u'Ok'), _(u'Cancel')))

        if comp.call(confirm):
            user = self.user_repository.get_by_uid(uid)
            user.remove_role(RoleType.Facilitator)
            user.remove_responsibilities(RoleType.Facilitator)


class FIEditor(editor.Editor):
    def __init__(self, uid):
        super(FIEditor, self).__init__(None)
        self.uid = uid
        self.user_repository = UserRepository()

        # FI
        self.fi_uid = editor.Property(u'').validate(
            validators.non_empty_string)

        self.corporation_id = editor.Property(' - 1')
        self.direction_id = editor.Property(' - 1')
        self.service_id = editor.Property(' - 1')
        self.site_id = editor.Property(' - 1')
        self.subsite_id = editor.Property(' - 1')

        self.successor = editor.Property('').validate(
            validators.non_empty_string)

        self.filter = component.Component(UserFilter())
        if self.user:
            self.filter().initialize_from_user_organization(self.user)

    @property
    def user(self):
        return self.user_repository.get_by_uid(self.uid)

    def get_fi_users(self):
        query = self.user_repository.get_facilitators()
        return self.filter().apply(query)

    # Refactor

    def change_corp(self):
        self.direction_id('-1')
        self.service_id('-1')
        self.site_id('-1')
        self.subsite_id('-1')

    def change_dir(self):
        self.service_id('-1')
        self.site_id('-1')
        self.subsite_id('-1')

    def change_service(self):
        self.site_id('-1')
        self.subsite_id('-1')

    def change_site(self):
        self.subsite_id('-1')

    def get_corporations(self):
        return OrganizationData.get_corporations()

    def get_directions(self):
        return OrganizationData.get_directions(parent_id=self.corporation_id())

    def get_services(self):
        return OrganizationData.get_services(parent_id=self.direction_id())

    def get_sites(self):
        return OrganizationData.get_sites(parent_id=self.service_id())

    def get_subsites(self):
        return OrganizationData.get_subsites(parent_id=self.site_id())

    def clear_successor(self):
        self.successor('')

    def replace_facilitator(self):
        if not super(FIEditor, self).commit((), ('successor',)):
            return False

        # transfer the FI responsibilities to the new user
        new_facilitator = self.user_repository.get_by_uid(self.successor())
        self.user.transfer_responsibilities(RoleType.Facilitator,
                                            new_facilitator)

        flashmessage.set_flash(_(u'Facilitator replaced'))

        return True

    def _get_organization_label(self, org_id):
        if org_id == -1:
            return None
            # FIXME: use the OrganizationRepository instead
        return OrganizationData.get(org_id).label

    def add_entity(self):
        if not super(FIEditor, self).commit(
                (),
                ('corporation_id', 'direction_id', 'service_id', 'site_id')):
            return False

        corporation = self._get_organization_label(long(self.corporation_id()))
        direction = self._get_organization_label(long(self.direction_id()))
        service = self._get_organization_label(long(self.service_id()))
        site = self._get_organization_label(long(self.site_id()))
        subsite = self._get_organization_label(long(self.subsite_id()))

        users = self.user_repository.get_by_organization(corporation,
                                                         direction,
                                                         service,
                                                         site,
                                                         subsite,
                                                         True)

        for user in users:
            user.fi_uid = self.uid

        flashmessage.set_flash(_(u'Entity assigned to the facilitator'))

        return True


# --------- developer administration ---------

class DIAdmin(object):
    def __init__(self):
        self.user_repository = UserRepository()

    def _users(self):
        return self.user_repository.get_developers().order_by(
            UserData.lastname, UserData.firstname)

    def confirm_delete_di(self, uid, comp):
        full_name = self.user_repository.get_by_uid(uid).fullname

        confirm = PortalBox(Confirmation(
            _(u'The expert role of the user "%s" will be removed. '
              u'You must confirm this change.') % full_name,
            _(u'Ok'), _(u'Cancel')))

        if comp.call(confirm):
            user = self.user_repository.get_by_uid(uid)
            user.remove_role(RoleType.Developer)
            user.remove_responsibilities(RoleType.Developer)


class DIEditor(editor.Editor):
    def __init__(self, uid):
        super(DIEditor, self).__init__(None)
        self.uid = uid
        self.user_repository = UserRepository()
        self.domains = editor.Property(
            [str(elt.id) for elt in self.get_domains()])
        self.successor = editor.Property('').validate(
            validators.non_empty_string)
        self.di_business_area = editor.Property(
            self.user.di_business_area or '').validate(
            validators.non_empty_string)

    @property
    def user(self):
        return self.user_repository.get_by_uid(self.uid)

    def get_domains(self):
        return DomainRepository().get_by_di(self.user)

    def get_all_domains(self):
        return DomainRepository().get_all()

    def get_di_users(self):
        return self.user_repository.get_developers()

    def clear_domains(self):
        self.domains([])

    def update_domains(self):
        if not super(DIEditor, self).commit((), ('domains',)):
            return False

        user = self.user
        if user:
            domain_ids = [int(elt) for elt in self.domains.value]
            # FIXME: use the domain repository
            user.managed_domains = DomainData.query.filter(
                DomainData.id.in_(domain_ids)).all()

        flashmessage.set_flash(_(u'Domains changed'))

        return True

    def clear_successor(self):
        self.successor('')

    def idea_url(self, idea):
        return get_url_service().expand_url(['idea', idea.id])

    def replace_developer(self):
        if not super(DIEditor, self).commit((), ('successor',)):
            return False

        # prepare the content of the confirmation email
        assigned_ideas = IdeaRepository().get_assigned_to_developer(self.user)
        comment = '\n'.join(_('%(title)s: %(url)s') % dict(title=idea.title,
                                                           url=self.idea_url(
                                                               idea))
                            for idea in assigned_ideas)

        # transfer the DI responsibilities to the new user
        new_developer = self.user_repository.get_by_uid(self.successor())
        self.user.transfer_responsibilities(RoleType.Developer, new_developer)

        # send the confirmation email
        mail_notification.send('mail-developer-replaced.html',
                               to=new_developer,
                               previous_di=self.user,
                               comment=comment)

        flashmessage.set_flash(_(u'Expert replaced'))

        return True

    def update_di_business_area(self):
        if not super(DIEditor, self).commit((), ('di_business_area',)):
            return False

        self.user.di_business_area = self.di_business_area.value

        flashmessage.set_flash(_(u"Expert's business area updated"))

        return True
