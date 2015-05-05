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

from peak.rules import when

from nagare import security

from eureka.domain.queries import get_all_user_ideas, get_published_user_ideas
from eureka.infrastructure import event_management
from .comp import Portal  # @UnusedImport - needed for peak-rules
from eureka.ui.desktop.user import User  # @UnusedImport - needed for peak-rules
from eureka.ui.desktop.idea import IdeaPager


# FIXME: remove all access to idea_submit, content, inner_content or idea_pager: should become a show_xxx in the portal comp

@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'VIEW_IDEA' and kwds.get('mode') == u'view'")
def _handle_signal_view_idea(self, sender, signal, *args, **kwds):
    # self.idea_submit.becomes(None)
    self.content.becomes(self, model='one_col')
    if hasattr(sender, 'idea_pager'):
        self.inner_content.becomes(sender.idea_pager, model='detail')
    else:
        self.inner_content.becomes(sender, model='detail')


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'VIEW_IDEA' and kwds.get('mode') == u'view' and kwds.get('idea_id')")
def _handle_signal_view_idea_anonymous(self, sender, signal, *args, **kwds):
    if self.idea_pager() is None:
        self.show_home()

    self.idea_pager().goto(kwds.get('idea_id'))


@when(event_management._handle_signal,
      "isinstance(self, Portal) and isinstance(sender, User) and signal == 'VIEW_IDEA' and kwds.get('mode') == u'view' and kwds.get('idea_id')")
def _handle_signal_view_idea_user(self, sender, signal, *args, **kwds):
    if security.has_permissions('view_unpublished_ideas', sender.user):
        p = IdeaPager(self, lambda: get_all_user_ideas(sender.uid), 9)
    else:
        p = IdeaPager(self, lambda: get_published_user_ideas(sender.uid), 9)
    p.goto(kwds.get('idea_id'))


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'VIEW_IDEA' and kwds.get('mode') == u'edit'")
def _handle_signal_view_idea_edit(self, sender, signal, *args, **kwds):
    # self.idea_submit.becomes(None)
    self.content.becomes(self, model='one_col')
    if hasattr(sender, 'idea_pager'):
        self.inner_content.becomes(sender.idea_pager, model='detail_edit')
    else:
        self.inner_content.becomes(sender, model='detail_edit')


@when(event_management._handle_signal,
      "isinstance(self, Portal) and isinstance(sender, User) and signal == 'VIEW_IDEA' and kwds.get('mode') == u'edit' and kwds.get('idea_id')")
