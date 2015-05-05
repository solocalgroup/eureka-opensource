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
from operator import itemgetter

from nagare import security

from eureka.domain.models import VotePollData
from eureka.domain.repositories import PollRepository


class Poll(object):
    def __init__(self, poll_id):
        self.poll_id = poll_id

    @property
    def poll(self):
        return PollRepository().get_by_id(self.poll_id)

    @property
    def user(self):
        current_user = security.get_user()
        if current_user:
            return current_user.entity

    def should_display_date(self):
        return True

    def is_poll_finished(self):
        return datetime.now() >= self.poll.end_date  # not included

    def has_voted(self):
        return self._find_votes(self.user)

    def _find_votes(self, user):
        for vote in user.votes_for_polls:
            if vote.choice in self.poll.choices:
                return True
        return False

    def _find_choice(self, id):
        for choice in self.poll.choices:
            if choice.id == id:
                return choice
        return None

    def add_vote(self, choice_id):
        choice = self._find_choice(choice_id)
        VotePollData(choice=choice, user=self.user)

    def commit(self, choices):
        if not choices and self.has_voted():
            return False

        for choice in choices:
            self.add_vote(choice)
        return True

    def get_votes_ratios_per_choice(self):
        votes_count_per_choice = [(choice, len(choice.votes)) for choice in self.poll.choices]
        total_votes_count = sum(map(itemgetter(1), votes_count_per_choice))  # compute the sum of vote counts
        for choice, vote_count in votes_count_per_choice:
            ratio = (vote_count * 100 / total_votes_count) if total_votes_count else 0
            yield choice, ratio

    @property
    def nb_voters(self):
        # unique voters
        unique_users = set(vote.user for vote in self.poll.votes)
        return len(unique_users)
