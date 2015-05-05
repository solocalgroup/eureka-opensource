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

from nagare import presentation
from nagare.i18n import _

from eureka.ui.desktop.search import SearchBlock, SearchMenu


@presentation.render_for(SearchBlock)
def render(self, h, comp, *args):
    if self.show_form():
        h << comp.render(h.SyncRenderer(), model='with_form')
    else:
        h << h.a(h.i(class_='icon-search'), class_='icon-search-link').action(lambda: self.show_form(True))

    return h.root


@presentation.render_for(SearchMenu)
def render(self, h, comp, *args):
    with h.div(class_='filter'):
        for label, value in self.items:
            with h.label:
                if value == self.selected():
                    class_ = 'icon-checkbox-selected'
                else:
                    class_ = 'icon-checkbox'
                h << h.a(h.i(class_=class_)).action(lambda value=value: comp.answer(value))
                h << label

    return h.root


@presentation.render_for(SearchBlock, model='with_form')
def render(self, h, comp, *args):

    with h.form:
        if self.search_pattern():
            on_focus = {}
            on_click = {}
            default_value = self.search_pattern()
            default_class = None
        else:
            on_focus = {'onfocus': "this.value='';this.className='text';this.id=''"}
            on_click = {'onclick': "var element = document.getElementById('search'); if (element) element.value='';"}
            default_value = _(u'Search')
            default_class = "defaultsearch"

        h << h.div(h.input(class_='icon-search', type='submit', value=''), class_='icon-search-link')

        if self.form_opened():
            class_search_box = 'search-box open'
        else:
            class_search_box = 'search-box'

        with h.div(class_=class_search_box):
            h << h.input(id="search",
                         type="text",
                         class_='text ' + (default_class or ''),
                         name="search",
                         value=default_value,
                         **on_focus).action(self.search_pattern)

            h << self.options.render(h.AsyncRenderer())

            # IE bugfix: IE don't pass the submit action if we press enter in the text field,
            # so it is passed as a hidden input, but handled as a submit button on the server-side
            search_action_name = h.input(type='submit').action(self.do_search).get('name')

            h << h.input(type='hidden', name=search_action_name)

        h << h.input(type='submit',
                     name='commit',
                     class_="submit",
                     value="",
                     **on_click)

        if not self.form_opened():
            js = r"""YAHOO.util.Event.onDOMReady(function(){
                var attributes = {
                    left: { to: 350}
                };

                var icon_search = YAHOO.util.Dom.getElementsByClassName('icon-search-link')[0];
                var search_box = YAHOO.util.Dom.getElementsByClassName('search-box')[0];
                var scroll = new YAHOO.util.Anim(search_box, attributes);

                scroll.animate();
            });"""

            h << h.script(js)
            self.form_opened(True)

    return h.root
