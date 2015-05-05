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

from eureka.domain.models import UserData
from eureka.domain.queries import get_corporation_label, get_direction_label
from eureka.domain.repositories import (ChallengeRepository, DomainRepository,
                                        IdeaRepository, UserRepository)
from eureka.domain.services import get_workflow
from eureka.infrastructure import event_management
from eureka.infrastructure.content_types import download_content_response
from eureka.infrastructure.tools import group_as_dict, limit_string, percentage
from eureka.ui.common.box import PagerBox
from eureka.ui.common.charts import ColorChooser
from eureka.ui.common.yui2 import Calendar, ColumnDefinition, TableEnhancement
from eureka.ui.desktop.dashboard import Dashboard, IdeasOnAlert, IdeasProgress
from eureka.ui.desktop.idea import Idea, IdeaPager, IdeaPagerBox
from eureka.ui.desktop.user import UserPager
from nagare import component, presentation
from nagare.i18n import _, format_datetime


def render_dashboard_panel(h, comp, left_model, right_model):
    """Utility function that renders a dashboard panel"""
    with h.table(class_="panel"):
        with h.tr:
            with h.td(class_="left"):
                h << comp.render(h, model=left_model)
            with h.td(class_='right'):
                h << comp.render(h, model=right_model)


@presentation.render_for(Dashboard)
def render_dashboard(self, h, comp, *args):
    with h.div(class_='dashboardBox rounded'):
        # h << comp.render(h, model='available_colors') << h.br
        h << comp.render(h, model='tabs')
        h << comp.render(h, model='dashboard_items')
    return h.root


@presentation.render_for(Dashboard, model='tabs')
def render_tabs(self, h, comp, *args):
    h << self.menu
    return h.root


@presentation.render_for(Dashboard, model='available_colors')
def render_available_colors(self, h, *args):
    def download_image():
        image = ColorChooser([], [], 300, 1800).get_png()
        raise download_content_response(
            'image/png', image, 'dashboard_colors.png')

    with h.p:
        h << h.a('Available colors').action(download_image)

    return h.root


@presentation.render_for(Dashboard, model='dashboard_items')
def render_dashboard_items(self, h, comp, *args):
    active_tab = self.active_tab() or 'ideas'
    with h.ul(class_='dashboard-items'):
        for model in self.get_models_by_tab(active_tab):
            with h.li(class_='dashboard-item'):
                h << comp.render(h, model=model)
    return h.root


@presentation.render_for(Dashboard, model='2weeks_report')
def render_2weeks_report(self, h, *args):
    chart_width = self.configuration['chart']['chart_width']
    h << h.h1(_(u'Connections and ideas posted by day on the last 2 weeks'))
    h << h.img(alt='', class_='chart').action(
        lambda: self.get_2weeks_chart(chart_width, 200))
    return h.root


@presentation.render_for(Dashboard, model='2months_report')
def render_2months_report(self, h, *args):
    chart_width = self.configuration['chart']['chart_width']
    h << h.h1(_(u'Connections and ideas posted by week on the last 2 months'))
    h << h.img(alt='', class_='chart').action(
        lambda: self.get_2months_chart(chart_width, 200))
    return h.root


@presentation.render_for(Dashboard, model='domain_state')
def render_domain_state(self, h, *args):
    chart_width = self.configuration['chart']['chart_width']
    h << h.h1(_(u'Ideas shares by state and by domain'))
    h << h.img(alt='', class_='chart').action(
        lambda: self.get_ideas_count_by_domain_state_chart(chart_width, 450))
    return h.root


@presentation.render_for(Dashboard, model='active_users_by_entity')
def render_active_users_by_entity(self, h, *args):
    h << h.h1(_(u'Users by entity'))
    with h.table(class_='datatable'):
        with h.tr:
            h << h.th(_(u'Corporation'))
            h << h.th(_(u'Direction'))
            h << h.th(_(u'Users'))
            h << h.th(_(u'Total'))
            h << h.th(_(u'Ratio'))

        total_user = 0
        total_total = 0

        for elt in self.get_active_users_by_entity():
            total_user += elt[2]
            total_total += elt[3]
            with h.tr:
                h << h.td(get_corporation_label(elt[0]))
                h << h.td(get_direction_label(elt[1]))
                h << h.td(str(elt[2]))
                h << h.td(str(elt[3]))
                h << h.td("%.2f%%" % elt[4])

        with h.tr(class_="totals"):
            h << h.td(_(u"Totals"), colspan="2")
            h << h.td(str(total_user))
            h << h.td(str(total_total))
            if total_total:
                h << h.td("%.2f%%" % (float(total_user * 100) / total_total))
            else:
                h << h.td(' - ')

    return h.root


