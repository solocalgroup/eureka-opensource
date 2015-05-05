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

from peak import rules

from nagare.i18n import _

from .workflow import WFEvents, WFStates, get_refused_states

from eureka.infrastructure.workflow.workflow import _permission, _switching_actions, _recommendation_actions


@rules.when(_switching_actions, "permission in ('dsig', 'facilitator') and state == WFStates.FI_NORMALIZE_STATE")
def _switching_actions_in_fi_normalize_state(permission, state):
    return [(_(u'Ask the author for further information'), WFEvents.ASK_INFORMATIONS_EVENT),
            (_(u'Send to the developer'), WFEvents.SEND_DI_EVENT),
            (_(u'Refuse the idea'), WFEvents.REFUSE_EVENT),
            (_(u'Mark the idea as disturbing'), WFEvents.DISTURBING_IDEA_EVENT)]


@rules.when(_switching_actions, "permission in ('dsig', 'author') and state == WFStates.AUTHOR_NORMALIZE_STATE")
def _switching_actions_in_author_normalize_state(permission, state):
    return [(_(u'Finalize and send to the facilitator'), WFEvents.SUBMIT_EVENT),
            (_(u'Mark the idea as disturbing'), WFEvents.DISTURBING_IDEA_EVENT)]


@rules.when(_switching_actions, "permission in ('dsig', 'developer') and state == WFStates.DI_APPRAISAL_STATE")
def _switching_actions_in_di_appraisal_state(permission, state):
    """
    In this case actions are split in 2 folds: actions and recommendations,
    this will disappear in a future release
    """
    return [(_(u'Ask the author for further information'), WFEvents.ASK_INFORMATIONS_EVENT),
            (_(u'Send to another developer'), WFEvents.SEND_DI_EVENT),
            (_(u'Mark the idea as disturbing'), WFEvents.DISTURBING_IDEA_EVENT)]


@rules.when(_switching_actions, "permission in ('dsig', 'author') and state == WFStates.RETURNED_BY_DI_STATE")
def _switching_actions_in_returned_by_di_state(permission, state):
    return [(_(u'Finalize and send back to the developer'), WFEvents.SUBMIT_EVENT),
            (_(u'Mark the idea as disturbing'), WFEvents.DISTURBING_IDEA_EVENT)]


@rules.when(_switching_actions, "permission == 'dsig' and state == WFStates.DI_APPROVED_STATE")
def _switching_actions_in_di_approved_state(permission, state):
    return [(_(u'Select the idea'), WFEvents.SELECT_EVENT),
            (_(u'Refuse the idea'), WFEvents.REFUSE_EVENT),
            (_(u'Mark the idea as disturbing'), WFEvents.DISTURBING_IDEA_EVENT)]


@rules.when(_switching_actions, "permission == 'dsig' and state == WFStates.SELECTED_STATE")
def _switching_actions_in_selected_state(permission, state):
    return [(_(u'Set up the implementation'), WFEvents.SEND_PROJECT_EVENT),
            (_(u'Refuse the idea'), WFEvents.REFUSE_EVENT),
            (_(u'Mark the idea as disturbing'), WFEvents.DISTURBING_IDEA_EVENT)]


@rules.when(_switching_actions, "permission == 'dsig' and state == WFStates.PROJECT_STATE")
def _switching_actions_in_project_state(permission, state):
    return [(_(u'Set up the pilot'), WFEvents.SEND_PROTOTYPE_EVENT),
            (_(u'Refuse the idea'), WFEvents.REFUSE_EVENT),
            (_(u'Mark the idea as disturbing'), WFEvents.DISTURBING_IDEA_EVENT)]


@rules.when(_switching_actions, "permission == 'dsig' and state == WFStates.PROTOTYPE_STATE")
def _switching_actions_in_prototype_state(permission, state):
    return [(_(u'Deploy the idea'), WFEvents.EXTEND_EVENT),
            (_(u'Refuse the idea'), WFEvents.REFUSE_EVENT),
            (_(u'Mark the idea as disturbing'), WFEvents.DISTURBING_IDEA_EVENT)]


@rules.when(_switching_actions, "permission in ('dsig', 'developer') and state == WFStates.DSIG_BASKET_STATE")
def _switching_actions_in_dsig_basket_state(permission, state):
    return [(_(u'Unmark the idea as disturbing'), WFEvents.NOT_DISTURBING_IDEA_EVENT)]


@rules.when(_switching_actions, "permission in ('dsig', 'developer') and state in get_refused_states()")
def _switching_actions_in_refused_states(permission, idea):
    return [(_(u'Reopen this idea'), WFEvents.REOPEN_EVENT)]


@rules.when(_recommendation_actions, "permission in ('dsig', 'developer') and state == WFStates.DI_APPRAISAL_STATE")
def _recommendation_actions_in_di_appraisal_state(permission, state):
    return [(_(u'Refuse the idea'), WFEvents.REFUSE_EVENT),
            (_(u'Recommend the idea'), WFEvents.APPROVAL_EVENT)]
