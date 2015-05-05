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

import datetime

from nagare import component
from nagare.i18n import _

from eureka.infrastructure import event_management
from eureka.domain import models
from eureka.domain.repositories import ChallengeRepository
from eureka.domain.queries import get_published_challenge_ideas
from eureka.ui.common import ellipsize
from eureka.ui.common.tab import TabContainer
from eureka.ui.common.menu import Menu
from eureka.ui.desktop.challenge import Challenge
from eureka.ui.desktop.pager import InfinitePager
from eureka.ui.desktop.idea import IdeaPager, IdeasFilters


class ChallengePage(object):
    def __init__(self, parent, default_challenge_id=None):
        super(ChallengePage, self).__init__()
        self.parent = parent
        event_management._register_listener(parent, self)

        now = datetime.datetime.now()
        self.items = [(challenge.short_title or ellipsize(challenge.title, 35),
                       Challenge(parent, challenge.id)) for challenge in
                      self._challenges if challenge.is_active(now)]
        self.items = [(_(u'All challenges'), None)] + self.items
        self.menu = component.Component(
            Menu([label for label, challenge in self.items]),
            model='challenges')
        self.menu.on_answer(self.select_challenge)

        self.content = component.Component(None)
        self.current_challenge = component.Component(None)
        self.ordered = component.Component(None)
        self.filtered = component.Component(None)
        self.excel_exporter = component.Component(None)
        self.batch_size_changer = component.Component(None)
        self.idea_counter = component.Component(None)

        for index, (label, challenge) in enumerate(self.items):
            if challenge and challenge.challenge_id == default_challenge_id:
                self.select_challenge(index)
                break

        if not self.menu().selected():
            # challenge selected fallback to first one or all
            if len(self.items) > 1:
                show_challenge = False
                self.select_challenge(1)
            else:
                show_challenge = True
                self.select_challenge(0)

    def select_challenge(self, index):

        if index:
            if self.filtered():
                self.filtered().show_challenge = False
            challenge = self.items[index][1]
            challenge_id = challenge.challenge_id
            pager = self._create_pager_all_challenges(self.parent,
                                                      challenge_id)
            self.current_challenge.becomes(challenge, model='short_excerpt')
            show_challenge = False
        else:
            if self.filtered():
                self.filtered().show_challenge = True
            pager = self._create_pager_all_challenges(self.parent)
            self.current_challenge.becomes(None)
            show_challenge = True

        pager = InfinitePager(component.Component(pager, model='ideas-list'))
        self.content.becomes(pager, model='list')

        self.filtered.becomes(IdeasFilters(self.content, show_challenge=show_challenge))
        self.ordered.becomes(self.content().pager, model='ordered')
        self.excel_exporter.becomes(self.content().pager, 'xls_export')
        self.batch_size_changer.becomes(self.content().pager, 'batch_size')
        self.idea_counter.becomes(self.content().pager, 'count')

        self.menu().selected(index)

    def _create_pager_all_challenges(self, parent, challenge_id=None):
        q = get_published_challenge_ideas(challenge_id)
        pager = IdeaPager(parent, q)
        pager.all_challenges()
        return pager

    @property
    def _challenges(self):
        """Return all the active challenges."""
        # return list(ChallengeRepository().get_by_active_at_date(now))
        return list(ChallengeRepository().get_all())

    @property
    def selected_challenge(self):
        """Returns the selected challenge or ``None``."""
        idx = self.content().selected_tab
        if idx > 0:
            challenge = self._challenges[
                idx - 1]  # The real index is idx-1 since we inserted an "All challenges" element
            return challenge.id

    def with_login(self, action):
        event_management._emit_signal(self, "WITH_LOGIN", action)
