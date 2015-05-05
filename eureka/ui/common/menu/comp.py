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

"""A nagare component used for navigation."""
from nagare import var


class Menu(object):
    """
    This a base class to handle navigation.

    Attributes:
        items: list of objects to handle
        selected: index of the selected object
    """
    def __init__(self, items, items_creator=None):
        """
        Initialize Menu navigation component.

        Args:
            items: a list of object
        """
        self.items = items
        self.items_creator = items_creator
        self.selected = var.Var(None)

    def get_items(self):
        if self.items_creator:
            return self.items_creator()
        else:
            return self.items

    def display(self, i, comp):
        """
        Callbacks that fire click event in navigation.
        """
        if i < 0 or i >= len(self.get_items()):
            raise ValueError('index must be between 1 and %d' %
                             len(self.get_items()))
        comp.answer(i)

    def change_label_entry(self, id, label):
        if not self.items_creator:
            items = []
            for item in self.items:
                if item[1] == id:
                    items.append((label, item[1], item[2], item[3], item[4]))
                else:
                    items.append(item)
            self.items = items

    def add_entry_before(self, item):
        self.items = [item] + self.get_items()

    def has_entry(self, id):
        item = [a for a in self.get_items() if a[1] == id]
        return item != []

    def remove_entry(self, id):
        if not self.items_creator:
            if self.selected():
                id_selected = self.get_items()[self.selected()][1]
            else:
                id_selected = None

            self.items = [a for a in self.get_items() if a[1] != id]
            if not self.items:
                self.selected(None)
            elif id_selected == id:
                self.selected(0)
            elif id_selected:
                self.select_by_id(id_selected)

    def select_by_id(self, id):
        index_entry = [index for index, entry in enumerate(self.get_items()) if entry[1] == id]
        if index_entry:
            self.selected(index_entry[0])
        else:
            raise ValueError('id %s not exist' % id)

    def select_by_index(self, index):
        items = self.get_items()
        if len(items) >= index:
            self.selected(index)
            return items[index][1]
        else:
            raise ValueError('index %s not exist' % index)
