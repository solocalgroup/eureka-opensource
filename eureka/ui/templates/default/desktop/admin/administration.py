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

from eureka.ui.desktop.admin import Administration
from nagare import presentation, security
from nagare.i18n import _, format_date


@presentation.render_for(Administration)
def render_administration(self, h, comp, *args):
    with h.div(class_='admin-page'):
        if self.content() and security.get_user():
            h << self.content
        else:
            h << comp.render(h, model='menu')
    return h.root


# FIX urls: the administration part should be owned by the Administration component
@presentation.render_for(Administration, model='menu')
def render_administration_menu(self, h, comp, *args):
    with h.div(class_="admin-menu rounded"):

        h << h.h2(_(u'Statistics'))
        with h.ul:
            with h.li:
                with h.a(class_="dashboard").action(self.show_dashboard):
                    h << _(u'Dashboard')

            with h.li:
                with h.a(class_="liked-comments").action(self.show_most_liked_comments):
                    h << _(u'Most Liked Comments')
                    with h.span(class_='download'):
                        h << _("Download")

            board_export_url, board_export_date = None, None
            if self.configuration['administration']['board_export']:
                board_export_url, board_export_date = self.last_board_export()

            if board_export_url:
                with h.li:
                    with h.a(class_='last-export', href=board_export_url):
                        h << _(u'Last Export: %s') % format_date(board_export_date)
                        with h.span(class_='download'):
                            h << _("Download")

            stats_url = self.configuration['administration']['stats_url']
            if stats_url:
                with h.li:
                    with h.a(
                        class_='desktop-visits', href='#',
                        onclick=('window.open("%s"); '
                                 'return false') % stats_url):
                        h << _("Visits on the Desktop Platform")

        h << h.h2(_(u'Directories'))
        with h.ul:
            with h.li:
                with h.a(class_="user-admin").action(self.show_users):
                    h << _(u'Users')

            with h.li:
                with h.a(class_="fi-admin").action(self.show_fis):
                    h << _(u'Facilitators')

            with h.li:
                with h.a(class_="di-admin").action(self.show_dis):
                    h << _(u'Developers')

        h << h.h2(_(u'Communication / Site activities'))
        with h.ul:
            with h.li:
                with h.a(class_='points-admin').action(self.show_points):
                    h << _(u'Points')

            with h.li:
                with h.a(class_='challenges-admin').action(self.show_challenges):
                    h << _(u'Challenges')

            with h.li:
                with h.a(class_='articles-admin').action(self.show_articles):
                    h << _(u'Articles')

            with h.li:
                with h.a(class_='polls-admin').action(self.show_polls):
                    h << _(u'Polls')

    return h.root