@presentation.render_for(Dashboard, model='votes_by_entity')
def render_votes_by_entity(self, h, *args):
    h << h.h1(_(u'Votes by entity'))
    with h.table(class_='datatable'):
        with h.tr:
            h << h.th(_(u'Corporation'))
            h << h.th(_(u'Direction'))
            h << h.th(_(u'Voters'))
            h << h.th(_(u'Votes'))
            h << h.th(_(u'Total'))
            h << h.th(_(u'Ratio'))

        total_voters = 0
        total_votes = 0
        total_total = 0

        for elt in self.get_votes_by_entity():
            total_voters += elt[2]
            total_votes += elt[4]
            total_total += elt[3]

            with h.tr:
                h << h.td(get_corporation_label(elt[0]))
                h << h.td(get_direction_label(elt[1]))
                h << h.td(str(elt[2]))
                h << h.td(str(elt[4]))
                h << h.td(str(elt[3]))
                h << h.td("%.2f%%" % elt[5])

        with h.tr(class_="totals"):
            h << h.td(_(u"Totals"), colspan="2")
            h << h.td(str(total_voters))
            h << h.td(str(total_votes))
            h << h.td(str(total_total))
            if total_total:
                h << h.td("%.2f%%" % (float(total_voters * 100) /
                                      total_total))
            else:
                h << h.td(' - ')

    return h.root


@presentation.render_for(Dashboard, model='status_by_entity')
def render_status_by_entity(self, h, comp, *args):
    h << h.h1(_(u'Status by entity'))
    status_levels = UserData.StatusLevelLabels
    status_by_entity = self.get_status_by_entity()

    def create_user_box(user_uids, title):
        query = lambda: UserRepository().get_by_uids(user_uids)
        pager = UserPager(self.parent, query)
        return PagerBox(pager, title='Users',
                        ok_button=_(u'Back to the dashboard'))

    with h.div:  # div required for progressive enhancement
        with h.table(id='status_by_entity', class_='datatable'):
            with h.thead:
                with h.tr:
                    h << h.th(_(u'Unit'))
                    for level in status_levels:
                        h << h.th(_(level))
                    h << h.th(_(u'Active %'))

            with h.tfoot:
                with h.tr(class_="totals"):
                    h << h.td(_(u"Totals"))
                    total = 0
                    for level in status_levels:
                        value = sum(len(statistics.get(level, []))
                                    for _, statistics in status_by_entity)
                        h << h.td(value)
                        total += value
                    inactive_users = sum(
                        len(statistics.get('status_level0', []))
                        for _, statistics in status_by_entity)
                    h << h.td("%.2f %%" % percentage(
                        total - inactive_users, total))

            with h.tbody:
                for entity, statistics in status_by_entity:
                    with h.tr:
                        h << h.td(entity)
                        total = 0
                        for level in status_levels:
                            users = [user.uid for user
                                     in statistics.get(level, [])]
                            with h.td:
                                title = _(u'%s - The %ss') % (entity, _(level))
                                value = len(users)
                                if value > 0:
                                    h << h.a(value).action(
                                        lambda users=users, title=title:
                                        comp.call(create_user_box(users, title)))
                                else:
                                    h << value
                                total += value

                        inactive_users = len(statistics.get('status_level0', []))
                        h << h.td(
                            "%.2f %%" % percentage(
                                total - inactive_users, total))

    col_types = ('string', 'number', 'number', 'number',
                 'number', 'number', 'number', 'percentage')
    col_defs = [ColumnDefinition(type) for type in col_types]
    h << component.Component(TableEnhancement('status_by_entity', col_defs, -21)).render(h)

    return h.root


