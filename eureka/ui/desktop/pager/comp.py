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

from nagare import component
from eureka.infrastructure.cache import cached


# FIXME: move to the common package / merge with the existing pager (or drop it if possible)
class Pager(object):
    """ Generic Pager """

    def __init__(self, query, batch_size):
        self._query = query
        self.start = 0
        self.batch_size = batch_size
        self.radius = 3

    def first_page(self):
        self.start = 0
        return self

    def has_next(self):
        """ Return True if pager has next page """
        current_page = self.start / self.batch_size
        page_count = (self.count() - 1) // self.batch_size + 1
        return current_page < page_count - 1

    def next_page(self):
        """ Go to the next page """
        self.start += self.batch_size

    def has_previous(self):
        """ Return True if pager has previous page """
        return self.start != 0

    def previous_page(self):
        """ Go to the previous page """
        self.start -= self.batch_size

    def goto_page(self, page_num):
        """ Go to page page_num """
        self.start = (page_num - 1) * self.batch_size

    @cached
    def count(self):
        """ Return number of elements """
        query = self.get_query()
        return query.count() if query else 0

    def get_query(self):
        """ Return query """
        return self._query()

    def get_pager_elements(self):
        """
        Return elements of the current page

        In:
          - `wrapper` -- class used to wrap element
        Return:
          - a list of wrapped element
        """
        query = self.get_query().offset(self.start).limit(self.batch_size + 1)
        return list(query)


class InfinitePager(object):

    def __init__(self, pager):
        self.pager = pager
        self.next = component.Component(InfinitePagerNextElement(self))

    def display_next_page(self, comp, model):
        self.pager().next_page()
        comp.becomes(InfinitePager(self.pager), model=model)

    def has_next(self):
        return self.pager().has_next()

    def count(self):
        return self.pager().count()

    def goto(self, idea_id):
        return self.pager().goto(idea_id)


class InfinitePagerNextElement(object):

    def __init__(self, infinite_pager):
        self.infinite_pager = infinite_pager


class PagerMenu(object):
    def __init__(self, label, items, pager, action=None, linked_menu=[]):
        self.pager = pager
        self.default_label = label
        self.label = label
        self.items = items
        self.items.cb_ = self.toggle_menu
        self.menu = component.Component(None)
        self.linked_menu = linked_menu
        self.action = action

    def attach_linked_menu(self, linked_menu):
        self.linked_menu = linked_menu

    def has_next(self):
        return self.pager().has_next()

    def reset_label(self):
        self.label = self.default_label

    def toggle_menu(self, filter_=None):
        if self.menu() and not filter_:
            self.menu.becomes(None)
        elif self.menu() and filter_ == 'reset':
            self.menu.becomes(None)
            self.reset_label()
            self.action(None)
        elif self.menu() and filter_:
            self.menu.becomes(None)
            self.label = filter_.title
            self.action(filter_.name)
        else:
            for m in self.linked_menu:
                m.menu.becomes(None)

            self.menu.becomes(self.items)


class FilterMenu(object):
    def __init__(self, filters=None, filter_type='', pager=None):
        self.filters = filters
        self.filter_type = filter_type
        self.pager = pager
        self.cb_ = None

    @property
    def create_pager_comp(self):
        return component.Component(InfinitePager(self.pager), model='first-page')

    def reset_pager(self):
        self.pager().first_page()


class Filter(object):
    def __init__(self, name, title):
        self.name = name
        self.title = title
