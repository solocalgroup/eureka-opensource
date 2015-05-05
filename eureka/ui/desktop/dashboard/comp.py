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

import cStringIO as StringIO
import itertools
import operator
from datetime import datetime, timedelta
from urlparse import urlparse

from eureka.domain import queries
from eureka.domain.models import (CommentData, DomainData, IdeaData,
                                  IdeaWFContextData, PointData, ReminderType,
                                  StateData, UserData, VoteIdeaData,
                                  WFCommentData)
from eureka.domain.repositories import (ChallengeRepository, IdeaRepository,
                                        WFCommentRepository)
from eureka.domain.services import get_workflow, StatisticsService
from eureka.domain.user_groups import AllUnitsGroups
from eureka.infrastructure import event_management, validators
from eureka.infrastructure.content_types import excel_response
from eureka.infrastructure.tools import group_as_dict, percentage
from eureka.infrastructure.workflow.voucher import PointCategory
from eureka.infrastructure.xls_renderer import XLSRenderer
from eureka.ui.common.charts import (BarChart, DoubleHorizontalLineChart,
                                     MultipleVerticalBarChart,
                                     Pie)
from eureka.ui.common.charts.comp import InvalidDataError, TextImage
from eureka.ui.common.menu import Menu
from nagare import component, database, editor, var
from nagare.database import session
from nagare.i18n import _, format_date
from sqlalchemy import desc, func


