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

from nagare import presentation, security, component
from nagare.i18n import _, format_date, format_datetime

from eureka.ui.common import ellipsize

from eureka.ui.desktop.workflow import (IdeaWFComment, IdeaWFContext,
                                        WorkflowEventEditor, WorkflowSection,
                                        WorkflowMenu)


@presentation.render_for(IdeaWFComment, model='table_head')
def render_idea_wf_comment_table_head(self, h, comp, *args):
    h << h.th(_(u'Date'), class_='date')
    h << h.th(_(u'Action'), class_='change')
    h << h.th(_(u'From'), class_='author')
    h << h.th(_(u'Comment'), class_='comment')
    return h.root


@presentation.render_for(IdeaWFComment, model='table_row')
def render_idea_wf_comment_table_row(self, h, comp, *args):
    with h.td(class_='date'):
        h << format_datetime(self.data.submission_date, format='short')

    with h.td(class_='change'):
        h << _(self.data.from_state.label)
        h << h.div(u" ⬇ ")
        h << _(self.data.to_state.label)

    with h.td(class_='author'):
        # FIXME: we should use a specific "di" view to render the author name
        author = self.data.created_by
        di = self.data.idea_wf.assignated_di
        if author is not di or security.has_permissions('view_di', self):
            h << author.fullname
        else:
            h << _(u'Expert')

    with h.td(class_='comment'):
        if security.has_permissions('edit_comment', self):
            h << self.content_editor.render(h.AsyncRenderer())
        else:
            h << self.data.content

    return h.root


# ---------------------------------------

@presentation.render_for(IdeaWFContext, model='challenge-step')
def render_idea_wf_context_step(self, h, comp, *args):
    h << h.div(class_="bar %s" % self.step.lower().replace('_', '-'))
    if self.is_refused():
        label = _(u"Non-retained")
    elif self.is_disturbing():
        label = _(u'Disturbing')
    else:
        label = _(self.step)
    h << h.span(label, class_='potential')
    return h.root


@presentation.render_for(IdeaWFContext, model='step')
def render_idea_wf_context_step(self, h, comp, *args):
    with h.span(class_='state-bar'):
        h << comp.render(h, model='step_image')
        h << comp.render(h, model='step_text')

    return h.root


@presentation.render_for(IdeaWFContext, model='step_image')
def render_idea_wf_context_step_image(self, h, comp, *args):
    step = self.step
    css_class = step.lower().replace('_', '-')
    if self.is_refused():
        css_class += ' refused'
    elif self.is_disturbing():
        css_class += ' disturbing'

    h << h.span(class_='step-image %s' % css_class)
    return h.root


@presentation.render_for(IdeaWFContext, model='step_text')
def render_idea_wf_context_step_text(self, h, comp, *args):
    if self.is_refused():
        label = _(u"Non-retained")
    elif self.is_disturbing():
        label = _(u'Disturbing')
    else:
        label = _(self.step)

    h << h.span(label, class_='step-text')
    return h.root


@presentation.render_for(IdeaWFContext, model='last_comment')
def render_idea_wf_context_last_comment(self, h, comp, *args):
    comments = self.comments
    if len(comments) > 0:
        with h.div(class_="warning"):
            date = format_date(comments[-1].data.submission_date)
            h << h.h1(_(u'This idea has been refused on %s') % date)
            h << h.h2(_(u"The expert opinion:"))

            h << h.div(comments[-1].content)
    return h.root


@presentation.render_for(IdeaWFContext, model='history')
def render_idea_wf_context_history(self, h, comp, *args):
    comments = self.comments
    if comments:
        with h.table(class_='wf-history'):
            with h.tr(class_='head'):
                h << component.Component(comments[0]).render(h, model='table_head')

            for idx, comment in enumerate(comments):
                with h.tr(class_=['even', 'odd'][idx % 2]):
                    h << component.Component(comment).render(h, model='table_row')

    return h.root


