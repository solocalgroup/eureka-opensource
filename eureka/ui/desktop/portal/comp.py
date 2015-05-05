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

from eureka.ui.desktop.poll import Poll

from peak.rules import when

from nagare import component, security
from nagare.i18n import _
from webob.exc import HTTPNotFound
from eureka.domain.models import ArticleType, IdeaData, StateData
from eureka.domain.queries import (get_all_published_ideas_unordered,
                                   get_searched_ideas,
                                   get_all_published_ideas,
                                   get_all_user_ideas_with_state,
                                   get_fi_ideas_count,
                                   get_fi_ideas_with_state,
                                   get_di_ideas_with_state,
                                   get_published_tag_ideas,
                                   get_user_ideas_count,
                                   get_di_ideas_count,
                                   get_fi_process_ideas, get_di_process_ideas,
                                   get_all_enabled_polls)
from eureka.infrastructure.tools import is_integer, is_string
from eureka.infrastructure.security import get_current_user
from eureka.ui.common.yui2 import ModalBox
from eureka.ui.common.menu import Menu

from eureka.ui.desktop.article import Article, ArticleBox, ArticleBlock
from eureka.ui.desktop.idea import (SubmitIdeaBox, IdeaEditor, IdeaPager,
                                    IdeaBarChart, IdeaPagerBox)
from eureka.ui.desktop.pager import InfinitePager
from eureka.ui.desktop.staticcontent import (OnlineShop, FAQ, TermsOfUse, Welcome)
from eureka.ui.desktop.basket import IdeaBasket
from eureka.ui.desktop.challenge import Challenge
from eureka.ui.desktop.admin import Administration

from eureka.ui.desktop.search import SearchBlock
from eureka.ui.desktop.suggestion import (SubmitSuggestion, SuggestionsPager)
from eureka.ui.desktop.user import (User, ProfileBox,
                                    UserBrowser, PasswordEditor)

from eureka.ui.desktop.login import (Login, LoginEvent,
                                     LogoutEvent, CancelLoginEvent)  # @UnusedImport - needed for peak-rules
from eureka.ui.desktop.contact import Contact
from eureka.ui.desktop.resetpassword import (ResetPassword,
                                             ResetPasswordConfirmation,
                                             ResetPasswordEvent)  # @UnusedImport - needed for peak-rules

from .locale import LocaleChoice, LocaleChangeEvent
from .challenges import ChallengePage
from eureka.ui.common.box import PagerBox, PortalBox
from .home import HomePage, HomeBlock