class Dashboard(object):
    DEFAULT_COLORS = ['gold',
                      'lime',
                      'turquoise',
                      'indianred',
                      'mediumpurple',
                      'lightpink',
                      'silver',
                      'yellowgreen',
                      'violet',
                      'orange'
                      'skyblue',
                      'darkolivegreen']

    def __init__(self, parent, configuration):
        self.parent = parent
        self.configuration = configuration
        self.models_by_tab = {'ideas': configuration['tabs']['ideas'],
                              'users': configuration['tabs']['users']}

        event_management._register_listener(self.parent, self)
        self.active_tab = var.Var('')
        self.ideas_progress = component.Component(IdeasProgress(self.parent))
        self.ideas_on_alert = component.Component(IdeasOnAlert(self.parent))

        self.menu_items = [(_(u'Ideas Stats'), 'ideas', None, '', None),
                           (_(u'Users Stats'), 'users', None, '', None), ]
        self.menu = component.Component(Menu(self.menu_items),
                                        model='tab_renderer')
        self.menu.on_answer(self.select_tab)
        self.select_tab(0)

    def select_tab(self, value):
        self.active_tab(self.menu_items[value][1])
        self.menu().selected(value)

    def get_models_by_tab(self, tabname):
        return self.models_by_tab[tabname]

    def show_domain(self, id, label):
        event_management._emit_signal(self, 'VIEW_DOMAIN_IDEAS', domain_id=id,
                                      domain_label=label)

    def get_ideas_count_by_state(self):
        return queries.get_ideas_count_by_step()

    def get_ideas_count_by_refused_states_chart(self, width, legend_width,
                                                height):
        ideas_count_by_state = self.get_ideas_count_by_state().filter(
            StateData.label.in_(get_workflow().get_refused_states()))
        pie_data = []
        for idx, item in enumerate(ideas_count_by_state):
            pie_data.append(
                (item.count, _(item.state), self.DEFAULT_COLORS[idx]))
        try:
            return self._create_pie_chart(pie_data, width, height, legend_width)
        except ZeroDivisionError as e:
            import ipdb; ipdb.set_trace()
            raise

    def get_ideas_count_by_success_states_chart(self, width, legend_width,
                                                height):
        ideas_count_by_state = self.get_ideas_count_by_state().filter(
            StateData.label.in_(get_workflow().get_success_states()))
        pie_data = []
        for idx, item in enumerate(ideas_count_by_state):
            pie_data.append(
                (item.count, _(item.state), self.DEFAULT_COLORS[idx]))
        return self._create_pie_chart(pie_data, width, height, legend_width)

    def _create_pie_chart(self, pie_data, width, height, legend_width=None):
        """
        Return an image that represent a pie chart of the data, i.e. (value,
        label, color) triplets
        """
        assert pie_data
        values, labels, colors = zip(*pie_data)
        try:
            return Pie(labels,
                       values,
                       width=width,
                       height=height,
                       with_legend=True,
                       slice_format=_(u'%(value)d (%(percentage).1f%%)'),
                       legend_format=_(
                           u'%(label)s: %(value)d (%(percentage).1f%%)'),
                       legend_width=legend_width,
                       colors=colors).get_png()
        except InvalidDataError:
            return TextImage.get_png(
                text=_("No content yet"),
                width=width,
                height=height
            )

    def get_ideas_count_by_domain(self):
        return queries.get_ideas_count_by_domain()

    def get_ideas_count_by_domain_chart(self, width):
        labels = []
        values = []

        for __, domain, nb in self.get_ideas_count_by_domain():
            values.append(int(nb))
            labels.append(u'%s' % (_(domain)))

        chart = BarChart(reversed(labels), reversed(values), legend=True,
                         width=width, height=40 + len(labels) * 16)
        return chart.get_png()

    def get_ideas_count_by_domain_state(self):
        workflow = get_workflow()
        q = session.query(
            DomainData.id,
            DomainData.label,
            func.count(IdeaData.id).label('count'),
            StateData.label.label('state'))
        q = q.outerjoin(DomainData.ideas).outerjoin(IdeaData.wf_context)
        q = q.outerjoin(IdeaWFContextData.state)
        q = q.filter(StateData.label.in_(workflow.get_approved_states() +
                                         workflow.get_refused_states()))
        q = q.group_by(DomainData.id, StateData.label)
        res = {}
        for elt in q:
            if elt.label not in res:
                res[elt.label] = [0, 0]
            if elt.state == workflow.WFStates.DI_APPROVED_STATE:
                res[elt.label][0] = int(elt.count)
            else:
                res[elt.label][1] = int(elt.count)
        return res

    def get_ideas_count_by_domain_state_chart(self, width, height):
        labels = []
        values = [[], [], []]

        domains_sums = {}
        for __, domain, nb in self.get_ideas_count_by_domain():
            domains_sums[domain] = int(nb)

        for label, vals in self.get_ideas_count_by_domain_state().items():
            labels.append(_(label))
            values[0].append(vals[0])
            values[1].append(vals[1])
            values[2].append(domains_sums.get(label) - vals[0] - vals[1])

        chart = MultipleVerticalBarChart(labels, values, legend=True,
                                         width=width, height=height,
                                         stacked=True,
                                         legendlabels=[
                                             _(u'DI_APPROVED_STATE'),
                                             _(u'Basket'),
                                             _(u'Others')])
        return chart.get_png()

    def get_ideas_count_by_entity(self):
        statistics_service = StatisticsService()
        challenges = list(ChallengeRepository().get_all()) + [None]
        results = []
        for group in AllUnitsGroups:
            name = group.name
            workforce = len(group.users)
            for challenge in challenges:
                total_ideas, nb_authors = statistics_service.get_users_statistics_on_ideas(
                    tuple(group.users),
                    challenge=challenge)
                authors_percentage = percentage(nb_authors, workforce)

                results.append((name, workforce, challenge, total_ideas,
                                nb_authors, authors_percentage))
        return results

    def get_active_users_by_entity(self):
        q = session.query(
            UserData.corporation_id.label('corporation_id'),
            UserData.direction_id.label('direction_id'),
            func.count(UserData.uid).label('user_total'))
        q = q.filter(UserData.enabled == True)
        q = q.group_by(UserData.corporation_id,
                       UserData.direction_id).subquery()

        e = func.count(UserData.uid).label('user_count')

        q2 = session.query(
            UserData.corporation_id.label('Entite'),
            UserData.direction_id.label('Direction'),
            e.label("actifs"),
            q.c.user_total.label("total"),
            ((100 * e) / q.c.user_total).label('pourcent'))
        q2 = q2.filter(UserData.corporation_id == q.c.corporation_id)
        q2 = q2.filter(UserData.direction_id == q.c.direction_id)
        q2 = q2.filter(UserData.enabled == True)
        q2 = q2.filter(UserData.last_connection_date != None)
        q2 = q2.group_by(UserData.corporation_id, UserData.direction_id)
        q2 = q2.order_by(desc('pourcent'))

        return q2

    def get_votes_by_entity(self):
        q0 = session.query(
            UserData.uid,
            func.count(VoteIdeaData.id).label('vote_count'))
        q0 = q0.outerjoin(UserData.votes_for_ideas)
        q0 = q0.filter(UserData.enabled == True)
        q0 = q0.group_by(UserData.uid).subquery()

        q1 = session.query(
            UserData.corporation_id.label('corporation_id'),
            UserData.direction_id.label('direction_id'),
            func.count(UserData.uid).label('user_total'),
            UserData.enabled == True)
        q1 = q1.group_by(UserData.corporation_id,
                         UserData.direction_id).subquery()

        q2 = session.query(
            UserData.corporation_id.label('corporation_id'),
            UserData.direction_id.label('direction_id'),
            func.count(UserData.uid).label('user_voted'),
            q1.c.user_total.label("total_user"),
            func.sum(q0.c.vote_count).label("total_votes"),
            ((100 * func.count(UserData.uid).label(
                'user_voted')) / q1.c.user_total).label('pourcent'))
        q2 = q2.filter(q0.c.vote_count != 0)
        q2 = q2.filter(UserData.enabled == True)
        q2 = q2.filter(UserData.uid == q0.c.uid)
        q2 = q2.filter(UserData.direction_id == q1.c.direction_id)
        q2 = q2.filter(UserData.corporation_id == q1.c.corporation_id)
        q2 = q2.group_by(UserData.corporation_id, UserData.direction_id)
        q2 = q2.order_by(desc('pourcent'))

        return q2

    def get_comments_by_entity(self):
        # Count distinct commenters for each direction
        commenters_by_direction = {}
        q = session.query(
            UserData.corporation_id, UserData.direction_id, func.count(
                UserData.uid.distinct())
        ).join(UserData.comments).filter(
            UserData.enabled == True
        ).group_by(
            UserData.corporation_id, UserData.direction_id
        )

        for corpo_id, dir_id, commenters_count in q:
            commenters_by_direction[(corpo_id, dir_id)] = commenters_count

        # Count comments for each direction
        comments_by_direction = {}
        q = session.query(
            UserData.corporation_id, UserData.direction_id, func.count(
                CommentData.id)
        ).join(
            UserData.comments
        ).filter(
            UserData.enabled == True
        ).group_by(
            UserData.corporation_id, UserData.direction_id
        )

        for corpo_id, dir_id, comments_count in q:
            comments_by_direction[(corpo_id, dir_id)] = comments_count

        # Count users in each direction
        count_by_direction = {}
        q = session.query(
            UserData.corporation_id,
            UserData.direction_id,
            func.count(UserData.uid)
        ).filter(
            UserData.enabled == True
        ).group_by(
            UserData.corporation_id,
            UserData.direction_id
        )
        for corpo_id, dir_id, user_count in q:
            count_by_direction[(corpo_id, dir_id)] = user_count

        r = []
        for (corporation_id, direction_id), comments_count in comments_by_direction.iteritems():
            if direction_id:
                commenters = commenters_by_direction.get((corporation_id, direction_id), 0)
                comments = comments_by_direction.get((corporation_id, direction_id), 0)
                count = count_by_direction.get((corporation_id, direction_id), 0)
                r.append((corporation_id,
                          direction_id,
                          commenters,
                          comments,
                          count,
                          100.0 * commenters / count))

        # Results sorted by descending ratio
        return sorted(r, key=lambda row: row[5], reverse=True)

    def get_status_by_entity(self):
        statistics_service = StatisticsService()
        results = []
        for group in AllUnitsGroups:
            statistics = statistics_service.get_users_points_statistics(
                group.users)
            results.append((group.name, statistics))
        return results

    def get_latecomer_fi(self, n_days=7):
        n_days_ago = datetime.now() - timedelta(days=n_days)
        query = session.query(IdeaWFContextData,
                              func.max(WFCommentData.submission_date)) \
            .join(WFCommentData.idea_wf) \
            .join(IdeaWFContextData.state) \
            .filter(StateData.label == get_workflow().WFStates.FI_NORMALIZE_STATE) \
            .group_by(IdeaWFContextData.id)

        # there's at least one idea in FI_NORMALIZE_STATE that is older than n_days_ago
        return set(wfcontext.assignated_fi_uid for wfcontext, date in query if
                   date < n_days_ago)

    def get_ideas_count_by_di(self):
        return queries.get_ideas_count_by_di()

    def get_ideas_count_by_di_chart(self, width):
        labels = []
        values = []
        for user, count in self.get_ideas_count_by_di():
            formated_name = user.fullname
            values.append(int(count))
            labels.append(u'%s' % (formated_name.capitalize()))
        chart = BarChart(reversed(labels), reversed(values), legend=True,
                         width=width, height=40 + len(labels) * 16)
        return chart.get_png()

    def get_ideas_count_by_fi(self):
        results = []
        for user, iter in itertools.groupby(
                queries.get_ideas_count_in_fi_baskets(),
                operator.itemgetter(0)):
            ideas_counts = dict(
                (state.label, count) for _, state, count in iter)
            results.append((user.uid,
                            user.fullname,
                            sum(ideas_counts.values()),
                            ideas_counts.get(get_workflow().WFStates.FI_NORMALIZE_STATE, 0)))
        return results

    def get_ideas_count_by_fi_chart(self, width):
        labels = []
        values = []
        for __, fullname, total_ideas, __ in self.get_ideas_count_by_fi():
            formated_name = fullname
            values.append(int(total_ideas))
            labels.append(u'%s' % (formated_name.capitalize()))
        chart = BarChart(reversed(labels), reversed(values), legend=True,
                         width=width, height=40 + len(labels) * 16)
        return chart.get_png()

    def get_ideas_count_day_by_day(self, from_date):
        # count ideas day by day (not draft) since the from_date
        date = IdeaData.submission_date.label('date')
        db_type = urlparse(database._engines.keys()[0]).scheme
        if db_type == 'sqlite':
            formatted_date = func.strftime(
                '%d/%m/%Y', IdeaData.submission_date).label('formatted_date')
        else:
            formatted_date = func.date_format(
                IdeaData.submission_date, '%d/%m/%y').label('formatted_date')
        q = (session.query(formatted_date, date,
                           func.count(IdeaData.id).label('count'))
             .outerjoin(IdeaData.wf_context)
             .outerjoin(IdeaWFContextData.state)
             .filter(StateData.label.in_(get_workflow().get_workflow_states()))
             .filter(IdeaData.submission_date >= from_date)
             .group_by(formatted_date)
             .order_by(formatted_date))
        return q

    def get_connection_count_day_by_day(self, from_date, platform=None):
        # count first connection day by day since the from_date
        date = PointData.date.label('date')
        db_type = urlparse(database._engines.keys()[0]).scheme
        if db_type == 'sqlite':
            formatted_date = func.strftime(
                '%d/%m/%Y', IdeaData.submission_date).label('formatted_date')
        else:
            formatted_date = func.date_format(
                IdeaData.submission_date, '%d/%m/%y').label('formatted_date')

        q = session.query(date,
                          formatted_date,
                          func.count(PointData.id).label('count'))
        q = q.filter(
            PointData.label == PointCategory.FIRST_CONNECTION_OF_THE_DAY)
        q = q.filter(PointData.date >= from_date)
        q = q.group_by(formatted_date)
        q = q.order_by(formatted_date)

        if platform:
            q = q.filter(PointData.subject_id == platform)
        return q

    def get_2weeks_chart(self, width, height):
        start_date = datetime.today().date() - timedelta(days=14)

        ideas = {}
        for item in self.get_ideas_count_day_by_day(start_date):
            ideas[item.formatted_date] = item.count

        connections = {}
        for item in self.get_connection_count_day_by_day(start_date):
            connections[item.formatted_date] = item.count

        labels = [
            format_date(start_date + timedelta(days=days), format="short")
            for days in range(0, 14)]

        data = [(ideas.get(item, 0), connections.get(item, 0))
                for item in labels]

        legend_labels = [_(u'Ideas count'), _(u'Connections count')]
        chart = DoubleHorizontalLineChart(labels, zip(*data),
                                          width=width, height=height,
                                          legend=True,
                                          legendlabels=legend_labels)

        return chart.get_png()

    def get_2months_chart(self, width, height):
        today = datetime.today().date()
        start_date = today - timedelta(days=today.weekday(), weeks=7)

        ideas = {}
        for item in self.get_ideas_count_day_by_day(start_date):
            week_number = item.date.isocalendar()[1]
            ideas.setdefault(week_number, 0)
            ideas[week_number] += item.count

        connections = {}
        for item in self.get_connection_count_day_by_day(start_date):
            week_number = item.date.isocalendar()[1]
            connections.setdefault(week_number, 0)
            connections[week_number] += item.count

        # last 2 months labels
        week_numbers = [(start_date + timedelta(weeks=n)).isocalendar()[1]
                        for n in range(0, 8)]

        data = [(ideas.get(item, 0), connections.get(item, 0))
                for item in week_numbers]

        labels = [u'%s %s' % (_(u'week'), n) for n in week_numbers]
        legend_labels = [_(u'Ideas count'), _(u'Connections count')]
        chart = DoubleHorizontalLineChart(labels, zip(*data),
                                          width=width, height=height,
                                          legend=True,
                                          legendlabels=legend_labels)

        return chart.get_png()


