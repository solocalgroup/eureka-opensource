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

import operator
from datetime import datetime

from webob.exc import HTTPNotFound
from sqlalchemy.sql.expression import desc, case
from nagare import component, security
from nagare.i18n import _, _L
from eureka.domain.services import get_workflow
from eureka.domain.models import ReadIdeaData, StateData
from eureka.domain.repositories import (ChallengeRepository, DomainRepository,
                                        IdeaRepository, IdeaData)
from eureka.infrastructure import event_management
from eureka.infrastructure.workflow.workflow import _permission
from eureka.infrastructure.security import get_current_user
from eureka.infrastructure.content_types import excel_response
from eureka.ui.common.box import PagerBox
from eureka.ui.common.menu import Menu
from eureka.ui.desktop.pager import Pager, FilterMenu, PagerMenu
from .comp import Idea
from .editor import IdeaUpdater
from .filters import (IdeaChallengeFilter, IdeaDateFilter, IdeaStateFilter,
                      IdeaNoFilter, IdeaDomainFilter)
from .excel import export
from eureka.infrastructure.tools import is_integer
from eureka.ui.desktop.challenge import Challenge


def domain_filters(domains):
    filters = [IdeaDomainFilter('domain_%d' % domain.id, domain.i18n_label, domain.id)
               for domain in domains]
    return filters


def challenge_filters(challenges):
    """Returns a list of challenge filters for the specified challenges"""
    filters = [IdeaChallengeFilter('challenge_%d' % challenge.id, '#%d %s' % (challenge.id, challenge.title[:30]), challenge.id)
               for challenge in challenges]
    filters.append(IdeaChallengeFilter('challenge_none', _(u'Off challenge'), None))
    return filters


def date_filters(date_field):
    """
    Returns a list of IdeaDateFilter on the given date_field for all period
    types
    """
    return [
        IdeaDateFilter('last_day', _(u"Last 24 h"), date_field, 1),
        IdeaDateFilter('last_week', _(u"Last week"), date_field, 7),
        IdeaDateFilter('last_month', _(u"Last month"), date_field, 30)
    ]


def state_filters():
    """
    Returns a list of IdeaStateFilter for each step
    """
    workflow = get_workflow()
    return [
        IdeaStateFilter('SUBMITTED_STEP', _(u'SUBMITTED_STEP'), workflow.get_submitted_states()),
        IdeaStateFilter('STUDY_STEP', _(u'STUDY_STEP'), workflow.get_study_states()),
        IdeaStateFilter('SUGGESTED_STEP', _(u'SUGGESTED_STEP'), workflow.get_approved_states()),
        IdeaStateFilter('SELECTED_STEP', _(u'SELECTED_STEP'), workflow.get_selected_states()),
        IdeaStateFilter('PROJECT_STEP', _(u'PROJECT_STEP'), workflow.get_project_states()),
        IdeaStateFilter('PROTOTYPE_STEP', _(u'PROTOTYPE_STEP'), workflow.get_prototype_states()),
        IdeaStateFilter('EXTENDED_STEP', _(u'EXTENDED_STEP'), workflow.get_extended_states()),
        IdeaStateFilter('refused', _(u"Non-retained"), workflow.get_refused_states()),
        IdeaStateFilter('progressing_ideas', _(u"Ideas in progress"), workflow.get_progressing_ideas_states()),
    ]


def launched_ideas_step_filters():
    workflow = get_workflow()
    return [
        IdeaStateFilter('PROJECT_STEP', _(u'PROJECT_STEP'), workflow.get_project_states()),
        IdeaStateFilter('PROTOTYPE_STEP', _(u'PROTOTYPE_STEP'), workflow.get_prototype_states()),
        IdeaStateFilter('EXTENDED_STEP', _(u'EXTENDED_STEP'), workflow.get_extended_states()),
    ]


def sort_by_state(q, states_order):
    """Utility function to sort ideas by state, in the specified order"""
    sorted_states_id = [StateData.get_by(label=state) for state in states_order]
    sorted_states_id = [a.id for a in sorted_states_id if a]
    state_rank_mapping = [(state, rank) for rank, state in enumerate(sorted_states_id)]
    q = q.add_column(case(value=StateData.id, whens=state_rank_mapping).label('states_rank'))
    q = q.order_by('states_rank')
    return q


