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

from nagare.i18n import _L


class WFStates(object):
    INITIAL_STATE = u'INITIAL_STATE'
    DRAFT_STATE = u'DRAFT_STATE'
    FI_NORMALIZE_STATE = u'FI_NORMALIZE_STATE'
    AUTHOR_NORMALIZE_STATE = u'AUTHOR_NORMALIZE_STATE'
    DI_APPRAISAL_STATE = u'DI_APPRAISAL_STATE'
    RETURNED_BY_DI_STATE = u'RETURNED_BY_DI_STATE'
    DI_APPROVED_STATE = u'DI_APPROVED_STATE'
    SELECTED_STATE = u'SELECTED_STATE'
    PROJECT_STATE = u'PROJECT_STATE'
    PROTOTYPE_STATE = u'PROTOTYPE_STATE'
    EXTENDED_STATE = u'EXTENDED_STATE'
    FI_REFUSED_STATE = u'FI_REFUSED_STATE'
    PROTOTYPE_REFUSED_STATE = u'PROTOTYPE_REFUSED_STATE'
    DI_REFUSED_STATE = u'DI_REFUSED_STATE'
    PROJECT_REFUSED_STATE = u'PROJECT_REFUSED_STATE'
    SELECT_REFUSED_STATE = u'SELECT_REFUSED_STATE'
    APPROVAL_REFUSED_STATE = u'APPROVAL_REFUSED_STATE'
    DSIG_BASKET_STATE = u'DSIG_BASKET_STATE'


class WFEvents(object):
    DRAFT_EVENT = 'DRAFT_EVENT'
    SUBMIT_EVENT = 'SUBMIT_EVENT'
    ASK_INFORMATIONS_EVENT = 'ASK_INFORMATIONS_EVENT'
    SEND_DI_EVENT = 'SEND_DI_EVENT'
    REFUSE_EVENT = 'REFUSE_EVENT'
    APPROVAL_EVENT = 'APPROVAL_EVENT'
    SELECT_EVENT = 'SELECT_EVENT'
    SEND_PROJECT_EVENT = 'SEND_PROJECT_EVENT'
    SEND_PROTOTYPE_EVENT = 'SEND_PROTOTYPE_EVENT'
    EXTEND_EVENT = 'EXTEND_EVENT'
    DISTURBING_IDEA_EVENT = 'DISTURBING_IDEA_EVENT'
    NOT_DISTURBING_IDEA_EVENT = 'NOT_DISTURBING_IDEA_EVENT'
    REOPEN_EVENT = 'REOPEN_EVENT'


class WFSteps(object):
    NO_STEP = u'NO_STEP'
    SUBMITTED_STEP = u'SUBMITTED_STEP'
    STUDY_STEP = u'STUDY_STEP'
    SUGGESTED_STEP = u'SUGGESTED_STEP'
    SELECTED_STEP = u'SELECTED_STEP'
    PROJECT_STEP = u'PROJECT_STEP'
    PROTOTYPE_STEP = u'PROTOTYPE_STEP'
    EXTENDED_STEP = u'EXTENDED_STEP'


# Help Babel's messages extraction
TRANSLATED_STATES = (_L(u'AUTHOR_NORMALIZE_STATE'),
                     _L(u'DRAFT_STATE'),
                     _L(u'DSIG_BASKET_STATE'),
                     _L(u'PROTOTYPE_REFUSED_STATE'),
                     _L(u'APPROVAL_REFUSED_STATE'),
                     _L(u'DI_APPROVED_STATE'),
                     _L(u'PROTOTYPE_STATE'),
                     _L(u'DI_REFUSED_STATE'),
                     _L(u'EXTENDED_STATE'),
                     _L(u'RETURNED_BY_DI_STATE'),
                     _L(u'SELECT_REFUSED_STATE'),
                     _L(u'FI_REFUSED_STATE'),
                     _L(u'PROJECT_STATE'),
                     _L(u'PROJECT_REFUSED_STATE'),
                     _L(u'SELECTED_STATE'),
                     _L(u'DI_APPRAISAL_STATE'),
                     _L(u'FI_NORMALIZE_STATE'),
                     _L(u'INITIAL_STATE'))