class Portal(object):
    def __init__(self, configuration):
        super(Portal, self).__init__()

        self.configuration = configuration

        self.email_unique = True
        self.can_delete_users = True
        self.locale_box = component.Component(None)
        self.locale_box.on_answer(self.on_answer)

        self.menu_items = []
        self.menu = component.Component(None)
        self.menu.on_answer(self.select_tab)

        self.footer_menu_items = []
        self.footer_menu = component.Component(None)
        self.footer_menu.on_answer(self.select_footer_tab)

        self.idea_submit = component.Component(None)
        self.content = component.Component(None)
        self.inner_content = component.Component(None)
        self.modal = component.Component(None)

        # FIXME: what is idea_pager meant for?
        self.idea_pager = component.Component(None)

        # Search block
        self.search = component.Component(None)

        # rightcol charts
        self.idea_chart = component.Component(None)

        self.welcome = component.Component(None)
        self.online_shop = component.Component(None)
        self.faq = component.Component(None)
        self.terms_of_use = component.Component(None)

        # article blocks
        self.ongoing_block = component.Component(
            HomeBlock('ongoing', ArticleBox(ArticleType.Ongoing, 3)))
        self.news_block = component.Component(
            HomeBlock('news', ArticleBox(ArticleType.News, 5)))

        self.login_box = component.Component(None)
        self.login_box.on_answer(self.on_answer)

        self.poll = component.Component(None)

        self.initial_setup()

    def on_answer(self, answer):
        return _handle_answer(self, answer)

    def change_locale(self, locale):
        self.initial_setup()

    def initial_setup(self):

        poll = get_all_enabled_polls().first()
        if poll:
            self.poll = component.Component(Poll(poll.id))
        else:
            self.poll = component.Component(None)

        self.locale_box.becomes(LocaleChoice())

        self.idea_submit.becomes(SubmitIdeaBox(self))
        self.search.becomes(SearchBlock(self))

        self.idea_chart.becomes(IdeaBarChart(self))

        self.welcome.becomes(Welcome(self))
        self.online_shop.becomes(OnlineShop(self))
        self.faq.becomes(FAQ(self))
        self.terms_of_use.becomes(TermsOfUse(self))

        self.login_box.becomes(Login())

        # Note: setup done here because we need to access the current user and check the
        #       permissions in order to setup the component but they are not available when
        #       the Portal component is created.

        # password change modal dialog
        current_user = get_current_user()
        if current_user and current_user.should_change_password():
            self.show_password_editor(current_user)

        current_user = get_current_user()
        if current_user:
            self.login_box.becomes(User(self, current_user),
                                   model='login_status')

        self.menu_items = [
            (_(u'home'), _(u"Go to the home page"), 'home', self.show_home),
            (_(u'news'), None, 'news', self.show_articles_by_type),
            (_(u'challenge'), _(u"View, comment and vote for challenge ideas"),
             'challenges', self.show_challenge_ideas),
            (_(u'ideas'), _(u"View, comment and vote for ideas"), 'ideas',
             self.show_ideas),
        ]

        self.menu_items.extend([
            (_(u"discover eurêka"), None, 'welcome', self.show_welcome),
            (_(u'gifts'), None, 'shop', self.show_shop),
            (_(u'help'), None, 'help', self.show_help),
            (_(u'contact us'), None, 'contact_us', self.show_contact)
        ])

        self.menu.becomes(Menu(self.menu_items), model='list')

        self.footer_menu_items = [(_(u'Help'), None, 'help', self.show_help),
                                  (_(u'Suggestions'), None, 'improvements',
                                   self.show_suggestions),
                                  (_(u'Terms of use'), None, 'terms_of_use',
                                   self.show_terms_of_use), ]
        self.footer_menu.becomes(Menu(self.footer_menu_items), model='links')

        # initial the content if necessary (that is, when no presentation.init_for rule was
        # called)
        if not self.content():
            self.select_tab(0)

    def login(self):
        self.initial_setup()

    def logout(self):
        security.get_manager().logout()
        self.login_box.becomes(Login())

    def with_login(self, action, *args, **kwargs):
        if get_current_user():
            action(*args, **kwargs)
            return

        def on_answer(answer):
            self.initial_setup()
            if isinstance(answer, LoginEvent):
                action(*args, **kwargs)
            elif isinstance(answer, ResetPasswordEvent):
                self.show_reset_password()

        self._show_modal(Login(), model='prompt',
                         title=_('You must log in to perform this action'),
                         on_answer=on_answer)

    def show_password_editor(self, user):
        self._show_modal(PasswordEditor(user, with_cancel=True),
                         title=_('Please change your password'))

    def show_reset_password(self):
        self._show_modal(ResetPassword(),
                         title=_('Reset my password'))

    def confirm_reset_password(self, uid, token):
        confirmation = ResetPasswordConfirmation(uid)
        if confirmation.confirm_reset_password(token):
            self.show_password_editor(uid)
        else:
            self._show_modal(confirmation, model='failure',
                             title=_("Password reset failure!"))

    def _show_modal(self, o, model=0, title=None, on_answer=None):
        """Utility function that shows a component in a modal window"""

        def _on_answer(answer):
            self.modal.becomes(None)
            if on_answer:
                on_answer(answer)

        inner_comp = component.Component(o, model=model)
        modal_box = ModalBox(inner_comp,
                             title=title,
                             width=500,
                             closable=False)
        self.modal.becomes(modal_box).on_answer(_on_answer)

    def _show(self, o, model=0, selected_tab=None, with_idea_submit=False,
              with_two_cols=False):
        """Utility function that shows a top-level component in the portal"""
        # change the inner content
        self.inner_content.becomes(o, model=model)

        if with_two_cols:
            self.content.becomes(self, model='two_cols')
        else:
            self.content.becomes(self, model='one_col')

        self.idea_submit.becomes(SubmitIdeaBox(self))

        menu_items = [menu_item[2] for menu_item in self.menu_items]
        if selected_tab in menu_items:
            self.menu().selected(menu_items.index(selected_tab))

        return self.inner_content

    def _uid(self, user=None):
        if user is None:
            user = get_current_user()
            assert user

        return user if is_string(user) else user.uid

    def select_tab(self, index):
        callback = self.menu_items[index][3]
        if callback:
            callback()
        self.menu().selected(index)

    @property
    def selected_tab(self):
        return self.menu().selected()

    def select_footer_tab(self, index):
        callback = self.footer_menu_items[index][3]
        if callback:
            callback()
        self.footer_menu().selected(index)

    def show_frontdesk(self):
        if security.has_permissions('show_administration_menu', self):
            self.show_administration_menu()
        elif security.has_permissions('show_di_basket', self):
            self.show_di_ideas_basket()
        elif security.has_permissions('show_fi_basket', self):
            self.show_fi_ideas_basket()
        else:
            self.show_home()

    def show_home(self):
        # FIXME: what is it used for?
        self.idea_pager.becomes(IdeaPager(self, get_all_published_ideas))
        return self._show(HomePage(self), selected_tab='home')

    def show_user_profile(self, user=None, selected_tab=None):
        uid = self._uid(user)
        return self._show(ProfileBox(self, uid, selected_tab=selected_tab,
                                     online_shop=OnlineShop),
                          with_idea_submit=True)

    def show_ideas(self):

        pager = IdeaPager(self, get_all_published_ideas_unordered)
        menu_items = (
            (_(u"Last published"), pager.last_published),
            (_(u"Progressing"), pager.progressing_ideas),
            (_(u"Most viewed"), pager.most_viewed),
            (_(u"Launched ideas"), pager.launched_ideas),
        )
        pager = InfinitePager(component.Component(pager, model='ideas-list'))
        box = IdeaPagerBox(pager, model='list', menu_items=menu_items)
        box.select_item(0)

        return self._show(box, selected_tab='ideas', with_idea_submit=True)

    def show_ideas_with_state(self, state):

        pager = IdeaPager(self,
                          lambda: get_all_published_ideas_unordered([state]))
        menu_items = (
            (_(u"Last published"), pager.last_published),
            (_(u"Progressing"), pager.progressing_ideas),
            (_(u"Most viewed"), pager.most_viewed),
            (_(u"Launched ideas"), pager.launched_ideas),
        )
        pager = InfinitePager(component.Component(pager, model='ideas-list'))
        box = IdeaPagerBox(pager, model='list', menu_items=menu_items)
        box.select_item(0)

        return self._show(box, selected_tab='ideas', with_idea_submit=True)

    def show_idea(self, idea_id):
        # FIXME: we should not use a pager to show a single idea
        c = self.show_ideas()
        c().pager().goto(idea_id)

    def show_most_viewed_ideas(self):

        pager = IdeaPager(self, get_all_published_ideas_unordered)
        menu_items = (
            (_(u"Last published"), pager.last_published),
            (_(u"Progressing"), pager.progressing_ideas),
            (_(u"Most viewed"), pager.most_viewed),
            (_(u"Launched ideas"), pager.launched_ideas),
        )
        pager = InfinitePager(component.Component(pager, model='ideas-list'))
        box = IdeaPagerBox(pager, model='list', menu_items=menu_items)
        box.select_item(2)

        return self._show(box, selected_tab='ideas', with_idea_submit=True)

    def show_launched_ideas(self):

        pager = IdeaPager(self, get_all_published_ideas_unordered)
        menu_items = (
            (_(u"Last published"), pager.last_published),
            (_(u"Progressing"), pager.progressing_ideas),
            (_(u"Most viewed"), pager.most_viewed),
            (_(u"Launched ideas"), pager.launched_ideas),
        )
        pager = InfinitePager(component.Component(pager, model='ideas-list'))
        box = IdeaPagerBox(pager, model='list', menu_items=menu_items)
        box.select_item(3)

        return self._show(box, selected_tab='ideas', with_idea_submit=True)

    def show_user_ideas_basket(self, user=None):
        uid = self._uid(user)
        basket = IdeaBasket(self, uid, get_user_ideas_count(uid),
                            _(u'My Ideas'))
        return self._show(basket, selected_tab='my')

    def show_user_ideas_basket_with_state(self, state_id, user=None):
        uid = self._uid(user)
        pager = IdeaPager(self, get_all_user_ideas_with_state(uid, state_id))
        pager = InfinitePager(component.Component(pager, model='ideas-list'))
        return self._show(IdeaPagerBox(pager, model='list'), selected_tab='my',
                          with_idea_submit=True)

    def fi_ideas_basket_count(self, user=None):
        return get_fi_process_ideas(self._uid(user))().count()

    def show_fi_ideas_basket(self, user=None):
        uid = self._uid(user)
        basket = IdeaBasket(self, uid, get_fi_ideas_count(uid),
                            _(u'Facilitator basket'))
        return self._show(basket, model='FI', selected_tab='fi_basket')

    def show_fi_dsig_ideas_basket(self, user=None):
        uid = self._uid(user)
        basket = IdeaBasket(self, uid, get_fi_ideas_count(uid),
                            _(u'Facilitator basket'))
        return self._show(basket, model='FI_DSIG', selected_tab='fi_basket')

    def show_fi_ideas_basket_with_state(self, state_id, user=None):
        uid = self._uid(user)
        pager = IdeaPager(self, get_fi_ideas_with_state(uid, state_id))
        pager = InfinitePager(component.Component(pager, model='ideas-list'))
        return self._show(IdeaPagerBox(pager, model='list'),
                          selected_tab='fi_basket')

    def di_ideas_basket_count(self, user=None):
        return get_di_process_ideas(self._uid(user))().count()

    def show_di_ideas_basket(self, user=None):
        uid = self._uid(user)
        basket = IdeaBasket(self, uid, get_di_ideas_count(uid),
                            _(u'Developer basket'))
        return self._show(basket, model='DI', selected_tab='di_basket')

    def show_di_dsig_ideas_basket(self, user=None):
        uid = self._uid(user)
        basket = IdeaBasket(self, uid, get_di_ideas_count(uid),
                            _(u'Developer basket'))
        return self._show(basket, model='DI_DSIG', selected_tab='di_basket')

    def show_di_ideas_basket_with_state(self, state_id, user=None):
        uid = self._uid(user)
        pager = IdeaPager(self, get_di_ideas_with_state(uid, state_id))
        pager = InfinitePager(component.Component(pager, model='ideas-list'))
        return self._show(IdeaPagerBox(pager, model='list'),
                          selected_tab='di_basket')

    def show_dsig_ideas_basket(self, user=None):
        uid = self._uid(user)
        basket = IdeaBasket(self, uid, StateData.get_ideas_count_by_states,
                            _(u'DSIG basket'))
        return self._show(basket, model='DSIG', selected_tab='dsig_basket')

    # challenge-related pages
    def show_challenge(self, challenge_id):
        try:
            challenge = Challenge(self, challenge_id)
        except ValueError:
            raise HTTPNotFound()

        return self._show(challenge, selected_tab='challenge',
                          with_two_cols=True)

    def show_challenge_ideas(self, challenge_id=None):
        # FIXME: what about removing ChallengePage and replace it by a PortalBox?
        # FIXME: late import required?
        return self._show(ChallengePage(self, challenge_id),
                          selected_tab='challenges', with_idea_submit=True)

    def show_administration_menu(self):
        return self._show(
            Administration(
                parent=self,
                configuration=self.configuration,
                email_unique=self.email_unique,
                can_delete_users=self.can_delete_users,),
            selected_tab='administration')

    def search_ideas(self, pattern):
        if is_integer(pattern):
            idea_id = int(pattern)
            pager = IdeaPager(
                self,
                lambda idea_id=idea_id: get_all_published_ideas_unordered().filter(IdeaData.id == idea_id))
        else:
            pager = IdeaPager(
                self,
                lambda pattern=pattern: get_searched_ideas(pattern))
        pager.change_order("publication_date_desc")
        pager = InfinitePager(component.Component(pager, model='ideas-list'))
        box = IdeaPagerBox(pager, model='ideas-list')
        return self._show(box, selected_tab='search')

    def search_users(self, pattern):
        pager = UserBrowser(self, pattern)
        box = PagerBox(pager, title=_(u'Search results for %s') % pattern)
        return self._show(box, selected_tab='search')

    def show_tag_ideas(self, tag_label):
        pager = IdeaPager(self, get_published_tag_ideas(tag_label))
        pager.change_order('publication_date_desc')
        pager = InfinitePager(component.Component(pager, model='ideas-list'))
        box = IdeaPagerBox(pager)
        return self._show(box, selected_tab='ideas')

    def show_welcome(self):
        return self._show(self.welcome, with_two_cols=True)

    def show_shop(self):
        return self._show(self.online_shop, with_two_cols=True)

    def show_terms_of_use(self):
        return self._show(self.terms_of_use, with_two_cols=True)

    def show_help(self, section=None):
        self.faq().open_section(section)
        return self._show(self.faq, selected_tab='help', with_two_cols=True)

    def show_articles_by_type(self, type=None):
        block = ArticleBox(type or '')
        return self._show(block, model='full')

    def show_article(self, article_id):
        article = Article(article_id)
        return self._show(PortalBox(article), with_two_cols=True,
                          with_idea_submit=True)

    def show_domain(self, domain_id, domain_label):
        pager = IdeaPager(self, get_all_published_ideas_unordered)
        # FIXME: should be moved into an appropriate method of the pager
        pager.change_filter_domain('domain_%d' % domain_id)
        pager.change_order('publication_date_desc')
        pager = InfinitePager(
            component.Component(pager, model='domain-ideas-list'))
        return self._show(IdeaPagerBox(pager, model='list'),
                          selected_tab='ideas')

    def show_submit_idea(self, challenge_id=None):
        box = PortalBox(IdeaEditor(self, challenge_id),
                        model='form',
                        css_class='sendIdeaBox')
        return self._show(box)

    def show_contact(self, subject=None, body=None):
        return self._show(PortalBox(Contact(self, subject=subject, body=body)))

    def show_suggestions(self):
        return self._show(PortalBox(SuggestionsPager(self)))

    def show_submit_suggestion(self):
        return self._show(PortalBox(SubmitSuggestion(self)))


# portal's on_answer handlers
def _handle_answer(self, answer):
    raise NotImplementedError('Unhandled answer: %s' % answer)


@when(_handle_answer, "isinstance(answer, LocaleChangeEvent)")
def _handle_answer_login_event(self, answer):
    self.initial_setup()


@when(_handle_answer, "isinstance(answer, LoginEvent)")
def _handle_answer_login_event(self, answer):
    self.login()


@when(_handle_answer, "isinstance(answer, CancelLoginEvent)")
def _handle_answer_logout_event(self, answer):
    pass


@when(_handle_answer, "isinstance(answer, LogoutEvent)")
def _handle_answer_logout_event(self, answer):
    self.logout()
    self.initial_setup()


@when(_handle_answer, "isinstance(answer, ResetPasswordEvent)")
def _handle_answer_reset_password_event(self, answer):
    self.show_reset_password()
