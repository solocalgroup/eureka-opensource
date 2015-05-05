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

from datetime import datetime

from nagare import editor
from nagare.i18n import _, _L

from eureka.domain.models import RoleType
from eureka.domain.services import get_search_engine
from eureka.infrastructure import event_management
from eureka.infrastructure.xls_renderer import XLSRenderer
from eureka.infrastructure.content_types import excel_response
from eureka.infrastructure.tools import fix_filename
from eureka.infrastructure.cache import cached
from eureka.ui.desktop.pager import Pager


class UserPager(Pager):
    def __init__(self, parent, query, batch_size=10):
        super(UserPager, self).__init__(query, batch_size)
        event_management._register_listener(parent, self)

    def change_batch_size(self, value):
        self.batch_size = int(value)

    def export_xls(self, filename=None, title=_(u'Users')):
        renderer = XLSRenderer()
        self.render_xls(renderer, title)
        timestamp = datetime.now().date().isoformat()
        filename = filename or '%s-%s.xls' % (timestamp, fix_filename(title))
        raise excel_response(renderer.get_content(), filename)

    def render_xls(self, r, sheet_title=None, sheet_name=_(u'Users')):
        with r.sheet(sheet_name):
            headings = (_(u"Login"),
                        _(u"First name"),
                        _(u"Last name"),
                        _(u"Email"),
                        _(u"Corporation"),
                        _(u"Direction"),
                        _(u"Service"),
                        _(u"Site"),
                        _(u"Position"),
                        _(u"Office phone"),
                        _(u"Mobile phone"),
                        _(u"Acquired points"),
                        _(u"Spent points"),
                        _(u"Status"),
                        _(u"Enabled"),
                        _(u"Incorporated"),
                        _(u"Facilitator"))
            last_idx = len(headings) - 1

            if sheet_title:
                r << r.row()
                with r.row:
                    r << r.cell(sheet_title, colspan=len(headings), style=r.Style.Heading1)
                r << r.row()

            with r.row:
                headings_style = r.Style.ColumnHeading + r.Style.VerticalAlignCenter + r.Style.Wrap + r.Background.LightYellow + r.Border.TopMedium + r.Border.BottomMedium
                for idx, heading in enumerate(headings):
                    if idx == 0:
                        style = r.Border.LeftMedium
                    elif idx == last_idx:
                        style = r.Border.RightMedium + r.Border.Left
                    else:
                        style = r.Border.Left
                    r << r.cell(heading, style=style + headings_style)

            for row_index, user in enumerate(self.get_query()):
                line_style = r.Background.PaleBlue if not (row_index % 2) else ''
                line_style += r.Border.Bottom
                with r.row:
                    values = (user.uid,
                              user.firstname,
                              user.lastname,
                              user.email,
                              user.corporation.label,
                              user.direction.label,
                              user.service.label,
                              user.site.label,
                              user.position,
                              user.work_phone,
                              user.mobile_phone,
                              user.acquired_points,
                              user.spent_points,
                              user.status_level_label,
                              u'X' if user.enabled else u'',
                              u'X' if user.incorporated else u'',
                              u'X' if any(r for r in user.roles if r.type == RoleType.Facilitator) else u'')

                    for idx, value in enumerate(values):
                        if idx == 0:
                            style = r.Border.LeftMedium
                        elif idx == last_idx:
                            style = r.Border.RightMedium + r.Border.Left
                        else:
                            style = r.Border.Left
                        r << r.cell(value, style=line_style + style)

            with r.row:
                for __ in range(len(headings)):
                    r << r.cell('', style=r.Border.TopMedium)


class UserBrowser(UserPager):
    # (search field, label) pairs, in display order
    SEARCH_FIELDS = (
        ("firstname", _L(u"First name")),
        ("lastname", _L(u"Last name")),
        ("competencies", _L(u"Skills")),
        ("position", _L(u"Position")),
        ("business_unit", _L(u"Business Unit")),
        ("text", _L(u"All")),
    )

    def __init__(self, parent, pattern, batch_size=10):
        super(UserBrowser, self).__init__(parent, None, batch_size)
        self.pattern = pattern
        self.search_field = editor.Property("text")

    def count(self):
        field = self.search_field.value
        if not field:
            return 0

        pattern = self.pattern
        return self._search_results_count(pattern, field)

    def get_pager_elements(self):
        field = self.search_field.value
        if not field:
            return []

        pattern = self.pattern
        return self._search_results(pattern, field, start=self.start, rows=self.batch_size)

    @cached
    def _search_results_count(self, pattern, field):
        if not pattern:
            return 0
        return get_search_engine().search('user', pattern, rows=0, default_field=field)[1]

    @cached
    def _search_results(self, pattern, field, start=0, rows=200):
        if not pattern:
            return []
        return get_search_engine().search('user', pattern, start=start, rows=rows, default_field=field)[0]

    def get_results_counts_per_field(self):
        pattern = self.pattern
        return dict((field, self._search_results_count(pattern, field))
                    for field, __ in self.SEARCH_FIELDS)
