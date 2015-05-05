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

from nagare import editor, component, security, var
from nagare.i18n import _L

from eureka.domain.repositories import UserRepository, IdeaRepository
from eureka.domain.models import WFCommentData
from eureka.infrastructure import event_management, validators
from eureka.infrastructure.tools import is_integer
from eureka.infrastructure.workflow.workflow import process_event
from eureka.ui.common.inplace_editor import InplaceEditor
from eureka.ui.common.yui2 import flashmessage
from eureka.infrastructure.workflow.workflow import switching_actions, recommendation_actions
from eureka.ui.common.menu import Menu
from .evaluation import EvaluationMenu


class IdeaWFComment(object):
    def __init__(self, comment):
        self.id = comment.id
        self.content = editor.Property(comment.content)
        self.content_editor = component.Component(
            InplaceEditor(self.content, self.commit))

    @property
    def data(self):
        return WFCommentData.get(self.id)

    @property
    def idea(self):
        return self.data.idea_wf.idea

    def commit(self):
        if self.content.error:
            return False

        self.data.content = self.content.value
        return True


class IdeaWFContext(object):
    """Idea Workflow Context"""
    # FIXME: pass an IdeaData instance only
    def __init__(self, idea):
        super(IdeaWFContext, self).__init__()
        self.idea_id = idea if is_integer(idea) else idea.id

    @property
    def idea(self):
        return IdeaRepository().get_by_id(self.idea_id)

    @property
    def data(self):
        idea = self.idea
        return idea.wf_context if idea else None

    @property
    def comments(self):
        return [IdeaWFComment(c) for c in self.data.comments]

    @property
    def state(self):
        return self.data.state.label

    @property
    def step(self):
        return self.data.state.step.label

    def is_disturbing(self):
        dsig_basket_state = get_workflow().WFStates.DSIG_BASKET_STATE
        return self.state == dsig_basket_state

    def is_refused(self):
        return self.state in get_workflow().get_refused_states()

    def add_comment(self, content, old_state, new_state):
        self.data.add_comment(content, old_state, new_state)

    def show_user_profile(self, user_uid):
        event_management._emit_signal(self, "VIEW_USER_PROFILE",
                                      user_uid=user_uid)


class WorkflowSection(object):
    """Workflow section in the Idea detail view"""

    def __init__(self, idea):
        super(WorkflowSection, self).__init__()
        self.idea_id = idea if is_integer(idea) else idea.id

        self.switching_menu = component.Component(WorkflowMenu(self.idea_id, switching_actions))
        event_management._register_listener(self, self.switching_menu())

        recommendation_legend = _L(u'After my appraisal i can propose two kinds of suggestion:')
        self.recommendation_menu = component.Component(
            WorkflowMenu(self.idea_id, recommendation_actions, recommendation_legend))
        event_management._register_listener(self, self.recommendation_menu())

        self.evaluation_menu = component.Component(EvaluationMenu(self.idea_id))

        self.tabs = (('switching', _L(u'My actions'), self.switching_menu),
                     ('evaluation', _L(u"My evaluation"), self.evaluation_menu),
                     ('recommendation', _L(u"My recommendation"), self.recommendation_menu))
        self.selected_tab = editor.Property('switching')

        self.menu_items = [(label, name, None, '', None) for name, label, action in self.filtered_tabs]

        self.menu = component.Component(Menu([], self.filter_menu), model='tab_renderer')
        self.menu.on_answer(self.select_tab)

        if self.menu_items:
            self.select_tab(0)

    @property
    def filtered_tabs(self):
        return [(name, label, action) for name, label, action in self.tabs if
                security.has_permissions('view', action()) and security.has_permissions('show_menu', (name, action()))]

    def filter_menu(self):
        self.menu_items = [(label, name, None, '', None) for name, label, action in self.filtered_tabs]
        return self.menu_items

    def select_tab(self, value):
        self.selected_tab(self.menu_items[value][1])
        self.menu().selected(value)

    @property
    def idea(self):
        return IdeaRepository().get_by_id(self.idea_id)

    @property
    def state(self):
        return self.idea.wf_context.state.label

    @property
    def content_and_tabs(self):
        available_tabs = self.filtered_tabs

        if not available_tabs:
            return None, []

        selected_tab = self.selected_tab()
        selected_comp = None
        for name, _, comp in available_tabs:
            if name == selected_tab:
                selected_comp = comp

        if not selected_comp:
            selected_tab = available_tabs[0][0]
            selected_comp = available_tabs[0][2]
            self.selected_tab(selected_tab)

        return selected_comp, [(name, label) for name, label, _ in available_tabs]


class WorkflowMenu(object):
    def __init__(self, idea, get_actions, legend=None):
        self.idea_id = idea if is_integer(idea) else idea.id
        self.get_actions = get_actions
        self.legend = legend
        self.selected_item = editor.Property()
        self.wf_context = component.Component(IdeaWFContext(self.idea_id))
        event_management._register_listener(self, self.wf_context())

    @property
    def idea(self):
        return IdeaRepository().get_by_id(self.idea_id)

    @property
    def actions(self):
        current_user = security.get_user()
        return self.get_actions(current_user.entity if current_user else None,
                                self.idea)

    def create_editor(self, item):
        return component.Component(
            WorkflowEventEditor(self.idea_id, item)).on_answer(
            lambda a: self.reset())

    def reset(self):
        self.select_item(None)

    def select_item(self, item):
        if self.selected_item() == item:
            self.selected_item(None)
            self.event_editor = None
        else:
            self.selected_item(item)
            self.event_editor = self.create_editor(item)


class WorkflowEventEditor(editor.Editor):
    def __init__(self, idea, event):
        self.idea_id = idea if is_integer(idea) else idea.id
        self.event = event
        self.comment = editor.Property('')
        # for some workflow events, we must choose a new developer
        self.di = editor.Property('')

        refuse_event = get_workflow().WFEvents.REFUSE_EVENT
        if event in (refuse_event,):
            self.comment.validate(validators.non_empty_string)
        self.show_all = var.Var(False)

    @property
    def idea(self):
        return IdeaRepository().get_by_id(self.idea_id)

    @property
    def should_choose_di(self):
        send_di_event = get_workflow().WFEvents.SEND_DI_EVENT
        return self.event == send_di_event

    @property
    def current_di(self):
        return self.idea.wf_context.assignated_di

    def all_developers(self):
        return UserRepository().get_developers()

    def challenge_developers(self):
        challenge = self.idea.challenge
        return challenge.associated_dis if challenge else []

    def commit(self):
        current_user = security.get_user()
        assert current_user

        properties = ('comment', 'di')
        if not super(WorkflowEventEditor, self).is_validated(properties):
            return False

        idea = self.idea
        wf_context = idea.wf_context

        kw = dict()
        if self.should_choose_di:
            previous_di = wf_context.assignated_di
            kw = dict(di=self.di.value, previous_di=previous_di)

        process_event(from_user=current_user.entity,
                      idea=idea,
                      event=self.event,
                      comment=self.comment.value,
                      notify=flashmessage.set_flash,
                      **kw)

        return True