# FIXME: Extract the transform/filters/sorts from the IdeaPager to an IdeaPerspective class/view (in a new module?)
# FIXME: clean this class up. Many things are no more used
class IdeaPager(Pager):
    def __init__(self, parent, query, batch_size=10, container=None):
        super(IdeaPager, self).__init__(query, batch_size)
        self.container = container
        if parent:
            self.bind_parent(parent)

        self.content = component.Component(None)
        self.challenge_excerpt = component.Component(None)
        self.display_date = 'publication_date'
        self.filters = self.get_default_filters()
        self.filters_by_name = dict((f.name, f) for f in self.filters)
        self.sort_criteria = self.get_default_sort_criteria()

        self._filter_state = None
        self._filter_period = None
        self._filter_challenge = None
        self._filter_domain = None
        self._order = None
        self._transform = None

        self.menu_items = [
            (_(u"Last published"), 'last_published', None, '', self.last_published),
            (_(u"Progressing"), 'progressing_ideas', None, '', self.progressing_ideas),
            (_(u"Most viewed"), 'most_viewed', None, '', self.most_viewed),
            (_(u"Launched ideas"), 'launched_ideas', None, '', self.launched_ideas),
        ]

        self.menu = component.Component(Menu(self.menu_items),
                                        model='tab_renderer')
        self.menu.on_answer(self.select_tab)
        self.select_tab(0)

    def select_tab(self, value):
        self.menu().selected(value)

    def bind_parent(self, parent):
        event_management._register_listener(parent, self)

    def get_default_filters(self):
        return date_filters('publication_date') + state_filters() + challenge_filters(self.get_challenges()) + domain_filters(self.get_domains())

    def get_default_sort_criteria(self):
        return ['publication_date', 'total_comments', 'total_votes']

    def set_batch_size(self, v):
        self.batch_size = int(v)
        self.first_page()

    def reset_filter(self):
        self._filter_state = None
        self._filter_period = None
        self._filter_challenge = None
        self._filter_domain = None
        self.first_page()

    def change_filter_state(self, filter):
        self._filter_state = filter
        self.first_page()

    def change_filter_period(self, filter):
        self._filter_period = filter
        self.first_page()

    def change_filter_challenge(self, filter):
        self._filter_challenge = filter
        filter = self.filters_by_name.get(filter)

        if filter and filter.challenge_id:
            self.challenge_excerpt.becomes(Challenge(self, filter.challenge_id), model='short_excerpt')
        else:
            self.challenge_excerpt.becomes(None)
        self.first_page()

    def change_filter_domain(self, filter):
        self._filter_domain = filter
        self.first_page()

    def change_order(self, order):
        self._order = order

    def last_published(self):
        self.change_transform('last_published')
        self.change_order('publication_date_desc')
        self.display_date = 'publication_date'
        self.select_tab(0)

    def progressing_ideas(self):
        filters = reduce(operator.concat,
                         [date_filters('recommendation_date'),
                          state_filters()])
        sort_criteria = ['recommendation_date', 'total_comments', 'total_votes']

        self.change_transform('progressing_ideas', filters, sort_criteria)
        self.change_order('recommendation_date_desc')
        self.change_filter_state('')

        self.display_date = 'recommendation_date'
        self.select_tab(1)

    def most_viewed(self):
        self.change_transform('most_viewed')
        self.change_order('most_viewed')
        if security.has_permissions('state_filter', self):
            self.change_filter_state('STUDY_STEP')
        self.select_tab(2)

    def launched_ideas(self):
        filters = reduce(operator.concat,
                         [date_filters('publication_date'),
                          launched_ideas_step_filters()])
        self.change_transform('launched_ideas', filters)
        self.change_order('publication_date_desc')
        self.select_tab(3)

    def all_challenges(self):
        # remove the challenge_none filter
        filters = [filter for filter in self.get_default_filters() if filter.name != 'challenge_none']
        self.change_transform('challenge', filters)
        self.change_order('states')

    def specific_challenge(self):
        # remove the challenge filters
        filters = [filter for filter in self.get_default_filters() if not isinstance(filter, IdeaChallengeFilter)]
        self.change_transform('challenge', filters)
        self.change_order('states')

    def change_transform(self, transform, filters=None, sort_criteria=None):
        self.filters = filters if filters is not None else self.get_default_filters()
        self.filters_by_name = dict((f.name, f) for f in self.filters)

        self.sort_criteria = sort_criteria if sort_criteria is not None else self.get_default_sort_criteria()

        self.display_date = 'publication_date'

        self._transform = transform
        self._filter_state = None
        self._filter_period = None
        self._order = None

    def apply_query_transform(self, q):
        workflow = get_workflow()
        # only published states appear here
        IDEA_STATES_ORDER = (workflow.WFStates.EXTENDED_STATE,
                             workflow.WFStates.PROTOTYPE_STATE,
                             workflow.WFStates.PROJECT_STATE,
                             workflow.WFStates.SELECTED_STATE,
                             workflow.WFStates.DI_APPROVED_STATE,
                             workflow.WFStates.RETURNED_BY_DI_STATE,
                             workflow.WFStates.DI_APPRAISAL_STATE,
                             workflow.WFStates.PROTOTYPE_REFUSED_STATE,
                             workflow.WFStates.PROJECT_REFUSED_STATE,
                             workflow.WFStates.SELECT_REFUSED_STATE,
                             workflow.WFStates.APPROVAL_REFUSED_STATE,
                             workflow.WFStates.DI_REFUSED_STATE)

        IDEA_ORDER = {
            'publication_date': lambda q: q.order_by('publication_date'),
            'publication_date_desc': lambda q: q.order_by(desc('publication_date')),
            'recommendation_date': lambda q: q.order_by('recommendation_date'),
            'recommendation_date_desc': lambda q: q.order_by(desc('recommendation_date')),
            'total_comments': lambda q: q.order_by('total_comments'),
            'total_comments_desc': lambda q: q.order_by(desc('total_comments')),
            'total_votes': lambda q: q.order_by('total_votes'),
            'total_votes_desc': lambda q: q.order_by(desc('total_votes')),
            'most_viewed': lambda q: q.order_by(desc('total_readers')),
            'states': lambda q: sort_by_state(q, IDEA_STATES_ORDER),
        }

        IDEA_TRANSFORM = {
            'most_popular': lambda q: q.order_by(desc('popularity')),
            'dsig': lambda q: q.filter(StateData.label.in_(workflow.get_selected_states())),
            'progressing_ideas': lambda q: q.filter(StateData.label.in_(workflow.get_progressing_ideas_states())),
            'launched_ideas': lambda q: q.filter(StateData.label.in_(workflow.get_launched_ideas_states())),
        }

        q = IDEA_TRANSFORM.get(self._transform, lambda x: x)(q)
        q = self.filters_by_name.get(self._filter_state, IdeaNoFilter()).apply(q)
        q = self.filters_by_name.get(self._filter_challenge, IdeaNoFilter()).apply(q)
        q = self.filters_by_name.get(self._filter_period, IdeaNoFilter()).apply(q)
        q = self.filters_by_name.get(self._filter_domain, IdeaNoFilter()).apply(q)
        q = IDEA_ORDER.get(self._order, lambda x: x)(q)
        return q

    def get_domains(self):
        """ Return all domains """
        return DomainRepository().get_all()

    def get_challenges(self):
        return ChallengeRepository().get_all()

    def goto(self, idea_id, mode=u"view"):
        assert is_integer(idea_id)

        self.idea_i = None
        self.content.becomes(None)

        idea = IdeaRepository().get_by_id(idea_id)
        if not idea:
            raise HTTPNotFound()

        i = self._create_idea(idea)

        # Show the editor when the current user is the creator and the
        # idea state is DRAFT or AUTHOR_NORMALIZATION
        workflow = get_workflow()
        edit_state = i.i.wf_context.state.label in (workflow.WFStates.INITIAL_STATE,
                                                    workflow.WFStates.DRAFT_STATE,
                                                    workflow.WFStates.AUTHOR_NORMALIZE_STATE,
                                                    workflow.WFStates.RETURNED_BY_DI_STATE)

        # FIXME: is this a good idea to force the mode like this?!
        current_user = get_current_user()
        if current_user and (current_user in i.i.authors) and edit_state:
            mode = u"edit"

        if mode == u"edit":
            self.content.becomes(IdeaUpdater(i), model='form')
        else:
            self.content.becomes(i, model='detail')

        if current_user:
            # FIXME: WTF! Remove this!
            # Note: we do not use the association proxy and even no
            #       entity to avoid the index crawling extension to be
            #       notified of a change: we do not want to update the
            #       document each time it is viewed!
            ReadIdeaData(user_uid=current_user.uid, idea_id=i.id, timestamp=datetime.now())
            idea.readers_updated()

        event_management._emit_signal(self, "VIEW_IDEA", mode=mode)

    def get_query(self):
        q = super(IdeaPager, self).get_query()
        q = self.apply_query_transform(q)
        return q

    def _create_idea(self, idea):
        idea = Idea(self, idea)
        idea.display_date = self.display_date
        return idea

    def get_ideas(self):
        q = self.get_query()
        if not q:
            return []

        q = q.offset(self.start).limit(self.batch_size)

        return [self._create_idea(i) for i in q]

    def get_ideas_comp(self):
        return [component.Component(i) for i in self.get_ideas()]

    def get_next_page_ideas(self):
        q = self.get_query()
        if not q:
            return []

        q = q.offset(self.start + self.batch_size + 1).limit(self.batch_size + self.batch_size + 1)

        return [self._create_idea(i) for i in q]

    def export_xls(self, filename_prefix='export'):
        idea_ids = [i.id for i in self.get_query()]
        if idea_ids:
            current_user = get_current_user()
            first_idea = IdeaData.query.filter_by(id=idea_ids[0]).one()
            permission = _permission(current_user, first_idea)
        else:
            permission = None
        content, filename = export(idea_ids, permission, filename_prefix)
        raise excel_response(content, filename)

    def with_login(self, action):
        event_management._emit_signal(self, "WITH_LOGIN", action)


