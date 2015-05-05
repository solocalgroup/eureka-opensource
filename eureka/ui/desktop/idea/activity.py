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

from eureka.ui.desktop.pager.comp import InfinitePager

from nagare import security, component
from nagare.i18n import _L

from eureka.infrastructure.security import get_current_user
from eureka.domain.repositories import IdeaRepository
from .pager import IdeaPager
from eureka.ui.desktop.pager import PagerMenu, FilterMenu
from .filters import (IdeaChallengeFilter, IdeaDateFilter, IdeaStateFilter,
                      IdeaNoFilter, IdeaDomainFilter)


# FIXME: rename to activity feed or something like that
class IdeasActivityPager(object):
    def __init__(self, parent, batch_size=6):
        self.ideas = component.Component(IdeaPager(parent, self.get_ideas, batch_size, self), model='list')
        self.ideas_infinite_pager = component.Component(InfinitePager(self.ideas))
        self.menu = component.Component(IdeasActivityPagerMenu(self.ideas))

    def get_ideas(self):
        idea_repository = IdeaRepository()

        current_user = get_current_user()
        if not current_user:
            query = idea_repository.get_by_home_settings()
        else:
            query = idea_repository.get_by_home_settings(current_user.home_settings)

        query = query.order_by(None)  # remove the default ordering
        return idea_repository.sort_by_last_wf_comment_date(query)


class IdeasActivityPagerMenu(object):
    def __init__(self, pager):
        filters_by_name = dict(map(lambda f: (f.name, f), pager().filters))

        # state names
        state_names = ['SUGGESTED_STEP', 'SELECTED_STEP',
                       'PROJECT_STEP', 'PROTOTYPE_STEP', 'EXTENDED_STEP',
                       'refused']

        if pager()._transform != 'progressing_ideas':
            state_names = ['STUDY_STEP', ] + state_names

        if pager()._transform == 'user':
            state_names.insert(0, 'SUBMITTED_STEP')

        filter_state = [filters_by_name[name] for name in state_names]
        self.filter_menu_state = FilterMenu(filter_state, 'state', pager)

        period_names = ['last_day', 'last_week', 'last_month']
        filter_period = [filters_by_name[name] for name in period_names]
        self.filter_menu_period = FilterMenu(filter_period, 'period', pager)

        filter_domain = [filter for filter in pager().filters if isinstance(filter, IdeaDomainFilter)]
        self.filter_menu_domain = FilterMenu(filter_domain, 'domain', pager)
        filter_challenge = [filter for filter in pager().filters if isinstance(filter, IdeaChallengeFilter)]
        self.filter_menu_challenge = FilterMenu(filter_challenge, 'challenge', pager)

        self.menu_state = component.Component(PagerMenu(_L(u'state'), self.filter_menu_state, pager, pager().change_filter_state))
        self.menu_challenge = component.Component(PagerMenu(_L(u'challenge'), self.filter_menu_challenge, pager, pager().change_filter_challenge))
        self.menu_period = component.Component(PagerMenu(_L(u'period'), self.filter_menu_period, pager, pager().change_filter_period))
        self.menu_domain = component.Component(PagerMenu(_L(u'domain'), self.filter_menu_domain, pager, pager().change_filter_domain))

        self.menu_state().attach_linked_menu([self.menu_challenge(), self.menu_period(), self.menu_domain()])
        self.menu_challenge().attach_linked_menu([self.menu_state(), self.menu_period(), self.menu_domain()])
        self.menu_period().attach_linked_menu([self.menu_challenge(), self.menu_state(), self.menu_domain()])
        self.menu_domain().attach_linked_menu([self.menu_challenge(), self.menu_period(), self.menu_state()])