TRANSLATED_STEPS = (_L(u'NO_STEP'),
                    _L(u'SUGGESTED_STEP'),
                    _L(u'EXTENDED_STEP'),
                    _L(u'STUDY_STEP'),
                    _L(u'SUBMITTED_STEP'),
                    _L(u'SELECTED_STEP'),
                    _L(u'PROJECT_STEP'),
                    _L(u'PROTOTYPE_STEP'))


def get_ordered_states():
    return [WFStates.DRAFT_STATE,
            WFStates.FI_NORMALIZE_STATE,
            WFStates.AUTHOR_NORMALIZE_STATE,
            WFStates.DI_APPRAISAL_STATE,
            WFStates.RETURNED_BY_DI_STATE,
            WFStates.DI_APPROVED_STATE,
            WFStates.SELECTED_STATE,
            WFStates.PROJECT_STATE,
            WFStates.PROTOTYPE_STATE,
            WFStates.EXTENDED_STATE,
            WFStates.FI_REFUSED_STATE,
            WFStates.PROTOTYPE_REFUSED_STATE,
            WFStates.DI_REFUSED_STATE,
            WFStates.PROJECT_REFUSED_STATE,
            WFStates.SELECT_REFUSED_STATE,
            WFStates.APPROVAL_REFUSED_STATE,
            ]


def get_published_states():
    return [WFStates.DI_APPRAISAL_STATE,
            WFStates.RETURNED_BY_DI_STATE,
            WFStates.DI_APPROVED_STATE,
            WFStates.SELECTED_STATE,
            WFStates.PROJECT_STATE,
            WFStates.PROTOTYPE_STATE,
            WFStates.EXTENDED_STATE,
            WFStates.PROTOTYPE_REFUSED_STATE,
            WFStates.DI_REFUSED_STATE,
            WFStates.PROJECT_REFUSED_STATE,
            WFStates.SELECT_REFUSED_STATE,
            WFStates.APPROVAL_REFUSED_STATE,
            ]


def get_fi_basket_states():
    return [WFStates.FI_NORMALIZE_STATE,
            WFStates.AUTHOR_NORMALIZE_STATE,
            WFStates.DI_APPRAISAL_STATE,
            WFStates.FI_REFUSED_STATE]


def get_di_basket_states():
    return [WFStates.DI_APPRAISAL_STATE,
            WFStates.RETURNED_BY_DI_STATE,
            WFStates.DI_APPROVED_STATE,
            WFStates.DI_REFUSED_STATE,
            WFStates.SELECTED_STATE,
            WFStates.PROJECT_STATE,
            WFStates.PROTOTYPE_STATE,
            WFStates.EXTENDED_STATE]


# utility states groups


def get_workflow_states():
    """
    Subset of states that excludes draft_state. Ideas in draft_state are not
    really in the workflow (i.e. all states that can be reached from step 1)
    """
    return [WFStates.FI_NORMALIZE_STATE,
            WFStates.AUTHOR_NORMALIZE_STATE,
            WFStates.DI_APPRAISAL_STATE,
            WFStates.RETURNED_BY_DI_STATE,
            WFStates.DI_APPROVED_STATE,
            WFStates.SELECTED_STATE,
            WFStates.PROJECT_STATE,
            WFStates.PROTOTYPE_STATE,
            WFStates.EXTENDED_STATE,
            WFStates.FI_REFUSED_STATE,
            WFStates.PROTOTYPE_REFUSED_STATE,
            WFStates.DI_REFUSED_STATE,
            WFStates.PROJECT_REFUSED_STATE,
            WFStates.SELECT_REFUSED_STATE,
            WFStates.APPROVAL_REFUSED_STATE,
            WFStates.DSIG_BASKET_STATE,
            ]