@presentation.render_for(Dashboard, model='comments_by_entity')
def render_comments_by_entity(self, h, *args):
    h << h.h1(_(u'Comments by entity'))
    with h.table(class_='datatable'):
        with h.tr:
            h << h.th(_(u'Corporation'))
            h << h.th(_(u'Direction'))
            h << h.th(_(u'Commentators'))
            h << h.th(_(u'Comments'))
            h << h.th(_(u'Total'))
            h << h.th(_(u'Ratio'))

        total_commenters = 0
        total_comments = 0
        total_users = 0
        for elt in self.get_comments_by_entity():
            corpo_id, dir_id, commenters, comments, users, ratio = elt
            total_commenters += commenters
            total_users += users
            total_comments += comments
            with h.tr:
                h << h.td(get_corporation_label(corpo_id))
                h << h.td(get_direction_label(dir_id))
                h << h.td(str(commenters))
                h << h.td(str(comments))
                h << h.td(str(users))
                h << h.td("%.2f%%" % ratio)

        with h.tr(class_="totals"):
            h << h.td(_(u"Totals"), colspan="2")
            h << h.td("%d" % total_commenters)
            h << h.td("%d" % total_comments)
            h << h.td("%d" % total_users)
            if total_users:
                h << h.td("%.2f%%" % (100.0 * total_commenters / total_users))
            else:
                h << h.td(' - ')

    return h.root


@presentation.render_for(Dashboard, model='ideas_on_alert')
def render_ideas_on_alert_dashboard(self, h, comp, *args):
    h << h.h1(_(u'Ideas on alert and to be processed'))
    # async = h.AsyncRenderer()

    def create_idea_box(idea_ids, page_title=_(u'Ideas on alert')):
        query = lambda: IdeaRepository().get_by_ids(idea_ids)
        pager = IdeaPager(self.parent, query)
        return IdeaPagerBox(pager, model='simple', title=page_title,
                            ok_button=_(u'Back to the dashboard'))

    self.ideas_on_alert.on_answer(
        lambda ideas_and_title: comp.call(create_idea_box(*ideas_and_title)))

    h << self.ideas_on_alert.render(h)

    return h.root


@presentation.render_for(Dashboard, model='ideas_progress')
def render_ideas_progress_dashboard(self, h, comp, *args):
    h << h.h1(_(u"Ideas' progress"))
    async = h.AsyncRenderer()
    h << self.ideas_progress.render(async)
    return h.root


@presentation.render_for(Dashboard, model='ideas_by_domain_list')
def render_ideas_by_domain_list(self, h, comp, *args):
    ideas_count_by_domain = self.get_ideas_count_by_domain()
    with h.table(class_='phantom'):
        with h.tfoot:
            total = sum(map(operator.itemgetter(2), ideas_count_by_domain))
            with h.tr(class_='totals'):
                h << h.th(_(u"Totals"), class_='label')
                h << h.td("%d" % total, class_='value')

        with h.tbody:
            for id, label, count in ideas_count_by_domain:
                with h.tr:
                    with h.td(class_='label'):
                        h << h.a(_(label)).action(
                            lambda id=id, label=label: self.show_domain(
                                id, label))
                    h << h.td(str(count), class_='value')

    h << h.p(_(u'The values indicated for each domain correspond '
               u'to the sum of the published and unpublished ideas'),
             class_='legend')

    return h.root


@presentation.render_for(Dashboard, model='ideas_by_domain_chart')
def render_ideas_by_domain_chart(self, h, comp, *args):
    panel_chart_width = self.configuration['chart']['panel_chart_width']
    h << h.img(alt='', class_='chart').action(
        lambda: self.get_ideas_count_by_domain_chart(panel_chart_width))
    return h.root


@presentation.render_for(Dashboard, model='ideas_by_domain')
def render_ideas_by_domain(self, h, comp, *args):
    h << h.h1(_(u'Ideas by domain'))
    render_dashboard_panel(h, comp,
                           'ideas_by_domain_list', 'ideas_by_domain_chart')
    return h.root


@presentation.render_for(Dashboard, model='ideas_by_entity')
def render_ideas_by_entity(self, h, *args):
    h << h.h1(_(u'Ideas by unit and by challenge'))

    with h.div:  # div required for progressive enhancement
        with h.table(id='ideas_by_entity', class_='datatable'):
            with h.thead:
                with h.tr:
                    h << h.th(_(u'Unit'), title=_(u'Unit'))
                    h << h.th(_(u'Workforce'), title=_(u'Workforce'))
                    h << h.th(_(u'Challenge'), title=_(u'Challenge'))
                    h << h.th(_(u'Ideas'), title=_(u'Ideas'))
                    h << h.th(_(u'Submitters'), title=_(u'Submitters'))
                    h << h.th(_(u'Submitters percentage'), title=_(u'Submitters percentage'))

            with h.tbody:
                for unit, workforce, challenge, ideas_count, nb_authors, workforce_ratio in self.get_ideas_count_by_entity():
                    with h.tr:
                        h << h.td(unit)
                        h << h.td(workforce)
                        challenge_text = u'#%s %s' % (challenge.id, limit_string(challenge.title, 25)) if challenge else _(u'Off challenge')
                        h << h.td(challenge_text)
                        h << h.td(ideas_count)
                        h << h.td(nb_authors)
                        h << h.td("%.2f %%" % workforce_ratio)

    # all columns should be sortable
    col_defs = [ColumnDefinition(type) for type in (
        'string', 'number', 'string', 'number', 'number', 'percentage')]
    # 2*10px padding + 1px border
    h << component.Component(TableEnhancement('ideas_by_entity', col_defs, -21)
                             ).render(h)

    return h.root


