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

from cStringIO import StringIO
from datetime import datetime
import itertools

from sqlalchemy.orm.query import aliased
import xlwt

from nagare.database import session
from nagare.i18n import _

from eureka.infrastructure.urls import get_url_service
from eureka.domain.models import (UserData, OrganizationData, IdeaData,
                                  ChallengeData, DomainData, StateData,
                                  AuthorData, IdeaWFContextData, IdeaEvalContextData)


def export(idea_ids, permission=None, filename_prefix='export'):
    # gets the information to export
    columns = [(_(u'Id'), 1500),
               (_(u'Title'), 20000),
               (_(u'Challenge'), 10000),
               (_(u'Description'), 15000),
               (_(u'Origin'), 10000),
               (_(u'Impact'), 10000),
               (_(u'Submission date'), 5000),
               (_(u'Author name'), 7000),
               (_(u'Position'), 3000),
               (_(u'Corporation'), 7000),
               (_(u'Direction'), 7000),
               (_(u'Service'), 7000),
               (_(u'Site'), 7000),
               (_(u'Votes count'), 5000),
               (_(u'Comments count'), 5000),
               (_(u'Domain'), 8000),
               (_(u'State'), 5000),
               (_(u'Url'), 8000),
               (_(u'Facilitator'), 5000),
               (_(u'Developer'), 5000),
               (_(u'Benefit_department'), 5000),
               ]

    # launches the query
    # FIXME: don't create a query: use the appropriate IdeaRepository's method instead
    AuthorUser = aliased(UserData)
    FIUser = aliased(UserData)
    DIUser = aliased(UserData)
    Corporation = aliased(OrganizationData)
    Direction = aliased(OrganizationData)
    Service = aliased(OrganizationData)
    Site = aliased(OrganizationData)
    SubSite = aliased(OrganizationData)
    q = session.query(
        IdeaData.id,
        IdeaData.submission_date,
        IdeaData.challenge_id,
        ChallengeData.title.label('challenge'),
        IdeaData.title,
        IdeaData.description,
        IdeaData.origin,
        IdeaData.impact,
        IdeaData.benefit_department,
        AuthorUser.uid,
        AuthorUser.firstname,
        AuthorUser.lastname,
        AuthorUser.position,
        Corporation.label.label('corporation'),
        Direction.label.label('direction'),
        Service.label.label('service'),
        Site.label.label('site'),
        DomainData.label.label('domain'),
        FIUser.uid.label('fi_uid'),
        FIUser.firstname.label('fi_firstname'),
        FIUser.lastname.label('fi_lastname'),
        DIUser.uid.label('di_uid'),
        DIUser.firstname.label('di_firstname'),
        DIUser.lastname.label('di_lastname'),
        StateData.label.label('state'),
        IdeaData.total_votes,
        IdeaData.total_comments,
        IdeaEvalContextData.target_date.label('target_date'),
        IdeaEvalContextData.goal.label('goal'),
        IdeaEvalContextData.revenues_first_year.label('revenues_first_year'),
        IdeaEvalContextData.revenues_first_year_value.label(
            'revenues_first_year_value'),
        IdeaEvalContextData.revenues_second_year.label('revenues_second_year'),
        IdeaEvalContextData.revenues_second_year_value.label(
            'revenues_second_year_value'),
        IdeaEvalContextData.expenses_first_year.label('expenses_first_year'),
        IdeaEvalContextData.expenses_first_year_value.label(
            'expenses_first_year_value'),
        IdeaEvalContextData.expenses_second_year.label('expenses_second_year'),
        IdeaEvalContextData.expenses_second_year_value.label(
            'expenses_second_year_value'),
        IdeaEvalContextData.evaluation_impact.label('evaluation_impact'),
    ).outerjoin(AuthorData)

    q = q.join((AuthorUser, AuthorData.user))
    q = q.outerjoin((Corporation, AuthorUser.corporation))
    q = q.outerjoin((Direction, AuthorUser.direction))
    q = q.outerjoin((Service, AuthorUser.service))
    q = q.outerjoin((Site, AuthorUser.site))
    q = q.outerjoin((SubSite, AuthorUser.subsite))
    q = q.outerjoin(IdeaData.wf_context)
    q = q.outerjoin(IdeaData.eval_context)
    q = q.outerjoin(IdeaData.domain)
    q = q.outerjoin(IdeaWFContextData.state)
    q = q.outerjoin((DIUser, IdeaWFContextData.assignated_di))
    q = q.outerjoin((FIUser, IdeaWFContextData.assignated_fi))
    q = q.outerjoin(IdeaData.challenge)
    q = q.filter(IdeaData.id.in_(idea_ids))

    years_revenues = []
    years_expenses = []
    if permission in ('dsig', 'developer'):
        columns = columns + [(_(u'target_date'), 5000),
                             (_(u'goal'), 5000)]
        for row in q:
            years_revenues = years_revenues + [row.revenues_first_year, row.revenues_second_year]
            years_revenues = list(set(years_revenues))
            years_revenues = [y for y in years_revenues if y]
            years_revenues.sort()
            years_expenses = years_expenses + [row.expenses_first_year, row.expenses_second_year]
            years_expenses = list(set(years_expenses))
            years_expenses = [y for y in years_expenses if y]
            years_expenses.sort()

        columns = columns + [(_(u'Revenue %s') % y, 5000) for y in years_revenues]
        columns = columns + [(_(u'Expenses %s') % y, 5000) for y in years_expenses]
        columns = columns + [(_(u'CF/MSCV'), 3000)]

    authors = {}
    for id, ideas in itertools.groupby(q, key=lambda row: row.id):
        for idea in ideas:
            authors.setdefault(id, []).append(
                '%s %s' % (idea.firstname, idea.lastname))

    # creates the workbook
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet(u'Export')

    f = xlwt.Formatting.Font()
    f.underline = xlwt.Formatting.Font.UNDERLINE_SINGLE
    f.colour_index = 4  # built-in blue

    link_style = xlwt.Style.XFStyle()
    link_style.font = f

    date_style = xlwt.easyxf(num_format_str='DD-MM-YYYY HH:MM')

    # write header row & define columns width
    for col_index, (name, width) in enumerate(columns):
        ws.write(0, col_index, unicode(name))
        ws.col(col_index).width = width

    # write ideas
    duplicates = set()
    row_index = 1
    for row in q:

        # Remove duplicates
        # EV 592 : all author names in the same cell
        if row.id in duplicates:
            continue
        else:
            duplicates.add(row.id)

        idea_url = get_url_service().expand_url(['idea', row.id], relative=False)

        row_data = [
            unicode(row.id),
            row.title,
            u'%s (%s)' % (row.challenge, row.challenge_id) if row.challenge_id else u'',
            row.description,
            row.origin,
            row.impact,
            (row.submission_date, date_style),
            '; '.join(authors.get(row.id, [])),
            row.position,
            row.corporation,
            row.direction,
            row.service,
            row.site,
            unicode(row.total_votes),
            unicode(row.total_comments),
            _(row.domain),
            _(row.state),
            (xlwt.Formula(u'HYPERLINK("%s";"%s")' % (idea_url, idea_url)),
             link_style),
            u'%s %s' % (row.fi_firstname, row.fi_lastname) if row.fi_uid else u'',
            u'%s %s' % (row.di_firstname, row.di_lastname) if row.di_uid else u'',
            row.benefit_department,
        ]

        if permission in ('dsig', 'developer'):
            row_data = row_data + [
                row.target_date.strftime(
                    '%d/%m/%Y') if row.target_date else '',
                row.goal,
            ]

            row_year_revenues = ['' for y in years_revenues]
            row_year_expenses = ['' for y in years_expenses]

            if row.revenues_first_year:
                index = years_revenues.index(row.revenues_first_year)
                row_year_revenues[index] = row.revenues_first_year_value

            if row.revenues_second_year:
                index = years_revenues.index(row.revenues_second_year)
                row_year_revenues[index] = row.revenues_second_year_value

            if row.expenses_first_year:
                index = years_expenses.index(row.expenses_first_year)
                row_year_expenses[index] = row.expenses_first_year_value

            if row.expenses_second_year:
                index = years_expenses.index(row.expenses_second_year)
                row_year_expenses[index] = row.expenses_second_year_value

            row_data = row_data + row_year_revenues + row_year_expenses
            row_data = row_data + [row.evaluation_impact]

        for col_index, data in enumerate(row_data):
            if hasattr(data, '__iter__'):
                ws.write(row_index, col_index, *data)
            else:
                ws.write(row_index, col_index, data)
        row_index += 1

    # saves it in a memory buffer
    stream = StringIO()
    wb.save(stream)
    content = stream.getvalue()
    stream.close()

    timestamp = datetime.now().strftime('%Y-%m-%d')
    filename = filename_prefix + '_' + timestamp + '.xls'

    return content, filename
