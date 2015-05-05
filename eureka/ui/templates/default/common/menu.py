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
from eureka.ui.common.menu import Menu


@presentation.render_for(Menu, model='tab_bar')
def render_tab_container_tab_bar(self, h, comp, *args):
    """
    Render default html for Menu navigation in TabContainer context.

    Args:
        h: Nagare html renderer
        comp: Nagare Component to render
        *args: unused arguments needed for Nagare
    """
    with h.ul(class_='tab-bar'):
        for index, entry in enumerate(self.items):
            if entry:  # support None names -> no tab rendered for this item
                with h.li(class_='tab' + (' active' if self.selected() == index else '')):
                    with h.span:
                        h << h.a(entry).action(
                            lambda index=index: self.display(index, comp))
    return h.root


@presentation.render_for(Menu, model='list')
def render_tab_container_tab_bar(self, h, comp, *args):
    """
    Render default html for Menu navigation in TabContainer context.

    Args:
        h: Nagare html renderer
        comp: Nagare Component to render
        *args: unused arguments needed for Nagare
    """
    with h.ul:
        for index, (label, title, href, callback) in enumerate(self.items):
            if label:  # support None names -> no tab rendered for this item
                with h.li:
                    if self.selected() == index:
                        h << {'class_': 'current'}

                    kw = {}
                    if href:
                        kw['href'] = href
                    if title:
                        kw['title'] = title

                    a = h.a(label, **kw)
                    if callback:
                        a = a.action(
                            lambda index=index: self.display(index, comp))
                    h << a
    return h.root


@presentation.render_for(Menu, model='links')
def render_tab_container_tab_bar(self, h, comp, *args):
    """
    Render default html for Menu navigation in TabContainer context.

    Args:
        h: Nagare html renderer
        comp: Nagare Component to render
        *args: unused arguments needed for Nagare
    """
    for index, (label, title, href, callback) in enumerate(self.items):
        kw = {}
        if href:
            kw['href'] = href
        if title:
            kw['title'] = title
        a = h.a(label, **kw)
        if callback:
            a = a.action(lambda index=index: self.display(index, comp))
        h << a
    return h.root


@presentation.render_for(Menu)
def render(self, h, comp, *args):
    """
    Render default html for Menu navigation component. It uses styles
    from Twitter bootstrap.

    Args:
        h: Nagare html renderer
        comp: Nagare Component to render
        *args: unused arguments needed for Nagare
    """
    with h.ul(class_='nav nav-list'):
        for index, entry in enumerate(self.items):
            if entry:
                if self.selected() == index:
                    li = h.li(class_='active')
                else:
                    li = h.li

                with li:
                    h << h.a(entry, title=entry).action(
                        lambda index=index: self.display(index, comp)
                    )
            else:
                h << h.li(class_='divider')

    return h.root


@presentation.render_for(Menu, model='form')
def render_form(self, h, comp, *args):
    """
    Render html for Menu navigation component actions are submit buttons not
    links. It uses styles from Twitter boostrap. This html fragment as to be
    wrapped into an html form.

    Args:
        h: Nagare html renderer
        comp: Nagare Component to render
        *args: unused arguments needed for Nagare
    """
    with h.ul(class_='nav nav-list'):
        for index, entry in enumerate(self.items):
            if entry:
                if self.selected() == index:
                    li = h.li(class_='active')
                else:
                    li = h.li

                with li:
                    h << h.input(value=entry, title=entry,
                                 type='submit', class_='btn').action(
                        lambda index=index: self.display(
                            index, comp)
                    )
            else:
                h << h.li(class_='divider')

    return h.root


@presentation.render_for(Menu, model='slider')
def render(self, h, comp, *args):
    with h.ul(class_='nav'):
        for index, entry in enumerate(self.items):
            if self.selected() == index:
                li = h.li(class_='current')
            else:
                li = h.li
            with li:
                h << h.a('').action(
                    lambda index=index: self.display(index, comp)
                )
    return h.root


@presentation.render_for(Menu, model='challenges')
def render(self, h, comp, *args):
    for index, entry in enumerate(self.items):
        with h.a(entry).action(lambda index=index: self.display(index, comp)):
            if self.selected() == index:
                h << {'class_': 'current'}

    return h.root


@presentation.render_for(Menu, model='tab_renderer')
def render(self, h, comp, *args):
    with h.ul(class_="tab-bar"):
        for index, (label, name, title, href, callback) in enumerate(
                self.get_items()):
            if self.selected() == index:
                li = h.li(class_='current')
            else:
                li = h.li

            with li:
                h << h.a(label, href=href, title=title or label).action(
                    callback if callback else lambda index=index: self.display(
                        index, comp))
    return h.root
