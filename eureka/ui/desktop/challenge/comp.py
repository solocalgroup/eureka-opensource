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

from nagare import component

from eureka.domain import queries
from eureka.infrastructure.urls import get_url_service
from eureka.domain.repositories import ChallengeRepository
from eureka.infrastructure import event_management, registry


class Challenge(object):
    def __init__(self, parent, challenge_id):
        # FIXME: late import to avoid circular dependencies problem
        from eureka.ui.desktop.idea import SubmitIdeaBox
        event_management._register_listener(parent, self)
        self.challenge_id = challenge_id
        self.challenge_repository = ChallengeRepository()
        self.submit_idea_box = component.Component(SubmitIdeaBox(self))
        self._ideas = None

        if not self.challenge:
            raise ValueError('Invalid challenge id')

    @property
    def challenge(self):
        return self.challenge_repository.get_by_id(self.challenge_id)

    @property
    def challenge_url(self):
        return get_url_service().expand_url(['challenge', self.challenge.id])

    @property
    def challenge_ideas_url(self):
        return get_url_service().expand_url(['challenge_ideas', self.challenge.id])

    @property
    def ideas(self):  # lazy initialization
        if not self._ideas:
            self._ideas = self.create_idea_pager()
        return self._ideas

    def create_idea_pager(self):
        """Get an idea pager that show ideas in this challenge"""
        # FIXME: late import to avoid circular dependencies problem
        from eureka.ui.desktop.idea import IdeaPager
        q = queries.get_published_challenge_ideas(self.challenge_id)
        pager = IdeaPager(self, q)
        pager.specific_challenge()
        return pager
