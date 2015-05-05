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

from datetime import datetime, timedelta

from nagare.i18n import _, get_month_names, format_datetime

from eureka.domain.repositories import ChallengeRepository, CommentRepository
from eureka.domain.services import StatisticsService, NO_FILTER
from eureka.infrastructure.tools import is_string


class RowType(object):
    Odd = 'odd'
    Even = 'even'
    First = 'first'
    Last = 'last'


class IdeasStatistics(object):
    # items to be shown for each group
    def group_items(self, r, date):
        return ((None, r.Background.Grey25, _(u'Consolidated')),
                (date - timedelta(days=28), r.Background.Tan, _(u'Last 28 days')),
                (date - timedelta(days=7), r.Background.LightYellow, _(u'Last 7 days')))

    def headings_style(self, r):
        return r.Style.ColumnHeading + r.Style.VerticalAlignCenter + r.Style.Wrap + r.Background.LightYellow

    def __init__(self, statistics_service=StatisticsService, challenge_repository=ChallengeRepository):
        self.statistics_service = statistics_service()
        self.challenge_repository = challenge_repository()

    def get_title(self, sheet_name, date):
        # date information
        month_name = get_month_names()[date.month].upper()
        week_number = date.strftime('%U')

        # format the string
        return _(u'%s - %s - Week %s') % (sheet_name, month_name, week_number)

    def render(self, r, user_groups_categories, date=datetime.now()):
        # Statistics
        for name, groups in user_groups_categories:
            # global sheet
            sheet = _(u'%s, global stats') % name
            title_prefix = _(u'Global %s statistics') % name
            title = self.get_title(title_prefix, date)
            subtitle = None
            self.render_statistics_sheet(r, sheet, title, subtitle, groups, date, None)

            # challenges sheets
            for challenge in self.challenge_repository.get_all():
                sheet = _(u'%s, stats challenge #%s') % (name, challenge.id)
                title_prefix = _(u'%s statistics for challenge #%s') % (name, challenge.id)
                title = self.get_title(title_prefix, date)
                subtitle = challenge.title
                self.render_statistics_sheet(r, sheet, title, subtitle, groups, date, challenge)

        # Composition of the groups
        for name, groups in user_groups_categories:
            composition_sheet = _(u'%s, corresp.') % name
            composition_title = _(u'%s correspondences') % name
            self.render_groups_composition_sheet(r, composition_sheet, composition_title, groups)

    def render_statistics_sheet(self, r, name, title, subtitle, groups, date, challenge=None):
        with r.sheet(name):
            # items rows that will be displayed for each group
            group_items = self.group_items(r, date)

            # title
            self.render_title(r, title, subtitle, 11)

            # headings
            self.render_group_statistics_column_headings(r, challenge)

            # data rows
            first_data_row = r.current_row + 1
            last_index = len(groups) - 1
            for idx, group in enumerate(groups):
                row_types = []
                if idx % 2:
                    row_types.append(RowType.Odd)
                else:
                    row_types.append(RowType.Even)

                if idx == 0:
                    row_types.append(RowType.First)
                elif idx == last_index:
                    row_types.append(RowType.Last)

                self.render_group_statistics(r, group, group_items, row_types, challenge)

            # totals
            self.render_group_statistics_totals(r, group_items, first_data_row, challenge)

    def render_group_statistics_column_headings(self, r, challenge):
        headings_style = self.headings_style(r)

        # first row of headings
        with r.row:
            r << r.cell(colspan=2 + (2 if not challenge else 0))
            r << r.cell(_(u'Statistics on published ideas only'), colspan=9,
                        style=headings_style + r.Border.AllMedium)

        # second and third row of headings
        with r.row(height=36):
            r << r.cell(_(u'Unit'), rowspan=2, width=500,
                        style=headings_style + r.Border.LeftMedium + r.Border.TopMedium)
            r << r.cell(_(u'Workforce'), rowspan=2,
                        style=headings_style + r.Border.Left + r.Border.TopMedium + r.Border.RightMedium)

            if not challenge:
                r << r.cell(_(u'Users who have connected at least once'), colspan=2,
                            style=headings_style + r.Border.Bottom + r.Border.TopMedium + r.Border.RightMedium)

            r << r.cell(_(u'IDEAS'), rowspan=2,
                        style=headings_style + r.Border.Right + r.Border.TopMedium)
            r << r.cell(_(u'Users who have published at least one idea'), colspan=2,
                        style=headings_style + r.Border.Bottom + r.Border.TopMedium)
            r << r.cell(_(u'VOTES'), rowspan=2,
                        style=headings_style + r.Border.Left + r.Border.Right + r.Border.TopMedium)
            r << r.cell(_(u'Users who have voted at least once'), colspan=2,
                        style=headings_style + r.Border.Bottom + r.Border.TopMedium)
            r << r.cell(_(u'COMMENTS'), rowspan=2,
                        style=headings_style + r.Border.Left + r.Border.Right + r.Border.TopMedium)
            r << r.cell(_(u'Users who have published at least one comment'), colspan=2,
                        style=headings_style + r.Border.Bottom + r.Border.RightMedium)

        with r.row:
            if not challenge:
                r << r.cell(_(u'number'), style=headings_style)
                r << r.cell(_(u'workforce %'), style=headings_style + r.Border.Left + r.Border.RightMedium)

            for idx in range(3):
                last_style = r.Border.RightMedium if (idx == 2) else ''
                r << r.cell(_(u'number'), style=headings_style)
                r << r.cell(_(u'workforce %'), style=headings_style + r.Border.Left + last_style)

    def render_group_statistics(self, r, group, group_items, row_types, challenge):
        users = group.users
        items_statistics = [self.get_statistics(users, item[0], challenge) for item in group_items]

        group_style = r.Style.VerticalAlignCenter + r.Border.TopMedium
        if RowType.Odd in row_types:
            group_style += r.Background.PaleBlue
        first_row = RowType.First in row_types

        workforce = len(users)
        with r.row:
            r << r.cell(group.name, rowspan=len(group_items),
                        style=group_style + r.Border.LeftMedium)
            workforce_cell = r.current_cell_id
            r << r.cell(workforce, rowspan=len(group_items),
                        style=group_style + r.Style.Centered + r.Border.Left + r.Border.RightMedium)
            item_style, item_caption = group_items[0][1:]
            item_statistics = items_statistics[0]
            self.render_group_statistics_item(r, item_statistics, workforce_cell, challenge,
                                              item_style + r.Style.Centered + r.Border.TopMedium + r.Border.Left)
            # caption
            if first_row:
                self.render_group_statistics_item_caption(r, item_caption, item_style + r.Border.All)

        for i in range(1, len(group_items)):
            with r.row:
                item_style, item_caption = group_items[i][1:]
                item_statistics = items_statistics[i]
                self.render_group_statistics_item(r, item_statistics, workforce_cell, challenge,
                                                  item_style + r.Style.Centered + r.Border.Top + r.Border.Left)
                # caption
                if first_row:
                    self.render_group_statistics_item_caption(r, item_caption,
                                                              item_style + r.Border.All)

    def render_group_statistics_totals(self, r, group_items, first_data_row, challenge):
        last_data_row = r.current_row
        group_rows = range(first_data_row, last_data_row + 1, 3)  # +1 since the first row in excel is numbered 1
        workforce_total = self.sum([r.cell_id(row_index, 1) for row_index in group_rows])

        item_style = r.Border.Left + r.Style.Centered
        with r.row:
            r << r.cell(rowspan=len(group_items), style=r.Border.TopMedium)
            workforce_total_cell = r.current_cell_id
            r << r.cell(r.formula(workforce_total), rowspan=len(group_items), style=r.Border.AllMedium + r.Style.Centered + r.Style.VerticalAlignCenter)
            self.render_group_statistics_totals_item(r, [index for index in group_rows], workforce_total_cell, challenge,
                                                     item_style + group_items[0][1] + r.Border.TopMedium)

        for i in range(1, len(group_items)):
            with r.row:
                style = item_style + group_items[i][1] + r.Border.Top + (r.Border.BottomMedium if i == len(group_items) - 1 else '')
                self.render_group_statistics_totals_item(r, [index + i for index in group_rows], workforce_total_cell, challenge,
                                                         style)

    def render_group_statistics_totals_item(self, r, rows, workforce_total_cell, challenge, item_style):
        if not challenge:
            cells = [r.cell_id(row_index, r.current_col) for row_index in rows]
            workforce_cell = r.current_cell_id
            r << r.cell(r.formula(self.sum(cells)), style=item_style)
            formula = self.ratio(workforce_cell, workforce_total_cell)
            r << r.cell(r.formula(formula), style=item_style + r.Border.RightMedium, format=r.Format.Percentage)

        for __ in range(3):
            # simple totals
            cells = [r.cell_id(row_index, r.current_col) for row_index in rows]
            r << r.cell(r.formula(self.sum(cells)), style=item_style)
            cells = [r.cell_id(row_index, r.current_col) for row_index in rows]
            workforce_cell = r.current_cell_id
            r << r.cell(r.formula(self.sum(cells)), style=item_style)
            # workforce percentage
            formula = self.ratio(workforce_cell, workforce_total_cell)
            r << r.cell(r.formula(formula), style=item_style, format=r.Format.Percentage)
        r << r.cell(style=r.Border.LeftMedium)

    def render_group_statistics_item_caption(self, r, text, style):
        r << r.cell()
        r << r.cell(text, width=300, style=style)

    def render_group_statistics_item(self, r, statistics, workforce_cell, challenge, style):
        if not challenge:
            ratio_nb_connected = self.ratio(r.current_cell_id, workforce_cell)
            r << r.cell(statistics.nb_connected, style=style + r.Border.LeftMedium)
            r << r.cell(r.formula(ratio_nb_connected), style=style + r.Border.RightMedium, format=r.Format.Percentage)

        r << r.cell(statistics.total_ideas, style=style)
        ratio_nb_authors = self.ratio(r.current_cell_id, workforce_cell)
        r << r.cell(statistics.nb_authors, style=style)
        r << r.cell(r.formula(ratio_nb_authors), style=style, format=r.Format.Percentage)

        r << r.cell(statistics.total_votes, style=style)
        ratio_nb_voters = self.ratio(r.current_cell_id, workforce_cell)
        r << r.cell(statistics.nb_voters, style=style)
        r << r.cell(r.formula(ratio_nb_voters), style=style, format=r.Format.Percentage)

        r << r.cell(statistics.total_comments, style=style)
        ratio_nb_commentators = self.ratio(r.current_cell_id, workforce_cell)
        r << r.cell(statistics.nb_commentators, style=style)
        r << r.cell(r.formula(ratio_nb_commentators), style=style + r.Border.RightMedium, format=r.Format.Percentage)

    def get_statistics(self, users, date, challenge):
        if challenge is None:
            challenge = NO_FILTER
        return self.statistics_service.get_users_statistics(tuple(users), date, challenge)

    def render_groups_composition_sheet(self, r, name, title, groups):
        with r.sheet(name):
            # page title
            self.render_title(r, title, None, 5)

            # column headers
            with r.row:
                style = self.headings_style(r) + r.Border.TopMedium + r.Border.BottomMedium + r.Border.Left + r.Border.Right
                r << r.cell(_(u'Unit'), width=500, style=style + r.Border.LeftMedium + r.Border.RightMedium)
                r << r.cell(_(u'Corporation'), width=300, style=style)
                r << r.cell(_(u'Direction'), width=450, style=style)
                r << r.cell(_(u'Service'), width=450, style=style)
                r << r.cell(_(u'Site'), width=300, style=style + r.Border.RightMedium)

            # data
            for group_index, group in enumerate(groups):
                group_items = []
                # organizations
                for organization_tuple in group.organizations:
                    group_items.append([(item or _(u'All')) for item in organization_tuple])
                # specific users
                if group.specific_users:
                    group_items.append(', '.join(group.specific_users))

                style = r.Style.VerticalAlignCenter
                if group_index % 2:  # odd style
                    style += r.Background.PaleBlue

                with r.row:
                    r << r.cell(group.name, rowspan=len(group_items), style=style + r.Border.Top + r.Border.LeftMedium + r.Border.RightMedium)
                    self.render_group_composition_item(r, group_items[0], style + r.Border.Top + r.Border.Left)

                for group_item in group_items[1:]:
                    with r.row:
                        self.render_group_composition_item(r, group_item, style + r.Border.Top + r.Border.Left)

            with r.row:
                for __ in range(5):
                    r << r.cell(style=r.Border.TopMedium)

    def render_group_composition_item(self, r, item, style):
        if is_string(item):
            r << r.cell(item, colspan=4, style=style + r.Style.Wrap + r.Border.RightMedium)
        else:
            corporation, direction, service, site = item
            r << r.cell(corporation, style=style)
            r << r.cell(direction, style=style)
            r << r.cell(service, style=style)
            r << r.cell(site, style=style + r.Border.RightMedium)

    def render_title(self, r, title, subtitle, colspan):
        for __ in range(2):
            r << r.row()

        with r.row:
            r << r.cell(title, colspan=colspan, style=r.Style.Heading1)

        if subtitle:
            with r.row:
                r << r.cell(subtitle, colspan=colspan, style=r.Style.Heading2)

        for __ in range(2):
            r << r.row()

    def ratio(self, num, den):
        return 'IF(N(%s)<>0;%s/%s;"")' % (den, num, den)

    def sum(self, terms):
        # split the terms into chunks if necessary (xlwt or excel does not support summing more than 30 items)
        if len(terms) > 30:
            terms = [self.sum(group) for group in self._chunks(terms, 30)]
        return 'SUM(%s)' % ';'.join(terms)

    def sum_range(self, first_cell_id, second_cell_id):
        return 'SUM(%s:%s)' % (first_cell_id, second_cell_id)

    def _chunks(self, l, n):
        """Split a list into chunks of length n (at most)"""
        return [l[i:i + n] for i in range(0, len(l), n)]


