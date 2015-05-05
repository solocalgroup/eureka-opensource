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

from datetime import datetime, timedelta
import operator

from nagare import security, var, component
from nagare.i18n import _

from eureka.domain.models import RoleType, PointData, RoleLabels
from eureka.domain.queries import (get_all_user_ideas,
                                   get_published_user_ideas,
                                   get_fi_process_ideas, get_di_process_ideas)
from eureka.domain.repositories import UserRepository
from eureka.infrastructure.urls import get_url_service
from eureka.infrastructure import event_management, registry
from eureka.infrastructure.avatars import photo_filename
from eureka.infrastructure.tools import is_string
from eureka.ui.common.yui2 import flashmessage
from eureka.ui.common.menu import Menu
from .editor import (PasswordEditor, AvatarEditor, UserFIEditor,
                     ProfileEditor, SettingsEditor)
from eureka.ui.desktop.idea import IdeaPager
from eureka.ui.desktop.pager import InfinitePager


class User(object):
    def __init__(self, parent, user):
        event_management._register_listener(parent, self)
        self.uid = user if is_string(user) else user.uid
        self.user_repository = UserRepository()
        self.pager = None

    @property
    def user(self):
        return self.user_repository.get_by_uid(self.uid)  # the user represented by this block

    @property
    def _photo_filename(self):
        return photo_filename(self.uid, self.user.photo_date)

    def thumbnail_url(self, size):
        return get_url_service().expand_url(['profile-thumbnails', size, self._photo_filename])

    @property
    def photo_url(self):
        return get_url_service().expand_url(['profile-photo', self._photo_filename])

    @property
    def privileged_roles(self):
        relevant_roles = (RoleType.DSIG, RoleType.Developer, RoleType.Facilitator)
        return [unicode(RoleLabels[role]) for role in relevant_roles if self.user.has_role(role)]

    def profile_url(self, uid=None):
        return get_url_service().expand_url(['profile', (uid or self.uid)])

    def view_profile(self, uid=None):
        event_management._emit_signal(self, "VIEW_USER_PROFILE", user_uid=(uid or self.uid))

    def view_tracked_ideas(self, uid=None):
        event_management._emit_signal(self, "VIEW_USER_TRACKED_IDEAS", user_uid=(uid or self.uid))

    def view_basket(self, uid=None):
        event_management._emit_signal(self, "VIEW_USER_BASKET", user_uid=(uid or self.uid))

    def view_dsig_basket(self, uid=None):
        event_management._emit_signal(self, "VIEW_DSIG_BASKET", user_uid=(uid or self.uid))

    def view_di_basket(self, uid=None):
        event_management._emit_signal(self, "VIEW_DI_BASKET", user_uid=(uid or self.uid))

    def view_fi_basket(self, uid=None):
        event_management._emit_signal(self, "VIEW_FI_BASKET", user_uid=(uid or self.uid))

    def view_administration(self, uid=None):
        event_management._emit_signal(self, "VIEW_ADMINISTRATION")

    @property
    def _ideas(self):
        if security.has_permissions('view_unpublished_ideas', self):
            return get_all_user_ideas(self.uid)
        else:
            return get_published_user_ideas(self.uid)

    @property
    def ideas_count(self):
        return self._ideas.count()

    def get_idea_pager(self):
        # FIXME: late import to avoid circular dependencies problem

        if self.pager is None:

            idea_pager = IdeaPager(self, lambda: self._ideas)
            idea_pager.change_transform("user")
            idea_pager.change_order("publication_date_desc")
            self.pager = InfinitePager(component.Component(idea_pager, model='ideas-list'))
        return self.pager

    def get_tracked_idea_count(self):
        return len(self.get_tracked_ideas())

    def get_tracked_ideas(self):
        return self.user.tracked_ideas

    def remove_tracked_idea(self, idea_id):
        self.user.untrack_idea(idea_id)
        flashmessage.set_flash(_(u'Idea removed from tracking'))

    def events_history(self, days_ago=30):
        date = datetime.today() - timedelta(days_ago)
        return sorted(self.user.visible_events(date),
                      key=operator.attrgetter('date'), reverse=True)

    def new_events_count(self, days_ago=30):
        date = datetime.today() - timedelta(days_ago)
        return len(set([e.idea.id for e in self.user.unread_events(date)]))

    def remove_event(self, event_id):
        self.user.hide_event(event_id)
        flashmessage.set_flash(_(u'Event removed'))

    def read_event(self, event_id):
        event = self.user.read_event(event_id)
        self.view_idea(event.idea.id)

    def read_all_events(self):
        self.user.read_all_events()

    def get_fi_ideas_basket_count(self):
        return get_fi_process_ideas(self.uid)().count()

    def get_di_ideas_basket_count(self):
        return get_di_process_ideas(self.uid)().count()