class IdeasFilters(object):
    def __init__(self, pager, show_challenge=True):
        pager = pager().pager
        filters_by_name = dict(map(lambda f: (f.name, f), pager().filters))

        # state names
        state_names = ['SUGGESTED_STEP', 'SELECTED_STEP',
                       'PROJECT_STEP', 'PROTOTYPE_STEP', 'EXTENDED_STEP',
                       'refused']

        if pager()._transform != 'progressing_ideas':
            state_names = ['STUDY_STEP', ] + state_names

        if pager()._transform == 'user':
            state_names.insert(0, 'SUBMITTED_STEP')

        self.show_challenge = show_challenge

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

        # The pager can already have a domain value associated
        if pager()._filter_domain:
            filter_ = [f for f in filter_domain if f.name == pager()._filter_domain]
            if filter_:
                self.menu_domain().label = filter_[0].title

        self.menu_state().attach_linked_menu([self.menu_challenge(), self.menu_period(), self.menu_domain()])
        self.menu_challenge().attach_linked_menu([self.menu_state(), self.menu_period(), self.menu_domain()])
        self.menu_period().attach_linked_menu([self.menu_challenge(), self.menu_state(), self.menu_domain()])
        self.menu_domain().attach_linked_menu([self.menu_challenge(), self.menu_period(), self.menu_state()])


class IdeaPagerBox(PagerBox):

    def __init__(self, pager, model=None, title=None, ok_button=None,
                 css_class=None, menu_items=None):
        super(IdeaPagerBox, self).__init__(pager, model, title, ok_button,
                                           css_class, menu_items)

        self.ordered = component.Component(pager.pager, model='ordered')

        self.filtered = component.Component(IdeasFilters(self.content))

        self.excel_exporter = component.Component(pager.pager, 'xls_export')
        self.batch_size_changer = component.Component(pager.pager, 'batch_size')
        self.idea_counter = component.Component(pager.pager, 'count')
