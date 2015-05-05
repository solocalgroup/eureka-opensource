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

from nagare import component, security

from eureka.domain.models import UserData
from eureka.domain.repositories import UserRepository
from eureka.infrastructure import event_management
from eureka.infrastructure.tools import is_string
from eureka.ui.desktop.idea import IdeaPager
from eureka.ui.desktop.pager import InfinitePager


class IdeaBasket(object):
    def __init__(self, parent, user, query, label="All Ideas", batch_size=10):
        self.parent = parent
        # FIXME: WTF?
        event_management._register_listener(self, self)

        self.user_uid = user if is_string(user) else user.uid
        self._query = query

        self.pager = component.Component(None)
        self.state_id = None
        self.show_proxy_ideas = False

    @property
    def user(self):
        return UserRepository().get_by_uid(self.user_uid)

    def hide_ideas(self):
        self.state_id = None
        self.pager.becomes(None)

    def show_ideas(self, user_uid, state_id, query_factory):
        self.show_proxy_ideas = False
        self.state_id = state_id
        query = query_factory(user_uid, state_id)
        pager = IdeaPager(self.parent, query)
        pager = InfinitePager(component.Component(pager, model='ideas-list'))

        self.pager.becomes(pager, model='list')

    def get_sorted_ideas(self, batch=True):
        return [(state, count) for state, count in self._query()]

    def toggle_proxy_ideas(self, user_uid):
        self.state_id = None
        self.show_proxy_ideas = not self.show_proxy_ideas
        if self.show_proxy_ideas:
            query = lambda uid=user_uid: UserData.get_proxy_ideas(uid)
            pager = IdeaPager(self.parent, query)
            pager = InfinitePager(
                component.Component(pager, model='ideas-list'))

            self.pager.becomes(pager, model='list')
