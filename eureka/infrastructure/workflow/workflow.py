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

from datetime import timedelta, datetime
from eureka.domain.services import get_workflow


def _permission(user, idea):
    if not user:
        return None

    if user.is_dsig():
        return 'dsig'

    if user.is_developer(idea):
        return 'developer'

    if user.is_facilitator(idea):
        return 'facilitator'

    if user in idea.authors:
        return 'author'

    return None


def switching_actions(user, idea):
    # The list of the available actions depends on the permission of the user
    # on the idea and the state of the idea
    permission = _permission(user, idea)
    state = idea.wf_context.state.label
    return _switching_actions(permission, state)


def _switching_actions(permission, state):
    # By default, no action is available
    return []


def recommendation_actions(user, idea):
    """For all states return dict of allowed actions (button name, event)"""
    return _recommendation_actions(
        _permission(user, idea),
        idea.wf_context.state.label
    )


def _recommendation_actions(permission, state):
    return []


def apply_rule(idea, state, event, context, *args, **kw):
    """ Return next state for an event on a current state

    Common method return current state + 1

    In:
      - `idea`   -- current idea
      - `state`   -- current state
      - `event`   -- event
      - `context` -- idea context workflow
    Return:
      - next state
    """
    return state


def send_notifications(from_user, idea, state, event, new_state,
                       context, comment, notify, **kw):
    """Send notifications for the state change (workflow event)"""
    pass


def get_reminder_alert(new_state):
    if new_state in get_workflow().get_progression_states():
        time_to_wait = timedelta(days=60)  # 2 months
        return datetime.now() + time_to_wait
    else:
        return None


def process_event(from_user, idea, event, comment=None, notify=None, **kwargs):
    """
    Progress method for workflow.

    In this method:
      - changes state
      - send notification
      - add a comment on transition

    In:
      - `idea` -- current idea  (instance of IdeaData)
      - `state` -- current state  (string)
      - `event` --  event  (string)
      - `context` -- idea context  (instance of IdeaWFContextData)
    Return:
      - next state or raise a WorkflowError
    """
    context = idea.wf_context
    state_label = context.state.label

    # calculate the new state
    new_state = apply_rule(idea, state_label, event, context, **kwargs)

    # send the appropriate notifications
    send_notifications(from_user, idea, state_label, event, new_state, context,
                       comment, notify or (lambda m: None), **kwargs)

    idea.unchanged_state_reminder_date = get_reminder_alert(new_state)

    # add wf comment (state changes history)
    context.add_comment(from_user, comment, state_label, new_state)

    # change state
    # FIXME: use a setter instead
    context.set_state(new_state)

    return new_state
