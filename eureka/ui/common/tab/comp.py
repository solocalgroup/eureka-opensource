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
from eureka.ui.common.menu import Menu


class TabContainer(object):
    def __init__(self, tabs=None, default_tab=0):
        super(TabContainer, self).__init__()
        self.tabs = tabs or []
        self.content = component.Component(Empty(), model='tab_bar')

        self.menu = component.Component(Menu([e[0] for e in self.tabs]))
        self.menu.on_answer(self.select_tab)

        self.select_tab(default_tab)

    def add_tab(self, name, content):
        index = len(self.tabs)
        self.tabs.append((name, content))
        return index

    def find_tab(self, name):
        for idx, tab in enumerate(self.tabs):
            if name == tab[0]:
                return idx

    @property
    def selected_tab(self):
        return self.menu().selected()

    @selected_tab.setter
    def selected_tab(self, value):
        self.select_tab(value)

    def select_tab(self, index):
        if not self.tabs:
            return

        content = self.tabs[index][1]
        self.menu().selected(index)
        model = None
        if isinstance(content, component.Component):
            model = content.model
        self.content.becomes(content, model)


class Empty(object):
    pass