class ProfileBox(object):
    """Show profile pages in a profile box"""
    def __init__(self, parent, user, selected_tab=None, online_shop=None):
        self.parent = parent
        event_management._register_listener(parent, self)
        self.uid = user if is_string(user) else user.uid
        self.user_repository = UserRepository()
        self.user_comp = User(parent, self.uid)
        self.tabs = self._create_tabs()
        selected_tab = selected_tab if selected_tab in self.tabs else 'profile'
        self.selected_tab = var.Var(selected_tab)

        # inner components displayed in the tabs or the header
        # FIXME: all these should be wrapped into a component.Component
        self.fi_editor = UserFIEditor(self.uid)
        event_management._register_listener(self, self.fi_editor)
        self.avatar_editor = AvatarEditor(self.uid)
        event_management._register_listener(self, self.avatar_editor)
        self.password_editor = PasswordEditor(self.user)
        event_management._register_listener(self, self.password_editor)
        self.profile_editor = ProfileEditor(self.user)
        event_management._register_listener(self, self.profile_editor)
        self.settings_editor = component.Component(SettingsEditor(self.user))
        event_management._register_listener(self, self.settings_editor())
        self.idea_pager = self._create_pager()
        # FIXME: the pager should not depend on the parent
        # event_management._register_listener(self, self.idea_pager)
        self.online_shop = online_shop(self)

        self.tab_labels = {
            'profile': _("My Profile") if self.is_mine else _("Her Profile"),
            'settings': _("My Settings") if self.is_mine else _("Her Settings"),
            'tracked_ideas': (_("My Tracked Ideas") if self.is_mine else _("Her Tracked Ideas")) + " (%d)" % self.new_events_count(),
            'ideas': (_("My Ideas") if self.is_mine else _("Her Ideas")) + " (%d)" % self.ideas_count,
            'points': (_("My Points") if self.is_mine else _("Her Points")) + " (%d)" % self.user.acquired_points,
            # 'rank': self.user.status_level_label,
        }

        self.menu_items = [(self.tab_labels[name], name, None, '', None) for name in self.tabs]

        self.menu = component.Component(Menu(self.menu_items),
                                        model='tab_renderer')
        self.menu.on_answer(self.select_tab)
        if selected_tab:
            index_tab = self.tabs.index(selected_tab)
        else:
            index_tab = 0
        self.select_tab(index_tab)

    def select_tab(self, value):
        self.selected_tab(self.menu_items[value][1])
        self.menu().selected(value)

    @property
    def user(self):
        return self.user_repository.get_by_uid(self.uid)

    @property
    def is_mine(self):
        current_user = security.get_user()
        return current_user and (current_user.uid == self.uid)

    def _create_tabs(self):
        can_edit = security.has_permissions('edit_user', self)
        can_view_tracked_ideas = security.has_permissions('view_tracked_ideas', self)

        menu_items = (
            ('profile', True),
            ('settings', can_edit),
            ('tracked_ideas', can_view_tracked_ideas),
            ('ideas', True),
            ('points', True),
            # ('rank', True),
        )
        return [name for name, enabled in menu_items if enabled]

    def profile_url(self, uid=None):
        return get_url_service().expand_url(['profile', (uid or self.uid)])

    def view_profile(self, uid=None):
        # FIXME: fix the mess with profile-related events
        event_management._emit_signal(self, "VIEW_USER_PROFILE", user_uid=(uid or self.uid))

    def show_status_level_help(self):
        event_management._emit_signal(self, "VIEW_HELP", section='faq_1_7bis')

    # roles related methods
    @property
    def privileged_roles(self):
        relevant_roles = (RoleType.DSIG, RoleType.Developer, RoleType.Facilitator)
        return [unicode(RoleLabels[role]) for role in relevant_roles if self.user.has_role(role)]

    # ideas related methods
    def _create_pager(self):
        # FIXME: late import to avoid circular dependencies problem

        idea_pager = IdeaPager(self, lambda: self._ideas)
        idea_pager.change_transform("user")
        idea_pager.change_order("publication_date_desc")
        idea_pager = InfinitePager(component.Component(idea_pager, model='ideas-list'))

        return idea_pager

    @property
    def _ideas(self):
        if security.has_permissions('view_unpublished_ideas', self):
            return get_all_user_ideas(self.uid)
        else:
            return get_published_user_ideas(self.uid)

    @property
    def ideas_count(self):
        return self._ideas.count()

    # events related methods
    def events(self, days_ago=30):
        date = datetime.today() - timedelta(days_ago)
        return sorted(self.user.visible_events(date), key=operator.attrgetter('date'), reverse=True)

    def new_events_count(self, days_ago=30):
        date = datetime.today() - timedelta(days_ago)
        return len(set([e.idea.id for e in self.user.unread_events(date)]))

    def hide_event(self, event_id):
        self.user.hide_event(event_id)
        flashmessage.set_flash(_(u'Event removed'))

    def read_event(self, event_id):
        event = self.user.read_event(event_id)
        self.view_idea(event.idea.id)

    def read_all_events(self):
        self.user.read_all_events()

    # tracked ideas related methods
    def tracked_ideas(self):
        return self.user.tracked_ideas

    def view_idea(self, idea_id):
        event_management._emit_signal(self, "VIEW_IDEA", mode='view', idea_id=idea_id)

    def remove_tracked_idea(self, idea_id):
        self.user.untrack_idea(idea_id)
        flashmessage.set_flash(_(u'Idea removed from tracking'))

    def remove_point(self, point_id):
        PointData.get(point_id).delete()
        flashmessage.set_flash(_(u"Points deleted"))