@presentation.render_for(Dashboard, model='ideas_by_success_state')
def render_ideas_by_success_state(self, h, comp, *args):
    chart_width = self.configuration['chart']['chart_width']
    h << h.h1(_(u'Ideas by success state'))
    h << h.img(alt='', class_='chart').action(
        lambda: self.get_ideas_count_by_success_states_chart(
            chart_width, int(chart_width * 2 / 5), 280))
    return h.root


@presentation.render_for(Dashboard, model='ideas_by_refused_state')
def render_ideas_by_refused_state(self, h, comp, *args):
    chart_width = self.configuration['chart']['chart_width']
    h << h.h1(_(u'Ideas by refused state'))
    h << h.img(alt='', class_='chart').action(
        lambda: self.get_ideas_count_by_refused_states_chart(
            chart_width, int(chart_width * 2 / 5), 280))
    return h.root


@presentation.render_for(Dashboard, model='ideas_by_di_list')
def render_ideas_by_di_list(self, h, comp, *args):
    ideas_count_by_di = self.get_ideas_count_by_di()
    with h.table(class_='phantom'):
        with h.thead:
            with h.tr:
                h << h.th(_(u'Developer'))
                h << h.th(_(u'To process'))

        with h.tfoot:
            total = sum(map(operator.itemgetter(1), ideas_count_by_di))
            with h.tr(class_='totals'):
                h << h.th(_(u"Totals"), class_='label')
                h << h.td("%d" % total, class_='value')

        with h.tbody:
            for user, count in ideas_count_by_di:
                formated_name = user.fullname
                with h.tr:
                    h << h.td(h.a(formated_name).action(lambda user_uid=user.uid: event_management._emit_signal(self, "VIEW_DI_IDEA_SELECTOR", user_uid=user_uid)), class_='label')
                    h << h.td(str(count), class_='value')

    return h.root


@presentation.render_for(Dashboard, model='ideas_by_di_chart')
def render_ideas_by_di_chart(self, h, comp, width, *args):
    panel_chart_width = self.configuration['chart']['panel_chart_width']
    h << h.img(alt='', class_='chart').action(
        lambda: self.get_ideas_count_by_di_chart(panel_chart_width))
    return h.root


@presentation.render_for(Dashboard, model='ideas_by_di')
def render_ideas_by_di(self, h, comp, *args):
    h << h.h1(_(u'Ideas by developer'))
    render_dashboard_panel(h, comp, 'ideas_by_di_list', 'ideas_by_di_chart')
    return h.root


@presentation.render_for(Dashboard, model='ideas_by_fi_list')
def render_ideas_by_fi_list(self, h, comp, *args):
    ideas_count_by_fi = self.get_ideas_count_by_fi()
    with h.table(class_='phantom'):
        with h.thead:
            with h.tr:
                h << h.th(_(u'Facilitator'))
                h << h.th(_(u'Ideas count'))
                h << h.th(_(u'To process'))

        with h.tfoot:
            total_ideas = sum(map(operator.itemgetter(2), ideas_count_by_fi))
            total_ideas_to_review = sum(
                map(operator.itemgetter(3), ideas_count_by_fi))
            with h.tr(class_='totals'):
                h << h.th(_(u"Totals"), class_='label')
                h << h.td(str(total_ideas), class_='value')
                h << h.td(str(total_ideas_to_review), class_='value')

        with h.tbody:
            days = 15
            latecomer_fi = self.get_latecomer_fi(days)
            for uid, fullname, ideas, ideas_to_review in ideas_count_by_fi:
                with h.tr(class_='highlight' if uid in latecomer_fi else ''):
                    h << h.td(h.a(fullname).action(
                        lambda user_uid=uid: event_management._emit_signal(
                            self, "VIEW_FI_IDEA_SELECTOR",
                            user_uid=user_uid)), class_='label')
                    h << h.td(str(ideas), class_='value')
                    h << h.td(str(ideas_to_review), class_='value')

    h << h.p(_(u'In red, facilitators that have ideas '
               u'to process older than %d days.') % days,
             class_='legend')

    return h.root


