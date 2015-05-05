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

from nagare import editor, security, component, validator
from nagare.i18n import _

from eureka.domain.models import UserData
from eureka.domain.repositories import UserRepository, DomainRepository
from eureka.infrastructure import validators
from eureka.infrastructure.tools import is_string
from eureka.ui.common.yui2 import flashmessage
from eureka.domain import mail_notification


class UserFIEditor(editor.Editor):
    def __init__(self, user):
        super(UserFIEditor, self).__init__(None)
        self.uid = user if is_string(user) else user.uid
        self.user_repository = UserRepository()
        fi_uid = self.user.fi.uid if self.user.fi else ''
        self.fi_uid = editor.Property(fi_uid).validate(
            validators.non_empty_string)

    @property
    def is_mine(self):
        current_user = security.get_user()
        return current_user and (current_user.uid == self.uid)

    @property
    def user(self):
        return self.user_repository.get_by_uid(self.uid)

    def get_facilitators(self):
        return UserData.get_facilitators()

    def commit(self):
        if not super(UserFIEditor, self).commit((), ('fi_uid',)):
            return False

        new_facilitator = self.user_repository.get_by_uid(self.fi_uid())
        self.user.fi = new_facilitator

        flashmessage.set_flash(_(u'Facilitator changed'))
        return True


class AvatarEditor(editor.Editor):
    def __init__(self, user):
        super(AvatarEditor, self).__init__(None)
        self.uid = user if is_string(user) else user.uid
        self.photo = editor.Property(self.user.photo).validate(
            self.validate_img)

    @property
    def user(self):
        return UserRepository().get_by_uid(self.uid)

    def validate_img(self, photo):
        if is_string(photo):
            return None
        return photo.file.read()

    def commit(self):
        if super(AvatarEditor, self).commit((), ('photo',)):
            user = self.user
            if self.photo.value:
                user.photo = self.photo.value
                flashmessage.set_flash(_(u'Avatar changed'))
                return True
        return False


class PasswordEditor(editor.Editor):
    def __init__(self, user, with_cancel=False):
        super(PasswordEditor, self).__init__(None)
        self.uid = user if is_string(user) else user.uid
        self.password = editor.Property('').validate(self.validate_password)
        self.password_confirm = editor.Property('').validate(
            self.validate_password_confirm)
        self.with_cancel = with_cancel

    @property
    def user(self):
        return UserRepository().get_by_uid(self.uid)

    def validate_password(self, v):
        error = self.user.validate_password(v)
        if error:
            raise ValueError(error)
        return v

    def validate_password_confirm(self, v):
        if self.password.value and self.password.value != v:
            raise ValueError(
                _(u'The password confirmation is different from the password'))
        return v

    def commit(self):
        if not super(PasswordEditor, self).commit(
                (),
                ('password', 'password_confirm')):
            return False  # failure

        user = self.user
        user.change_password(self.password.value)
        security.get_manager().update_current_user_credentials()
        flashmessage.set_flash(_(u'Your password has been changed'))
        return True  # success


class ProfileEditor(editor.Editor):
    def __init__(self, user):
        super(ProfileEditor, self).__init__(None)
        self.uid = user if is_string(user) else user.uid

        # editable fields
        self.description = editor.Property(self.user.description or '')
        self.competencies = editor.Property(self.user.competencies or '')
        self.hobbies = editor.Property(self.user.hobbies or '')
        self.expertises = editor.Property(self.user.expertises or '')
        self.specialty = editor.Property(self.user.specialty or '')
        self.work_phone = editor.Property(self.user.work_phone or '')
        self.mobile_phone = editor.Property(self.user.mobile_phone or '')

    @property
    def user(self):
        return UserRepository().get_by_uid(self.uid)

    def commit(self):
        if not super(ProfileEditor, self).commit():  # no property!?
            return False

        self.user.description = self.description.value
        self.user.competencies = self.competencies.value
        self.user.hobbies = self.hobbies.value
        self.user.expertises = self.expertises.value
        self.user.specialty = self.specialty.value
        self.user.work_phone = self.work_phone.value
        self.user.mobile_phone = self.mobile_phone.value
        flashmessage.set_flash(_(u'Your profile has been changed'))
        return True


class HomeSettingsEditor(editor.Editor):
    periods = [(0, u'All'),
               (1, u'Last 24 h'),
               (7, u'Last week'),
               (30, u'Last month')]

    def __init__(self, user):
        super(HomeSettingsEditor, self).__init__(None)
        self.uid = user if is_string(user) else user.uid
        home_settings = self.user.home_settings
        self.show_progressing_ideas = editor.Property(
            home_settings.show_progressing_ideas)
        self.show_tracked_ideas = editor.Property(
            home_settings.show_tracked_ideas)
        self.show_challenges_ideas = editor.Property(
            home_settings.show_challenges_ideas)
        selected_domains = [domain.id for domain in home_settings.domains]
        self.domains_choice = editor.Property(selected_domains)
        self.keyword_filter = editor.Property(
            home_settings.keyword_filter).validate(validator.StringValidator)
        self.period_filter = editor.Property(home_settings.period_filter)
        self.users_filter = editor.Property(
            ', '.join([u.email for u in home_settings.users_filter])).validate(
            validator.StringValidator)

    @property
    def domains(self):
        return DomainRepository().get_all()

    @property
    def user(self):
        return UserRepository().get_by_uid(self.uid)

    def reset_fields(self):
        self.show_progressing_ideas(False)
        self.show_tracked_ideas(False)
        self.show_challenges_ideas(False)
        self.domains_choice.set([])

    def commit(self):
        properties = ('show_progressing_ideas', 'show_tracked_ideas',
                      'show_challenges_ideas', 'domains_choice',
                      'keyword_filter', 'users_filter', 'period_filter')
        if not super(HomeSettingsEditor, self).is_validated(properties):
            return False

        domains = [domain for domain in self.domains if
                   domain.id in self.domains_choice.value]

        # write down the settings into the user's settings
        user = self.user
        home_settings = user.home_settings
        home_settings.show_progressing_ideas = self.show_progressing_ideas.value
        home_settings.show_tracked_ideas = self.show_tracked_ideas.value
        home_settings.show_challenges_ideas = self.show_challenges_ideas.value
        home_settings.domains = domains
        home_settings.keyword_filter = self.keyword_filter.value
        home_settings.period_filter = self.period_filter.value

        users_filter = [UserRepository().get_by_email(email.strip()) for email
                        in self.users_filter.value.split(',') if email.strip()]

        for followed in set(users_filter) - set(
                [u for u in home_settings.users_filter]):
            mail_notification.send('mail-followed-user-notify.html',
                                   to=followed, comment_author=user)
            # add entry in timeline
            user.add_timeline_user(followed)

        home_settings.users_filter = users_filter

        return True


class MailSettingsEditor(editor.Editor):
    def __init__(self, user):
        super(MailSettingsEditor, self).__init__(None)
        self.uid = user if is_string(user) else user.uid
        self.mail_delivery_frequency = editor.Property(
            self.user.mail_delivery_frequency)

    @property
    def user(self):
        return UserRepository().get_by_uid(self.uid)

    def commit(self):
        properties = ()
        if not super(MailSettingsEditor, self).is_validated(properties):
            return False

        user = self.user
        user.mail_delivery_frequency = self.mail_delivery_frequency.value
        return True


class SettingsEditor(object):
    def __init__(self, user):
        self.home_settings = component.Component(HomeSettingsEditor(user))
        self.mail_settings = component.Component(MailSettingsEditor(user))
        self.password_settings = component.Component(PasswordEditor(user))