class IdeasOnAlert(object):
    def __init__(self, parent):
        self.parent = parent

    def get_ideas_on_alert(self):
        return IdeaRepository().get_by_reminder_before_date(datetime.now(),
                                                            ReminderType.UnchangedState)

    def get_ideas_by_states(self, states):
        return IdeaRepository().get_by_states(states)

    def group_by_challenge_and_domain(self, ideas):
        return group_as_dict(ideas, lambda idea: (idea.challenge, idea.domain))


class IdeasProgress(object):
    # period constants
    LAST_7_DAYS, LAST_30_DAYS, SINCE_DATE = range(3)

    def __init__(self, parent):
        self.parent = parent
        self.period_selection = editor.Property(self.LAST_7_DAYS)
        self.since_date = editor.Property().validate(validators.date)

    @property
    def reference_date(self):
        if self.period_selection.value == self.LAST_7_DAYS:
            return datetime.now().date() - timedelta(days=7)

        if self.period_selection.value == self.LAST_30_DAYS:
            return datetime.now().date() - timedelta(days=30)

        return self.since_date.value

    def is_validated(self):
        return (not self.period_selection.error and
                not self.since_date.error and
                self.since_date.value is not None if self.period_selection.value == self.SINCE_DATE else True)

    def commit(self):
        pass  # nothing to do, but an action is required for asynchronous rendering to work

    def find_state_changed_ideas(self, reverse=False):
        if not self.is_validated():
            return []

        # query workflow comments that have occured since the reference date
        wfcomments = WFCommentRepository().get_by_submission_after_date(
            self.reference_date)

        # (from_state, to_state) -> [(idea1, change_date1), (idea2, change_date2), ...]
        mapping = {}
        for wfcomment in wfcomments:
            # Omit transitions from DI_APPRAISAL_STATE to DI_APPRAISAL_STATE (changed developer for the idea)
            if wfcomment.from_state.label == wfcomment.to_state.label == get_workflow().WFStates.DI_APPRAISAL_STATE:
                continue

            k = (wfcomment.from_state, wfcomment.to_state)
            v = (wfcomment.idea_wf.idea, wfcomment.submission_date)
            mapping.setdefault(k, []).append(v)

        # FIXME: filter relevant states?
        return sorted(mapping.items(),
                      key=lambda (state_change, ideas): (state_change[0].id,
                                                         state_change[1].id),
                      reverse=reverse)

    def export_xls(self):
        state_changed_ideas = self.find_state_changed_ideas(reverse=True)

        r = XLSRenderer()
        center_top = r.Style.Centered + r.Style.VerticalAlignTop
        left_top = r.Style.VerticalAlignTop
        heading = r.Style.ColumnHeading + r.Style.VerticalAlignCenter + r.Style.Wrap + r.Background.LightYellow

        with r.sheet(_(u"Ideas on alert")):
            with r.row:
                r << r.cell(_(u"State changes"), style=heading)
                r << r.cell(_(u'Challenge'), style=heading)
                r << r.cell(_(u'Ideas'), style=heading)

            for (from_state, to_state), ideas in state_changed_ideas:
                for idx, (idea, __) in enumerate(ideas):
                    with r.row:
                        if not idx:
                            r << r.cell(u'%s\n⬇\n%s (%d)' %
                                        (_(from_state.label),
                                         _(to_state.label),
                                         len(ideas)),
                                        rowspan=len(ideas),
                                        style=center_top)
                        r << r.cell(
                            u'#%d' % idea.challenge.id if idea.challenge else '',
                            style=center_top)
                        r << r.cell(u'N°%d - %s' % (idea.id, idea.title),
                                    style=left_top)
        raise excel_response(r.get_content(), filename='idees_en_alerte.xls')