@presentation.render_for(Dashboard, model='ideas_by_fi_chart')
def render_ideas_by_fi_chart(self, h, comp, width, *args):
    panel_chart_width = self.configuration['chart']['panel_chart_width']
    h << h.img(alt='', class_='chart').action(
        lambda: self.get_ideas_count_by_fi_chart(panel_chart_width))
    return h.root


@presentation.render_for(Dashboard, model='ideas_by_fi')
def render_ideas_by_fi(self, h, comp, *args):
    h << h.h1(_(u'Ideas by facilitator'))
    render_dashboard_panel(h, comp, 'ideas_by_fi_list', 'ideas_by_fi_chart')
    return h.root


# -------------------------------
@presentation.render_for(IdeasOnAlert)
def render_ideas_on_alert(self, h, comp, *args):
    challenges = [None] + list(ChallengeRepository().get_all())
    domains = list(DomainRepository().get_all())
    workflow = get_workflow()
    states = [s for s in workflow.get_progression_states()
              if s != workflow.WFStates.RETURNED_BY_DI_STATE]
    ideas_on_alert = self.get_ideas_on_alert()
    all_ideas = self.get_ideas_by_states(states)
    ideas_on_alert_grouped = self.group_by_challenge_and_domain(ideas_on_alert)
    all_ideas_grouped = self.group_by_challenge_and_domain(all_ideas)

    with h.table(class_='datatable'):
        # data
        with h.tbody:
            for challenge in challenges:
                available_domains = [
                    domain for domain in domains
                    if (challenge, domain) in ideas_on_alert_grouped
                ]

                if available_domains:
                    with h.tr:
                        domain = available_domains[0]
                        h << h.td(challenge.title if challenge else _(u'Off challenge'), rowspan=len(available_domains))
                        h << h.td(domain.i18n_label)
                        render_ideas_on_alert_item(h, states, ideas_on_alert_grouped[(challenge, domain)], all_ideas_grouped[(challenge, domain)], comp.answer)

                    for domain in available_domains[1:]:
                        with h.tr:
                            h << h.td(domain.i18n_label)
                            render_ideas_on_alert_item(h, states, ideas_on_alert_grouped[(challenge, domain)], all_ideas_grouped[(challenge, domain)], comp.answer)

        # column headings
        with h.thead:
            with h.tr:
                h << h.th(colspan=2)
                h << h.th(_(u'State'), colspan=len(states))
            with h.tr:
                h << h.th(_(u'Challenge'))
                h << h.th(_(u'Domain'))
                for state in states:
                    h << h.th(_(state))

        # totals
        with h.tfoot:
            with h.tr:
                h << h.td(_(u'Totals'), colspan=2)
                for state in states:
                    total = len([idea for idea in ideas_on_alert
                                 if idea.wf_context.state.label == state])
                    total_all = len([idea for idea in all_ideas
                                     if idea.wf_context.state.label == state])
                    h << h.td('%s (%s)' % (total, total_all),
                              style='white-space:nowrap')

    return h.root


def render_ideas_on_alert_item(h, states, ideas, all_ideas, show_ideas):
    ideas = group_as_dict(ideas, lambda idea: idea.wf_context.state.label)
    all_ideas = group_as_dict(all_ideas, lambda i: i.wf_context.state.label)
    for state in states:
        ids = [idea.id for idea in ideas.get(state, [])]
        all_ids = [idea.id for idea in all_ideas.get(state, [])]
        with h.td:
            h << (h.a(len(ids), title=_(u'Show the on alert ideas'), class_='on-alert').action(lambda ideas=ids: show_ideas((ideas, _(u'Ideas on alert')))) if ids else '')
            h << (h.a('(%s)' % len(all_ids), title=_(u'Show the ideas to process'), class_='all-ideas').action(lambda ideas=all_ids: show_ideas((ideas, _(u'Ideas to process')))) if all_ids else '')


