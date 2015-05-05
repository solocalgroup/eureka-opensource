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

from sqlalchemy import desc

from nagare import var, security, component
from nagare.database import session
from nagare.i18n import _

from eureka.domain.models import ImprovementData, ImprovementState
from eureka.infrastructure import event_management
from eureka.ui.desktop.pager import Pager
from eureka.ui.common.menu import Menu


class SuggestionsPager(Pager):
    def __init__(self, parent, batch_size=10):
        super(SuggestionsPager, self).__init__(self._query, batch_size)
        event_management._register_listener(parent, self)

        self.selected_tab = var.Var('all')

        self.menu_items = [(_(u'All suggestions'), 'all', _(u'Show all suggestions'), '', None),
                           (_(u'Processed and deployed'), 'treated', _(u'Show processed and deployed suggestions'), '', None),
                           (_(u'In progress'), 'running', _(u'Show suggestions in progress'), '', None),
                           (_(u'Rejected'), 'rejected', _(u'Show the rejected suggestions'), '', None),
                           ]

        self.menu = component.Component(Menu(self.menu_items),
                                        model='tab_renderer')
        self.menu.on_answer(self.select_tab)
        self.select_tab(0)

    def select_tab(self, value):
        self.change_tab(self.menu_items[value][1])
        self.menu().selected(value)

    def change_tab(self, tab):
        self.selected_tab(tab)
        self.goto_page(1)

    def _query(self):
        query = session.query(ImprovementData.id).order_by(desc(ImprovementData.id))

        if not security.has_permissions('view_masked_suggestions', self):
            query = query.filter(ImprovementData.visible == True)

        # filter by state according to the selected tab
        if self.selected_tab() == 'running':
            query = query.filter(ImprovementData.state == ImprovementState.RUNNING)
        elif self.selected_tab() == 'treated':
            query = query.filter(ImprovementData.state == ImprovementState.TREATED)
        elif self.selected_tab() == 'rejected':
            query = query.filter(ImprovementData.state == ImprovementState.REJECTED)

        return query

    @property
    def suggestions(self):
        from .comp import Suggestion
        return [component.Component(Suggestion(id)) for id in self.get_pager_elements()]

    def submit_suggestion(self):
        event_management._emit_signal(self, "SUBMIT_SUGGESTION")

    def with_login(self, action):
        event_management._emit_signal(self, 'WITH_LOGIN', action)
