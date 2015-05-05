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
import glob
import os

from nagare import component
from nagare.i18n import _

from eureka.infrastructure.urls import get_url_service
from eureka.infrastructure.filesystem import get_fs_service
from eureka.infrastructure import event_management
from eureka.infrastructure.content_types import excel_response
from eureka.infrastructure.xls_renderer import XLSRenderer
from eureka.ui.desktop.dashboard import Dashboard, MostLikedComments
from .articles import ArticlesAdmin
from .users import UserAdmin, FIAdmin, DIAdmin
from .points import PointsAdmin
from .challenges import ChallengesAdmin
from .polls import PollsAdmin


class Administration(object):
    def __init__(self, parent, configuration,
                 email_unique=True, can_delete_users=False):
        self.parent = parent
        self.configuration = configuration
        self.email_unique = email_unique
        self.can_delete_users = can_delete_users
        self.mobile_access = configuration['mobile_version']['enabled']
        self.content = component.Component(None)

    def _show(self, o, model=0):
        event_management._register_listener(self.parent, o)
        # not a call because of the urls
        self.content.becomes(o, model).on_answer(
            lambda v: self.content.becomes(None))

    def show_dashboard(self):
        self._show(Dashboard(self.parent, self.configuration['dashboard']))

    def show_users(self):
        self._show(UserAdmin(
            email_unique=self.email_unique,
            can_delete_users=self.can_delete_users,
            mobile_access=self.mobile_access
        ))

    def show_fis(self):
        self._show(FIAdmin())

    def show_dis(self):
        self._show(DIAdmin())

    def show_points(self):
        self._show(PointsAdmin())

    def show_challenges(self):
        self._show(ChallengesAdmin(self.mobile_access))

    def show_articles(self):
        self._show(ArticlesAdmin(self.configuration))

    def show_polls(self):
        self._show(PollsAdmin())

    def last_board_export(self):
        board_dir = get_fs_service().expand_path(['board'])

        if not os.path.exists(board_dir):
            return None, None

        zip_files = sorted(glob.glob(os.path.join(board_dir, '*.zip')))
        if not zip_files:
            return None, None

        last_export_filename = os.path.basename(zip_files[-1])
        date_string = os.path.splitext(last_export_filename)[0].split('_')[1]
        date = datetime.strptime(date_string, '%Y%m%d')
        url = get_url_service().expand_url(['board', last_export_filename])
        return url, date

    def show_most_liked_comments(self):
        renderer = XLSRenderer()
        now = datetime.now()
        filename = now.strftime(_(u'eureka_most_liked_comments_week_%U_%Y.xls'))
        MostLikedComments().render(renderer, now, 500)
        raise excel_response(renderer.get_content(), filename)