class MostLikedComments(object):
    def comments_and_scores(self, date, max_results):
        q = CommentRepository().get_most_voted_comments(date)
        if max_results:
            q = q.limit(max_results)
        return q

    def render(self, r, date=datetime.now(), max_results=None):
        title = _("Most Liked Comments")
        with r.sheet(title):
            # title
            r << r.row()
            with r.row:
                r << r.cell(title, colspan=5, style=r.Style.Heading1)
            r << r.row()

            # column headings
            with r.row:
                style = (r.Border.TopMedium +
                         r.Border.BottomMedium +
                         r.Border.Left +
                         r.Border.Right +
                         r.Style.ColumnHeading +
                         r.Style.Wrap +
                         r.Background.LightYellow)

                r << r.cell(_("Score"), width=100, style=style + r.Border.LeftMedium)
                r << r.cell(_("Comment"), width=1400, style=style)
                r << r.cell(_("Author"), width=300, style=style)
                r << r.cell(_("Date"), width=200, style=style)
                r << r.cell(_("Idea"), width=100, style=style + r.Border.RightMedium)

            # data
            for idx, (comment, score) in enumerate(self.comments_and_scores(date, max_results)):
                style = (r.Style.VerticalAlignCenter +
                         r.Border.All +
                         r.Style.Wrap)

                # odd rows style
                if idx % 2:
                    style += r.Background.PaleBlue

                with r.row:
                    r << r.cell(score, style=style + r.Border.LeftMedium)
                    r << r.cell(comment.content, style=style)
                    r << r.cell(comment.created_by.fullname, style=style)
                    r << r.cell(format_datetime(comment.submission_date, format='short'), style=style)
                    r << r.cell(comment.idea.id, style=style + r.Border.RightMedium)

            with r.row:
                r << r.cell(colspan=5, style=r.Border.TopMedium)
