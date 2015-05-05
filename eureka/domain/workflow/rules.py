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
from eureka.infrastructure.workflow.workflow import apply_rule

import peak.rules

from .workflow import get_refused_states, WFStates, WFEvents
from eureka.infrastructure.workflow.voucher import PointEvent


@peak.rules.when(apply_rule,
                 "state == WFStates.INITIAL_STATE and "
                 "event == WFEvents.DRAFT_EVENT")
def apply_rule(idea, state, event, context, *args, **kw):
    return WFStates.DRAFT_STATE


@peak.rules.when(apply_rule,
                 "state == WFStates.INITIAL_STATE and "
                 "event == WFEvents.SUBMIT_EVENT")
def apply_rule(idea, state, event, context, *args, **kw):
    context.assignated_fi = idea.submitted_by.fi

    for user in idea.authors:
        user.process_point_event(PointEvent.SUBMIT_IDEA)

    return WFStates.FI_NORMALIZE_STATE


@peak.rules.when(apply_rule,
                 "state == WFStates.DRAFT_STATE and "
                 "event == WFEvents.SUBMIT_EVENT")
def apply_rule(idea, state, event, context, *args, **kw):
    context.assignated_fi = idea.submitted_by.fi

    for user in idea.authors:
        user.process_point_event(PointEvent.SUBMIT_IDEA)

    return WFStates.FI_NORMALIZE_STATE


@peak.rules.when(apply_rule,
                 "state == WFStates.FI_NORMALIZE_STATE and "
                 "event == WFEvents.SEND_DI_EVENT")
def apply_rule(idea, state, event, context, *args, **kw):
    from eureka.domain.queries import get_published_challenge_ideas
    from eureka.domain.repositories import UserRepository

    # Affect to DI
    di_uid = kw['di']
    di = UserRepository().get_by_uid(di_uid) or UserRepository().developer
    context.assignated_di = di
    context.publication_date = datetime.now()

    # Give points to creator
    for user in idea.authors:
        user.process_point_event(PointEvent.PUBLISH_IDEA, idea=idea)

        if (idea.challenge is not None and
           [e for e in get_published_challenge_ideas(idea.challenge.id)()] == []):
            user.process_point_event(PointEvent.PUBLISH_CHALLENGE_FIRST_IDEA, idea=idea)

        idea.show_creator = True

    return WFStates.DI_APPRAISAL_STATE


@peak.rules.when(apply_rule,
                 "state == WFStates.FI_NORMALIZE_STATE and "
                 "event == WFEvents.REFUSE_EVENT")
def apply_rule(idea, state, event, context, *args, **kw):
    return WFStates.FI_REFUSED_STATE


@peak.rules.when(apply_rule,
                 "state == WFStates.FI_NORMALIZE_STATE and "
                 "event == WFEvents.ASK_INFORMATIONS_EVENT")
def apply_rule(idea, state, event, context, *args, **kw):
    return WFStates.AUTHOR_NORMALIZE_STATE


@peak.rules.when(apply_rule,
                 "state == WFStates.AUTHOR_NORMALIZE_STATE and "
                 "event == WFEvents.SUBMIT_EVENT")
def apply_rule(idea, state, event, context, *args, **kw):
    return WFStates.FI_NORMALIZE_STATE


@peak.rules.when(apply_rule,
                 "state == WFStates.RETURNED_BY_DI_STATE and "
                 "event == WFEvents.SUBMIT_EVENT")
def apply_rule(idea, state, event, context, *args, **kw):
    return WFStates.DI_APPRAISAL_STATE


@peak.rules.when(apply_rule,
                 "state == WFStates.DI_APPRAISAL_STATE and "
                 "event == WFEvents.REFUSE_EVENT")
def apply_rule(idea, state, event, context, *args, **kw):
    return WFStates.DI_REFUSED_STATE


@peak.rules.when(apply_rule,
                 "state == WFStates.DI_APPRAISAL_STATE and "
                 "event == WFEvents.ASK_INFORMATIONS_EVENT")
def apply_rule(idea, state, event, context, *args, **kw):
    return WFStates.RETURNED_BY_DI_STATE


@peak.rules.when(apply_rule,
                 "state == WFStates.DI_APPRAISAL_STATE and "
                 "event == WFEvents.APPROVAL_EVENT")
def apply_rule(idea, state, event, context, *args, **kw):
    context.recommendation_date = datetime.now()

    # Give points to creator
    for user in idea.authors:
        user.process_point_event(PointEvent.APPROVAL, idea=idea)

    return WFStates.DI_APPROVED_STATE


@peak.rules.when(apply_rule,
                 "state == WFStates.DI_APPROVED_STATE and "
                 "event == WFEvents.SELECT_EVENT")
def apply_rule(idea, state, event, context, *args, **kw):
    context.recommendation_date = datetime.now()

    # Give points to creator
    for user in idea.authors:
        user.process_point_event(PointEvent.SELECT_IDEA, idea=idea)
    return WFStates.SELECTED_STATE


