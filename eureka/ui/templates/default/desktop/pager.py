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

from nagare import presentation, ajax
from nagare.i18n import _

from eureka.ui.desktop.pager import (Pager, InfinitePager,
                                     InfinitePagerNextElement, FilterMenu,
                                     PagerMenu)


@presentation.render_for(InfinitePager)
def render(self, h, comp, *args):
    h << self.pager
    h << self.next.render(h.AsyncRenderer())

    return h.root


@presentation.render_for(InfinitePager, model='filtered')
def render(self, h, comp, *args):
    h << self.pager.render(h, model='filtered')
    return h.root


@presentation.render_for(InfinitePager, model='xls_export')
def render(self, h, comp, *args):
    h << self.pager.render(h, model='xls_export')
    return h.root


@presentation.render_for(InfinitePager, model='batch_size')
def render(self, h, comp, *args):
    h << self.pager.render(h, model='batch_size')
    return h.root


@presentation.render_for(InfinitePager, model='count')
def render(self, h, comp, *args):
    h << self.pager.render(h, model='count')
    return h.root


@presentation.render_for(InfinitePager, model='detail')
def render(self, h, comp, *args):
    h << self.pager.render(h, model='detail')
    return h.root


@presentation.render_for(InfinitePager, model='detail_edit')
def render(self, h, comp, *args):
    h << self.pager.render(h, model='detail_edit')
    return h.root


@presentation.render_for(InfinitePager, model='first-page')
def render(self, h, comp, *args):
    with h.div(id='infinite-pager'):
        h << self.pager
        h << self.next.render(h.AsyncRenderer())

    return h.root


@presentation.render_for(InfinitePager, model='list')
def render(self, h, comp, *args):
    with h.div:
        h << self.pager
        h << self.next.render(h.AsyncRenderer())
    return h.root


@presentation.render_for(InfinitePagerNextElement)
def render(self, h, comp, *args):
    if self.infinite_pager.has_next():
        h << h.a('NEXT', class_='infinite-batch')

        action = h.a.action(lambda: self.infinite_pager.display_next_page(comp, 'list'))
        js = r"""YUI().use('dom-core', 'node', function (Y) {
            var ongoing = false;
            function fillToBelowViewport() {
                var next = Y.one('.infinite-batch')
                if (! ongoing && next){
                    ongoing = true;
                    var node = next.getDOMNode();
                    if (Y.DOM.inViewportRegion(node)) {
                        %s
                    }
                    ongoing = false;
                }
            }
            Y.on('scroll', fillToBelowViewport);
        });""" % action.get('onclick').replace('nagare_replaceNode', 'nagare_appendChild')

        h << h.script(js)

    return h.root


@presentation.render_for(Pager, model='batch')
def render(self, h, *args):
    if self.has_previous() or self.has_next():
        with h.div(class_="batch"):

            if self.count() % self.batch_size:
                total_page = max((self.count() / self.batch_size) + 1, 1)
            else:
                total_page = max((self.count() / self.batch_size), 1)

            first_page = 1
            last_page = total_page

            page_num = (self.start / self.batch_size) + 1

            leftmost_page = max(first_page, (page_num - self.radius))
            rightmost_page = min(last_page, (page_num + self.radius))

            if self.has_previous():
                h << h.a('<< ', _(u'Previous'), class_="back").action(self.previous_page)
            else:
                h << h.a('', class_="back")

            if self.has_next():
                h << h.a(_(u'Next'), " >>", class_="next").action(self.next_page)
            else:
                h << h.a('', class_="next")

            with h.div(class_="pages"):
                page_list = range(leftmost_page, rightmost_page + 1)

                if leftmost_page != first_page:
                    if page_num == first_page:
                        h << h.a(first_page, class_='current')
                    else:
                        h << h.a(first_page).action(lambda:
                                                    self.goto_page(first_page))

                if leftmost_page > first_page + 1:
                    h << h.a("...")

                for ind in page_list:
                    if ind == page_num:
                        h << h.a(ind, class_='current')
                    else:
                        h << h.a(ind).action(lambda p=ind: self.goto_page(p))

                if rightmost_page < last_page - 1:
                    h << h.a("...")

                if rightmost_page != last_page:
                    if page_num == last_page:
                        h << h.a(last_page, class_='current')
                    else:
                        h << h.a(last_page).action(lambda:
                                                   self.goto_page(last_page))

    return h.root


@presentation.render_for(FilterMenu)
def render_filter_menu(self, h, comp, *args):
    with h.ul(id='menu_popin', class_=self.filter_type):

        # First item reset previous filter
        action_1 = ajax.Update(action=lambda: self.cb_('reset'))
        action_2 = ajax.Update(action=self.reset_pager,
                               component_to_update='infinite-pager',
                               render=self.create_pager_comp.render)
        action_3 = ajax.Update(action=lambda: None,
                               component_to_update='pager-counter',
                               render=lambda h: self.pager.render(h, model='count'))
        h << h.li(h.a(_(u'All')).action(ajax.Updates(action_2, action_1, action_3)))

        for filter_ in self.filters:
            action_1 = ajax.Update(action=lambda filter_=filter_: self.cb_(filter_))
            action_2 = ajax.Update(action=self.reset_pager,
                                   component_to_update='infinite-pager',
                                   render=self.create_pager_comp.render)
            action_3 = ajax.Update(action=lambda: None,
                                   component_to_update='pager-counter',
                                   render=lambda h: self.pager.render(h, model='count'))
            h << h.li(h.a(filter_.title).action(ajax.Updates(action_2, action_1, action_3)))

    action = h.a.action(self.cb_)
    js = r"""manage_menu_click(function(){%s})""" % action.get('onclick')

    h << h.script(js)

    return h.root


@presentation.render_for(PagerMenu)
def render_ideas_pager_menu(self, h, comp, *args):
    with h.div(class_='dropdown'):
        h << h.a(self.label).action(self.toggle_menu)
        if self.menu():
            h << self.menu

    return h.root