# -------------------------------
@presentation.render_for(IdeasProgress)
def render_ideas_progress(self, h, comp, *args):
    h << comp.render(h, model='selector')
    h << comp.render(h, model='datatable')
    return h.root


@presentation.render_for(IdeasProgress, model='selector')
def render_ideas_progress_selector(self, h, comp, *args):
    since_date_calendar = component.Component(Calendar('progress_since_date',
                                                       title=_(u'Select a date'),
                                                       close_button=True,
                                                       maxdate=datetime.now()))

    period_selector_id = h.generate_id('period-selector')
    with h.form(id=period_selector_id, class_='period-selector'):
        with h.div(class_='fields'):
            with h.fieldset:
                with h.legend:
                    h << _(u"Select the period:")

                with h.div(class_='last-week field'):
                    field_id = h.generate_id('field')
                    h << h.input(id=field_id,
                                 type='radio',
                                 class_='radio',
                                 name=period_selector_id).selected(self.period_selection() == self.LAST_7_DAYS).action(lambda: self.period_selection(self.LAST_7_DAYS))
                    h << h.label(_(u"Last 7 days"), for_=field_id)

                with h.div(class_='last-month field'):
                    field_id = h.generate_id('field')
                    h << h.input(id=field_id,
                                 type='radio',
                                 class_='radio',
                                 name=period_selector_id).selected(self.period_selection() == self.LAST_30_DAYS).action(lambda: self.period_selection(self.LAST_30_DAYS))
                    h << h.label(_(u"Last month"), for_=field_id)

                with h.div(class_='since-date field'):
                    field_id = h.generate_id('field')
                    h << h.input(id=field_id,
                                 type='radio',
                                 class_='radio',
                                 name=period_selector_id).selected(self.period_selection() == self.SINCE_DATE).action(lambda: self.period_selection(self.SINCE_DATE))
                    h << h.label(_(u"Since a date:"), for_=field_id)
                    since_date_calendar().on_select = 'document.getElementById("%s").checked=true' % field_id

                    h << " "
                    with h.span(class_='since-date-selector'):
                        h << h.input(type='text',
                                     class_='date',
                                     size=10,
                                     maxlength=10,
                                     id=since_date_calendar().field_id,
                                     value=self.since_date() or '').action(self.since_date).error(self.since_date.error)
                        h << ' '
                        h << since_date_calendar.render(h, model='date_picker')

        with h.div(class_='buttons'):
            h << h.input(type='submit',
                         value=_(u"Go")).action(self.commit)

        h << since_date_calendar

    return h.root


@presentation.render_for(IdeasProgress, model='datatable')
def render_ideas_progress_datatable(self, h, comp, *args):
    state_changed_ideas = self.find_state_changed_ideas()

    if state_changed_ideas:
        url = h.a.action(self.export_xls).get('onclick').replace('return nagare_getAndEval("', '').replace('")', '')
        with h.p(class_='xls-export'):
            h << h.a(h.img(src='style/desktop/icons/xls.gif'), _(u'Export to Excel'), href=url, title=_(u'Export all filtered ideas'))

    with h.table(class_='datatable'):
        # data
        with h.tbody:
            if state_changed_ideas:
                for (from_state, to_state), ideas in state_changed_ideas:
                    if len(ideas) > 1:
                        row_class = lambda i: {0: 'inner-row-first', len(ideas) - 1: 'inner-row-last'}.get(i, 'inner-row')
                    else:
                        row_class = lambda i: ''
                    for idx, (idea, date) in enumerate(ideas):
                        with h.tr(class_=row_class(idx)):
                            if idx == 0:
                                with h.td(class_='state', rowspan=len(ideas)):
                                    h << _(from_state.label)
                                    h << h.div(u'⬇')
                                    h << _(to_state.label)
                                    h << ' (%d)' % len(ideas)
                            with h.td:
                                c = idea.challenge
                                h << (h.span('#%d' % c.id, title=c.title) if c else '')
                            with h.td:
                                formatted_date = format_datetime(date)
                                with h.span(title=_(u'State changed on %s') % formatted_date):
                                    h << component.Component(Idea(self, idea), model='short_link')
            else:
                with h.td(colspan=3,
                          class_='warning'):
                    h << _(u'No idea found')

        # column headings
        with h.thead:
            with h.tr:
                h << h.th(_(u"State changes"))
                h << h.th(_(u'Challenge'))
                h << h.th(_(u'Ideas'))

    return h.root
