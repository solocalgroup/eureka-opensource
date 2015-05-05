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

import os

from nagare import presentation, security
from nagare.i18n import _

from eureka.pkg import version

from eureka.domain.queries import get_all_published_ideas
from eureka.domain.repositories import IdeaRepository
from eureka.infrastructure.urls import get_url_service
from eureka.ui.desktop.portal import Portal
from eureka.ui.desktop import APP_TITLE
from eureka.ui.desktop.user.comp import User


@presentation.render_for(Portal)
def render_portal(self, h, comp, *args):

    # show the modal window, if any
    if self.modal():
        h << self.modal

    # show the main content
    h << self.content

    h.a('home', href=h.request.application_url)

    return h.root


@presentation.render_for(Portal, model='published_ideas')
def render_portal(self, h, comp, *args):
    with h.rss(version='0.91'):
        with h.channel:
            h << h.title(APP_TITLE)
            h << h.link(get_url_service().base_url)
            h << h.description(_('Ideas'))

            for idea in get_all_published_ideas().limit(10):
                with h.item:
                    h << h.title(idea.title)
                    h << h.link(get_url_service().expand_url(['idea', idea.id], relative=False))
                    h << h.description(idea.description)
                    h << h.pubDate(idea.publication_date.strftime('%a, %d %b %Y %H:%M:%S'))

    return h.root


@presentation.render_for(Portal, model='xml_published_ideas')
def render_portal_xml_published_ideas(self, h, comp, *args, **kw):
    ir = IdeaRepository()
    with h.ideas:
        for idea in get_all_published_ideas().limit(10):
            with h.idea:
                h << h.title(idea.title)
                h << h.description(idea.description)
                # The author is not available in the idea result
                i = ir.get_by_id(idea.id)
                user_data = i.authors[0] if i.authors else None
                # We must wrap it with the heavyweight User class to access the photo_url
                user = User(None, user_data.uid)
                with h.author:
                    h << h.uid(user.uid)
                    h << h.lastname(user.user.lastname)
                    h << h.firstname(user.user.firstname)
                    h << h.avatar(user.photo_url)
    return h.root


@presentation.render_for(Portal, model='welcome')
def render_portal_welcome(self, h, comp, *args):
    with h.div(class_='welcome'):
        with h.a(href="welcome").action(self.show_welcome):
            h << _(u"Welcome to") << " "
            h << "EURE" << h.span("K", style="color:#AB0552;") << "A"
    return h.root


@presentation.render_for(Portal, model="footer")
def render_portal_footer(self, h, comp, *args):
    with h.footer:
        h << self.footer_menu
        h << h.br << _(u'Eurêka © Solocal 2014')
        h << ' - ' << _('Version %s') % version
    return h.root


@presentation.render_for(Portal, model="one_col")
@presentation.render_for(Portal, model="two_cols")
def render_portal_one_col(self, h, comp, *args):
    with h.aside:
        h << h.header(h.a(class_="logo", href=h.request.application_url))
        with h.nav:
            h << self.menu

        if self.idea_submit() is not None:
            h << self.idea_submit

        if self.poll():
            h << self.poll
        else:
            h << self.idea_chart

        h << comp.render(h, model='footer')

    with h.section(class_='main-content'):
        with h.div(class_='footer-trick'):
            with h.header:
                with h.div(class_='tools'):
                    h << self.locale_box
                    h << self.login_box

                with h.div(class_='search'):
                    h << self.search.render(h.AsyncRenderer())

            h << self.inner_content
    return h.root


@presentation.render_for(Portal, model="navigation_top")
def render_portal_navigation_top(self, h, comp, *args):
    # FIXME: use a TabContainer instead
    with h.div(class_="nav-box"):
        with h.ul:
            with h.li(class_='current' if self.selected_tab == 'home' else ''):
                h << h.a(_(u'Home'),
                         title=_(u"Go to the home page"),
                         href='home').action(self.show_home)

            # challenges
            with h.li(class_='current' if self.selected_tab == 'challenge' else ''):
                h << h.a(_(u'Challenge'),
                         title=_(u"View, comment and vote for challenge ideas"),
                         href='challenges').action(self.show_challenge_ideas)

            # ideas
            with h.li(class_='current' if self.selected_tab == 'ideas' else ''):
                h << h.a(_(u'Ideas'),
                         title=_(u"View, comment and vote for ideas"),
                         href='ideas').action(self.show_ideas)

            # admininistration menu
            if security.has_permissions('show_administration_menu', self):
                with h.li(class_='current' if self.selected_tab == 'administration' else ''):
                    h << h.a(_(u'Administration'),
                             href='administration').action(self.show_administration_menu)

            # Help
            with h.li(class_='current' if self.selected_tab == 'help' else ''):
                h << h.a(_(u'Help'),
                         href="help")

    return h.root


@presentation.render_for(Portal, model="navigation_bottom")
def render_portal_navigation_bottom(self, h, comp, *args):
    with h.div(class_="nav-box rounded"):
        with h.ul:
            with h.li:
                h << h.a(_(u'Help'), href='help')
            with h.li:
                h << h.a(_(u'Suggestions'), href='improvements')
            with h.li:
                h << h.a(_(u'Contact us'), href='contact_us')
            with h.li:
                h << h.a(_(u'Terms of use'), href="terms_of_use")

    return h.root