@peak.rules.when(apply_rule,
                 "state == WFStates.DI_APPROVED_STATE and "
                 "event == WFEvents.REFUSE_EVENT")
def apply_rule(idea, state, event, context, *args, **kw):
    return WFStates.APPROVAL_REFUSED_STATE


@peak.rules.when(apply_rule,
                 "state == WFStates.DI_APPRAISAL_STATE and "
                 "event == WFEvents.SEND_DI_EVENT")
def apply_rule(idea, state, event, context, *args, **kw):
    from eureka.domain.repositories import UserRepository
    di_uid = kw['di']
    di = UserRepository().get_by_uid(di_uid) or UserRepository().developer
    context.assignated_di = di

    return WFStates.DI_APPRAISAL_STATE


@peak.rules.when(apply_rule,
                 "state == WFStates.SELECTED_STATE and "
                 "event == WFEvents.SEND_PROJECT_EVENT")
def apply_rule(idea, state, event, context, *args, **kw):
    for user in idea.authors:
        user.process_point_event(PointEvent.SEND_PROJECT_IDEA, idea=idea)

    return WFStates.PROJECT_STATE


@peak.rules.when(apply_rule,
                 "state == WFStates.SELECTED_STATE and "
                 "event == WFEvents.REFUSE_EVENT")
def apply_rule(idea, state, event, context, *args, **kw):
    return WFStates.SELECT_REFUSED_STATE


@peak.rules.when(apply_rule,
                 "state == WFStates.PROJECT_STATE and "
                 "event == WFEvents.SEND_PROTOTYPE_EVENT")
def apply_rule(idea, state, event, context, *args, **kw):
    for user in idea.authors:
        user.process_point_event(PointEvent.SEND_PROTOTYPE_IDEA, idea=idea)

    return WFStates.PROTOTYPE_STATE


@peak.rules.when(apply_rule,
                 "state == WFStates.PROJECT_STATE and "
                 "event == WFEvents.REFUSE_EVENT")
def apply_rule(idea, state, event, context, *args, **kw):
    return WFStates.PROJECT_REFUSED_STATE


@peak.rules.when(apply_rule,
                 "state == WFStates.PROTOTYPE_STATE and "
                 "event == WFEvents.EXTEND_EVENT")
def apply_rule(idea, state, event, context, *args, **kw):
    for user in idea.authors:
        user.process_point_event(PointEvent.EXTEND_IDEA, idea=idea)

    return WFStates.EXTENDED_STATE


@peak.rules.when(apply_rule,
                 "state == WFStates.PROTOTYPE_STATE and "
                 "event == WFEvents.REFUSE_EVENT")
def apply_rule(idea, state, event, context, *args, **kw):
    return WFStates.PROTOTYPE_REFUSED_STATE


@peak.rules.when(apply_rule,
                 "(state == WFStates.DRAFT_STATE or "
                 "state == WFStates.FI_NORMALIZE_STATE or "
                 "state == WFStates.AUTHOR_NORMALIZE_STATE or "
                 "state == WFStates.DI_APPRAISAL_STATE or "
                 "state == WFStates.RETURNED_BY_DI_STATE or "
                 "state == WFStates.DI_APPROVED_STATE or "
                 "state == WFStates.SELECTED_STATE or "
                 "state == WFStates.PROJECT_STATE or "
                 "state == WFStates.PROTOTYPE_STATE or "
                 "state == WFStates.EXTENDED_STATE or "
                 "state == WFStates.FI_REFUSED_STATE or "
                 "state == WFStates.PROTOTYPE_REFUSED_STATE or "
                 "state == WFStates.DI_REFUSED_STATE or "
                 "state == WFStates.PROJECT_REFUSED_STATE or "
                 "state == WFStates.SELECT_REFUSED_STATE or "
                 "state == WFStates.APPROVAL_REFUSED_STATE )and "
                 "event == WFEvents.DISTURBING_IDEA_EVENT")
def apply_rule(idea, state, event, context, *args, **kw):
    return WFStates.DSIG_BASKET_STATE


@peak.rules.when(apply_rule,
                 "(state == WFStates.DSIG_BASKET_STATE and"
                 " event == WFEvents.NOT_DISTURBING_IDEA_EVENT)")
def apply_rule(idea, state, event, context, *args, **kw):
    return context.comments[-1].from_state.label


@peak.rules.when(apply_rule, "event == WFEvents.REOPEN_EVENT")
def apply_rule(idea, state, event, context, *args, **kw):
    previous_opened_state = None
    for comment in reversed(context.comments):
        if comment.from_state.label not in get_refused_states():
            previous_opened_state = comment.from_state.label
            break
    if previous_opened_state is not None:
        return previous_opened_state
    else:
        raise ValueError('Could not find a previous opened state for idea #%s' % idea.id)