@presentation.render_for(IdeaWFContext, model='assignated_users')
def render_idea_wf_context_assignated_users(self, h, comp, *args):
    fi = self.data.assignated_fi
    di = self.data.assignated_di

    if fi or di:
        with h.dl(class_='assignated-users'):
            if fi:
                with h.dt:
                    h << _(u'Facilitator:')
                    h << ' '
                with h.dd:
                    h << h.a(fi.fullname,
                             href='profile/' + fi.uid).action(lambda uid=fi.uid: self.show_user_profile(uid))

            if di and security.has_permissions("view_di", self):
                with h.dt:
                    h << _(u'Expert:')
                    h << ' '
                with h.dd:
                    h << h.a(di.fullname,
                             href='profile/' + di.uid).action(lambda uid=di.uid: self.show_user_profile(uid))

    return h.root


# ---------------------------------------

@presentation.render_for(WorkflowSection)
def render_workflow_section(self, h, comp, *args):
    content, tabs = self.content_and_tabs

    # we need a wrapper <div> even if empty in order to refresh the asynchronous root properly
    with h.div(class_='workflow-section'):
        if content or tabs:
            if tabs:
                h << self.menu

            if content:
                with h.div(class_="tab-content"):
                    h << content

    return h.root


# ---------------------------------------

@presentation.render_for(WorkflowMenu)
def render_workflow_menu(self, h, comp, *args):
    # workflow history
    h << comp.render(h, model='assignated_users_and_history')

    # action menu
    actions = self.actions
    if actions:
        # legend
        if self.legend:
            with h.div(class_='legend'):
                h << self.legend

        # menu
        with h.ul(class_='workflow-actions'):
            for label, event in actions:
                with h.li(class_='ideaForm'):
                    h << h.a(label).action(lambda event=event: self.select_item(event))
                    if event == self.selected_item():
                        h << self.event_editor

    return h.root


@presentation.render_for(WorkflowMenu, model='assignated_users_and_history')
def render_workflow_menu_assignated_users_and_history(self, h, comp, *args):
    h << self.wf_context.render(h.SyncRenderer(), model='assignated_users')
    h << self.wf_context.render(h.SyncRenderer(), model='history')
    return h.root


# ---------------------------------------

@presentation.render_for(WorkflowEventEditor)
def render_workflow_event_editor(self, h, comp, *args):
    def commit():
        if self.commit():
            comp.answer(True)

    with h.form(class_='workflow-event-editor'):
        with h.div(class_='fields'):
            with h.div(class_='comment-field field'):
                h << h.label(_(u'Comment') + ':')
                h << h.textarea(rows="",
                                cols="",
                                class_="comment").action(self.comment).error(self.comment.error)

            if self.should_choose_di:
                with h.div(class_='choose-di-field field'):
                    h << comp.render(h, model='choose_di')

        with h.div(class_='buttons'):
            h << h.input(type='submit',
                         value=_(u'Submit'),
                         class_="ok").action(commit)

    return h.root


@presentation.render_for(WorkflowEventEditor, model='choose_di')
def render_workflow_event_editor_choose_di(self, h, comp, *args):
    def developer_option(user):
        di_business_area = ellipsize(user.di_business_area, 40) if user.di_business_area else _(u'N/A')
        ideas_count = len(user.assignated_di_ideas)
        label = '%s - %s (%d)' % (di_business_area, user.fullname, ideas_count)
        option = h.option(label, value=user.uid)
        if self.current_di:
            option = option.selected(self.current_di.uid)
        return option

    h << h.label(_(u'Expert:'))
    with h.select().action(self.di):
        sort_key = lambda user: (user.di_business_area or _(u'N/A'))
        challenge_developers = sorted(self.challenge_developers(), key=sort_key)
        other_developers = sorted((user for user in self.all_developers()
                                   if user not in challenge_developers), key=sort_key)

        if challenge_developers:
            h << h.option('-- %s --' % _("Challenge developers"), disabled=True)
            for user in challenge_developers:
                h << developer_option(user)

            h << h.option('-- %s --' % _("Other developers"), disabled=True)

        for user in other_developers:
            h << developer_option(user)

    return h.root
