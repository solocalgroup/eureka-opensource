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

import peak.rules

from nagare import security

from eureka.domain.services import get_workflow
from eureka.domain.models import IdeaData  # @UnusedImport - needed by peak.rules
from eureka.infrastructure.security import Rules
from .comp import Idea  # @UnusedImport - needed by peak.rules
from .pager import IdeaPager  # @UnusedImport - needed by peak.rules
from .editor import IdeaEditor, IdeaUpdater  # @UnusedImport - needed by peak.rules


# -------------
# Idea
@peak.rules.when(Rules.has_permission,
                 "perm == 'view_idea' and isinstance(subject, Idea)")
def has_permission_view_idea(self, user, perm, subject):
    user = user.entity if user else None
    idea = subject.i
    state = idea.wf_context.state.label
    workflow = get_workflow()
    if state in workflow.get_published_states():
        return True

    if not user:
        return False

    if user in idea.authors:
        return True

    if user.is_facilitator(idea) and state in workflow.get_submitted_states():
        return True

    if idea.proxy_submitter and user.uid == idea.proxy_submitter.uid:
        return True

    return user.is_dsig()


@peak.rules.when(Rules.has_permission,
                 "perm == 'edit_idea' and isinstance(subject, Idea)")
def has_permission_edit_idea(self, user, perm, subject):
    if not user:
        return False

    user = user.entity
    idea = subject.i
    state = idea.wf_context.state.label
    workflow = get_workflow()

    if user in idea.authors and state in workflow.get_author_edit_states():
        return True

    if user.is_facilitator(idea) and state in workflow.get_submitted_states():
        return True

    if idea.proxy_submitter and user.uid == idea.proxy_submitter.uid:
        return True

    return user.is_dsig()


@peak.rules.when(Rules.has_permission,
                 "perm == 'report_duplicate' and isinstance(subject, Idea)")
def has_permission_report_duplicate(self, user, perm, subject):
    if not user:
        return False
    return True


@peak.rules.when(Rules.has_permission,
                 "perm == 'delete_idea' and isinstance(subject, Idea)")
def has_permission_delete_idea(self, user, perm, subject):
    if not user:
        return False

    user = user.entity
    idea = subject.i
    state = idea.wf_context.state.label
    workflow = get_workflow()

    if state in workflow.get_draft_states():
        return True

    return user.is_dsig()


@peak.rules.when(Rules.has_permission,
                 "perm == 'view_moderated_comments' and isinstance(subject, Idea)")
def has_permission_view_moderated_comments(self, user, perm, subject):
    if not user:
        return False

    user = user.entity
    return user.is_dsig()


@peak.rules.when(Rules.has_permission,
                 "perm == 'submit_comment' and isinstance(subject, Idea)")
def has_permission_submit_comment(self, user, perm, subject):
    if not user:
        return True

    idea = subject.i
    state = idea.wf_context.state.label
    workflow = get_workflow()

    if state in workflow.get_refused_states():
        return False

    return True


@peak.rules.when(Rules.has_permission,
                 "perm == 'vote_idea' and isinstance(subject, Idea)")
def has_permission_vote_idea(self, user, perm, subject):
    if not user:
        return True

    user = user.entity
    idea = subject.i
    state = idea.wf_context.state.label
    workflow = get_workflow()

    # we can't vote for a refused idea
    if state in workflow.get_refused_states():
        return False

    # an author can't vote for his own idea
    if user in idea.authors:
        return False

    # the DSIG can cheat by voting more than once
    if user.is_dsig():
        return True

    # once a user has voted, he cannot vote anymore
    return not idea.find_vote(user)


@peak.rules.when(Rules.has_permission,
                 "perm == 'track_idea' and isinstance(subject, Idea)")
def has_permission_track_idea(self, user, perm, subject):
    if not user:
        return True

    user = user.entity
    idea = subject.i
    state = idea.wf_context.state.label
    workflow = get_workflow()

    if user in idea.authors:
        return False

    if state in workflow.get_refused_states():
        return False

    if state in workflow.get_published_states():
        return True

    return False


@peak.rules.when(Rules.has_permission,
                 "perm == 'email_idea' and isinstance(subject, Idea)")
def has_permission_email_idea(self, user, perm, subject):
    return subject.i.wf_context.state.label in get_workflow().get_published_states()


@peak.rules.when(Rules.has_permission,
                 "perm == 'view_alert' and isinstance(subject, Idea)")
@peak.rules.when(Rules.has_permission,
                 "perm == 'edit_alert' and isinstance(subject, Idea)")
def has_permission_view_or_edit_alert(self, user, perm, subject):
    if not user:
        return False

    user = user.entity
    return user.is_dsig() or user.is_developer()


# ----------
# IdeaEditor
@peak.rules.when(Rules.has_permission,
                 "perm == 'edit_idea' and isinstance(subject, IdeaEditor)")
def has_permission_edit_idea_in_editor(self, user, perm, subject):
    idea_comp = subject.idea

    if idea_comp is None:
        return True

    return security.has_permissions('edit_idea', idea_comp)


@peak.rules.when(Rules.has_permission,
                 "perm == 'delete_idea' and isinstance(subject, IdeaEditor)")
def has_permission_delete_idea_in_editor(self, user, perm, subject):
    idea_comp = subject.idea
    return security.has_permissions('delete_idea', idea_comp)


# ---------
# IdeaPager
@peak.rules.when(Rules.has_permission,
                 "perm == 'export_xls' and isinstance(subject, IdeaPager)")
def has_permission_export_xls_in_pager(self, user, perm, subject):
    if not user:
        return False

    user = user.entity
    return user.is_dsig() or user.is_developer() or user.is_facilitator()
