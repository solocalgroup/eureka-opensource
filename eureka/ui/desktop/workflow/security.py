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

from eureka.domain.services import get_workflow
import peak.rules
from eureka.infrastructure.security import Rules
from .evaluation import EvaluationMenu
from .comp import WorkflowMenu, IdeaWFContext, IdeaWFComment


@peak.rules.when(Rules.has_permission, "perm == 'show_menu'")
def has_permission_show_menu(self, user, perm, (name, subject)):
    has_actions = getattr(subject, 'actions', True)
    return bool(has_actions)


@peak.rules.when(Rules.has_permission, "perm == 'view' and isinstance(subject, EvaluationMenu)")
def has_permission_view_evaluation_menu(self, user, perm, subject):
    if not user:
        return False

    user = user.entity
    idea = subject.idea
    state = subject.state

    if user.is_developer(idea) and state in get_workflow().get_study_states():
        return True

    return user.is_dsig()


@peak.rules.when(Rules.has_permission, "perm == 'view' and isinstance(subject, WorkflowMenu)")
def has_permission_view_workflow_menu(self, user, perm, subject):
    if not user:
        return False

    user = user.entity
    idea = subject.idea

    if user in idea.authors or user.is_dsig() or user.is_facilitator(idea) or user.is_developer(idea):
        return True

    return False


@peak.rules.when(Rules.has_permission, "perm == 'view_di' and isinstance(subject, IdeaWFContext)")
def has_permission_view_di_wf_context(self, user, perm, subject):
    if not user:
        return False

    user = user.entity
    idea = subject.idea
    return user.is_dsig() or user.is_facilitator(idea) or user.is_developer(idea)


@peak.rules.when(Rules.has_permission, "perm == 'view_di' and isinstance(subject, IdeaWFComment)")
def has_permission_view_di_wf_comment(self, user, perm, subject):
    if not user:
        return False

    user = user.entity
    idea = subject.idea
    return user.is_dsig() or user.is_facilitator(idea) or user.is_developer(idea)


@peak.rules.when(Rules.has_permission, "perm == 'edit_comment' and isinstance(subject, IdeaWFComment)")
def has_permission_edit_comment_wf_comment(self, user, perm, subject):
    if not user:
        return False

    user = user.entity
    return user.is_dsig()
