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

from eureka.domain.models import DomainData
from eureka.domain.repositories import IdeaRepository, UserRepository
from eureka.domain.services import get_workflow
from eureka.infrastructure.workflow.workflow import (
    process_event as wf_process_event,
    switching_actions, recommendation_actions
)
from eureka.tests import DatabaseEnabledTestCase


class TestWorkflow(DatabaseEnabledTestCase):
    def setUp(self):
        super(TestWorkflow, self).setUp()

        # create the profiles that will interact with the idea
        user_repository = UserRepository()
        self.facilitator = user_repository.facilitator
        self.developer = user_repository.developer
        self.admin = user_repository.admin
        self.author = user_repository.create(
            uid=u'author',
            email=u'author@email.com',
            firstname=u'John',
            lastname=u'Doe',
            position=u'author',
            fi=self.facilitator
        )

        # create an idea domain
        domain = DomainData(
            label=u'domain',
            rank=100,
            en_label=u'en',
            fr_label=u'fr',
        )

        # create an idea
        self.idea = IdeaRepository().create(
            title=u'Title',
            description=u'description',
            impact=u'impact',
            submitted_by=self.author,
            domain=domain
        )

    def process_event(self, from_user, event):
        wf_process_event(
            from_user,
            self.idea,
            event,
            comment=u'comment',
            di=self.developer.uid
        )

    def test_actions(self):

        def _available_events(user):
            actions = (
                switching_actions(user, self.idea)
                + recommendation_actions(user, self.idea)
            )
            return [item[1] for item in actions]

        WFEvents = get_workflow().WFEvents
        # submit the idea
        self.process_event(self.author, WFEvents.SUBMIT_EVENT)
        self.assertEqual(self.facilitator, self.idea.wf_context.assignated_fi)

        # here is the scenario that we're going to run
        scenario = (
            (self.facilitator, WFEvents.ASK_INFORMATIONS_EVENT),
            (self.author, WFEvents.SUBMIT_EVENT),
            (self.facilitator, WFEvents.SEND_DI_EVENT),
            (self.developer, WFEvents.REFUSE_EVENT),
            (self.developer, WFEvents.REOPEN_EVENT),
            (self.developer, WFEvents.APPROVAL_EVENT),
            (self.admin, WFEvents.DISTURBING_IDEA_EVENT),
            (self.admin, WFEvents.NOT_DISTURBING_IDEA_EVENT),
            (self.admin, WFEvents.SELECT_EVENT),
            (self.admin, WFEvents.SEND_PROJECT_EVENT),
            (self.admin, WFEvents.SEND_PROTOTYPE_EVENT),
            (self.admin, WFEvents.EXTEND_EVENT),
        )

        for user, event in scenario:
            self.assertIn(event, _available_events(user))
            self.process_event(user, event)