def _handle_signal_view_idea_edit_user(self, sender, signal, *args, **kwds):
    # self.idea_submit.becomes(None)
    self.content.becomes(self, model='one_col')
    if security.has_permissions('view_unpublished_ideas', sender.user):
        p = IdeaPager(self, lambda: get_all_user_ideas(sender.uid), 9)
    else:
        p = IdeaPager(self, lambda: get_published_user_ideas(sender.uid), 9)

    p.goto(kwds.get('idea_id'))


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'WITH_LOGIN'")
def _handle_signal_with_login(self, sender, signal, action, *args, **kwargs):
    self.with_login(action, *args, **kwargs)


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'VIEW_FRONTDESK'")
def _handle_signal_view_frontdesk(self, sender, signal):
    self.show_frontdesk()


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'VIEW_IDEAS_WITH_STATE' and kwds.get('state')")
def _handle_signal_view_ideas_with_state(self, sender, signal, *args, **kwds):
    self.show_ideas_with_state(kwds.get('state'))


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'VIEW_MY_IDEAS' and kwds.get('state')")
def _handle_signal_view_my_ideas(self, sender, signal, *args, **kwds):
    self.show_user_ideas_basket_with_state(kwds.get('state'))


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'VIEW_IDEAS'")
def _handle_signal_view_ideas(self, sender, signal, *args, **kwds):
    self.show_user_ideas_basket()


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'VIEW_LAUNCHED_IDEAS'")
def _handle_signal_view_launched_ideas(self, sender, signal, *args, **kwds):
    self.show_launched_ideas()


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'VIEW_WELCOME'")
def _handle_signal_view_welcome(self, sender, signal, *args, **kwds):
    self.show_welcome()


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'VIEW_SHOP'")
def _handle_signal_view_shop(self, sender, signal, *args, **kwds):
    self.show_shop()


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'VIEW_HELP'")
def _handle_signal_view_help(self, sender, signal, *args, **kwds):
    self.show_help(kwds.get('section'))


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'VIEW_DOMAIN_IDEAS' and kwds.get('domain_id') and kwds.get('domain_label')")
def _handle_signal_view_domain_ideas(self, sender, signal, *args, **kwds):
    self.show_domain(kwds.get('domain_id'), kwds.get('domain_label'))


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal=='SUBMIT_SUGGESTION'")
def _handle_signal_submit_suggestion(self, sender, signal, *args, **kwds):
    self.show_submit_suggestion()


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'VIEW_DSIG_BASKET'")
def _handle_signal_view_dsig_basket(self, sender, signal, *args, **kwds):
    self.show_dsig_ideas_basket()


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'VIEW_TAG_IDEAS' and kwds.get('label')")
def _handle_signal_view_tag_ideas(self, sender, signal, *args, **kwds):
    self.show_tag_ideas(kwds.get('label'))


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'VIEW_USER_PROFILE'")
def _handle_signal_view_user_profile(self, sender, signal, *args, **kwds):
    self.show_user_profile(kwds.get('user_uid'))


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'VIEW_ADMINISTRATION'")
def _handle_signal_view_administration(self, sender, signal, *args, **kwds):
    self.show_administration_menu()


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'VIEW_USER_TRACKED_IDEAS'")
def _handle_signal_view_user_tracked_ideas(self, sender, signal, *args, **kwds):
    self.show_user_profile(kwds.get('user_uid'), selected_tab='tracked_ideas')


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'VIEW_USER_BASKET'")
def _handle_signal_view_user_basket(self, sender, signal, *args, **kwds):
    self.show_user_ideas_basket(kwds.get('user_uid'))


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'VIEW_FI_IDEAS' and kwds.get('state')")
def _handle_signal_view_fi_ideas(self, sender, signal, *args, **kwds):
    self.show_fi_ideas_basket_with_state(kwds.get('state'))


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'VIEW_DI_BASKET'")
def _handle_signal_view_di_ideas_basket(self, sender, signal, *args, **kwds):
    self.show_di_ideas_basket()


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'VIEW_FI_BASKET'")
def _handle_signal_view_di_ideas_basket(self, sender, signal, *args, **kwds):
    self.show_fi_ideas_basket()


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'VIEW_DI_IDEAS' and kwds.get('state')")
def _handle_signal_view_di_ideas(self, sender, signal, *args, **kwds):
    self.show_di_ideas_basket_with_state(kwds.get('state'))


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'VIEW_DI_DSIG_IDEAS' and kwds.get('state') and kwds.get('user_uid')")
def _handle_signal_view_dsig_ideas(self, sender, signal, *args, **kwds):
    self.show_di_ideas_basket_with_state(kwds.get('state'),
                                         kwds.get('user_uid'))


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'VIEW_FI_DSIG_IDEAS' and kwds.get('state') and kwds.get('user_uid')")
def _handle_signal_view_fi_dsig_ideas(self, sender, signal, *args, **kwds):
    self.show_fi_ideas_basket_with_state(kwds.get('state'),
                                         kwds.get('user_uid'))


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'SUBMIT_IDEA'")
def _handle_signal_submit_idea(self, sender, signal, *args, **kwds):
    self.show_submit_idea(kwds.get('challenge_id'))


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'SEARCH_USERS' and kwds.get('pattern')")
def _handle_signal_search_users(self, sender, signal, *args, **kwds):
    self.search_users(kwds.get('pattern'))


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'SEARCH_IDEAS' and kwds.get('pattern')")
def _handle_signal_search_ideas(self, sender, signal, *args, **kwds):
    self.search_ideas(kwds.get('pattern'))


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'CHANGE_PASSWORD'")
def _handle_signal_change_password(self, sender, signal, *args, **kwds):
    self.show_frontdesk()


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'VIEW_DI_IDEA_SELECTOR' and kwds.get('user_uid')")
def _handle_signal_view_di_idea_selector(self, sender, signal, *args, **kwds):
    self.show_di_dsig_ideas_basket(kwds.get('user_uid'))


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'VIEW_FI_IDEA_SELECTOR' and kwds.get('user_uid')")
def _handle_signal_view_fi_idea_selector(self, sender, signal, *args, **kwds):
    self.show_fi_dsig_ideas_basket(kwds.get('user_uid'))


@when(event_management._handle_signal,
      "isinstance(self, Portal) and signal == 'VIEW_CHALLENGE' and kwds.get('challenge_id')")
def _handle_signal_view_challenge(self, sender, signal, *args, **kwds):
    self.show_challenge(kwds.get('challenge_id'))