def get_chart_states():
    """
    Subset of states that is used to draw homepage chart.
    """
    return [WFStates.EXTENDED_STATE,
            WFStates.PROTOTYPE_STATE,
            WFStates.PROJECT_STATE,
            WFStates.SELECTED_STATE,
            ]


def get_di_handled_states():
    """
    Subset of states that includes all states that can be reached from step 2
    (a developer has been chosen).
    """
    return get_published_states()


def get_draft_states():
    """
    Pseudo state that gather all draft states
    """
    return [WFStates.DRAFT_STATE,
            ]


def get_refused_states():
    """
    Pseudo state that gather all refused states
    """
    return [WFStates.FI_REFUSED_STATE,
            WFStates.PROTOTYPE_REFUSED_STATE,
            WFStates.DI_REFUSED_STATE,
            WFStates.PROJECT_REFUSED_STATE,
            WFStates.SELECT_REFUSED_STATE,
            WFStates.APPROVAL_REFUSED_STATE,
            ]


def get_success_states():
    """
    Pseudo state that gather all positive states, that is states that are not refused
    """
    return [WFStates.FI_NORMALIZE_STATE,
            WFStates.AUTHOR_NORMALIZE_STATE,
            WFStates.DI_APPRAISAL_STATE,
            WFStates.RETURNED_BY_DI_STATE,
            WFStates.DI_APPROVED_STATE,
            WFStates.SELECTED_STATE,
            WFStates.PROJECT_STATE,
            WFStates.PROTOTYPE_STATE,
            WFStates.EXTENDED_STATE,
            ]


def get_progression_states():
    """
    Pseudo state that gather all states that can progress.
    """
    return get_success_states()[:-1]


def get_submitted_states():
    """
    Step 1 out of 7
    """
    return [WFStates.FI_NORMALIZE_STATE,
            WFStates.AUTHOR_NORMALIZE_STATE,
            ]


def get_study_states():
    """
    Step 2 out of 7
    """
    return [WFStates.DI_APPRAISAL_STATE,
            WFStates.RETURNED_BY_DI_STATE,
            ]


def get_approved_states():
    """
    Step 3 out of 7
    """
    return [WFStates.DI_APPROVED_STATE,
            ]


def get_selected_states():
    """
    Step 4 out of 7
    """
    return [WFStates.SELECTED_STATE,
            ]


def get_project_states():
    """
    Step 5 out of 7
    """
    return [WFStates.PROJECT_STATE,
            ]


def get_prototype_states():
    """
    Step 6 out of 7
    """
    return [WFStates.PROTOTYPE_STATE,
            ]


def get_extended_states():
    """
    Step 7 out of 7
    """
    return [WFStates.EXTENDED_STATE,
            ]


def get_progressing_ideas_states():
    return [WFStates.DI_APPROVED_STATE,
            WFStates.SELECTED_STATE,
            WFStates.PROJECT_STATE,
            WFStates.PROTOTYPE_STATE,
            WFStates.EXTENDED_STATE,
            WFStates.PROTOTYPE_REFUSED_STATE,
            WFStates.PROJECT_REFUSED_STATE,
            WFStates.SELECT_REFUSED_STATE,
            WFStates.APPROVAL_REFUSED_STATE,
            ]


def get_progressing_ideas_with_success_states():
    success_states = set(get_success_states())
    return [state for state in get_progressing_ideas_states() if state in success_states]


def get_proposed_ideas_states():
    return get_study_states() + get_approved_states() + get_selected_states()


def get_launched_ideas_states():
    return [WFStates.PROJECT_STATE,
            WFStates.PROTOTYPE_STATE,
            WFStates.EXTENDED_STATE,
            ]


def get_author_edit_states():
    """
    Subset of states in which author can edit the idea
    """
    return [WFStates.DRAFT_STATE,
            WFStates.FI_NORMALIZE_STATE,
            WFStates.AUTHOR_NORMALIZE_STATE,
            WFStates.RETURNED_BY_DI_STATE,
            ]
