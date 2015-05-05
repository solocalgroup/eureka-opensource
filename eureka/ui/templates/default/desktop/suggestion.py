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

from nagare import presentation, security
from nagare.i18n import _, format_date

from eureka.infrastructure.tools import limit_string

from eureka.domain.models import ImprovementState
from eureka.ui.desktop.suggestion import (Suggestion, SubmitSuggestion,
                                          SuggestionsPager)


@presentation.render_for(SubmitSuggestion)
def render_submit_suggestion(self, h, comp, *args):
    with h.div(class_='submit-suggestion'):
        with h.h1(class_="tab big active"):
            h << h.span(_(u"Describe your improvement request"))

        with h.h2:
            h << _(u"You have ideas to help us improve Eureka? Don't hesitate, please tell us the improvements that you want to see in the application")

        with h.form:
            with h.div(class_='fields'):
                with h.div(class_='domain-field field'):
                    h << h.label(_(u'Domain:'))
                    with h.select(name="domain", class_="select").action(self.domain):
                        for d in self.domains:
                            h << h.option(_(d.label), value=d.id).selected(self.domain())

                with h.div(class_='proposal-field field'):
                    h << h.label(_(u"Proposal:"))
                    h << h.textarea(self.content(), rows=5, cols=80, class_='wide').action(self.content).error(self.content.error)

            with h.div(class_='buttons'):
                h << h.input(type="submit",
                             class_="submit",
                             value=_(u"I send my suggestion")).action(self.commit)

    return h.root


@presentation.render_for(Suggestion)
def render_suggestion(self, h, comp, *args):
    masked_class = '' if self.data.visible else ' masked'
    with h.li(class_='collapse suggestion' + masked_class):
        content = self.data.content
        shortcontent = limit_string(content, 85)[1:] if len(content) > 85 else content

        # expand/collapse button
        if len(shortcontent) != len(content):
            h << h.a(class_="toggle on",
                     onclick='toggleCollapseExpand(this);',
                     title=_(u"Show the whole suggestion"))
            h << h.a(class_="toggle off",
                     onclick='toggleCollapseExpand(this);',
                     title=_(u"Hide the whole suggestion"))

        # icon
        icon_info_by_state = {
            ImprovementState.TREATED: (_(u'Suggestion processed and deployed'), 'flag_green.png'),
            ImprovementState.RUNNING: (_(u'Suggestion in progress'), 'flag_yellow.png'),
            ImprovementState.REJECTED: (_(u'Suggestion rejected'), 'flag_red.png'),
        }
        icon_info = icon_info_by_state.get(self.data.state, None)
        if icon_info:
            title, icon_name = icon_info
            icon_url = "%sstyle/desktop/icons/%s" % (h.head.static_url, icon_name)
            h << h.img(title=title,
                       alt=title,
                       src=icon_url,
                       class_="flag")

        # short and full content blocks
        with h.p(class_='meta'):
            h << _(u"from").capitalize() << " "
            h << h.span(self.data.user.fullname, class_='author')
            h << " " << _(u'at') << ' '
            h << h.span(format_date(self.data.submission_date, format='short'),
                        lass_='submission date')
            h << " - "
            h << _(self.data.domain.label)

        h << h.p(shortcontent, class_='short content')
        h << h.p(content, class_='long content')

        # actions
        if security.has_permissions('edit', self):
            with h.div(class_='actions'):
                # visibility toggle
                visible = self.data.visible
                label = _(u'Hide') if visible else _(u'Show')
                title = _(u'Hide the suggestion') if visible else _(u'Show the suggestion')
                h << h.a(label, title=title).action(self.toggle_visibility)

                # change state actions
                title = _(u'Mark as rejected')
                rejected_action = h.a(title, title=title).action(lambda: self.change_state(ImprovementState.REJECTED))
                title = _(u'Mark as in progress')
                running_action = h.a(title, title=title).action(lambda: self.change_state(ImprovementState.RUNNING))
                title = _(u'Mark as processed')
                treated_action = h.a(title, title=title).action(lambda: self.change_state(ImprovementState.TREATED))

                actions_by_state = {
                    ImprovementState.NEW: (rejected_action, treated_action, running_action),
                    ImprovementState.RUNNING: (rejected_action, treated_action)
                }

                actions = actions_by_state.get(self.data.state, None)
                if actions:
                    for action in actions:
                        h << h.a(u' | ')
                        h << action

    return h.root


@presentation.render_for(SuggestionsPager)
def render_suggestions_pager(self, h, comp, *args):
    with h.div(class_='suggestions'):
        with h.h1(class_="tab big active"):
            h << h.span(_(u'List of the improvements suggested and their last processing status'))

        # button to submit a new suggestion
        with h.div(class_='betaBox'):
            h << h.a(_(u'Suggest improvements'),
                     title=_(u"Propose site or application improvements"),
                     class_='submit').action(lambda: self.with_login(self.submit_suggestion))

        h << comp.render(h, 'tabs')

        with h.ul(class_="items"):
            for suggestion in self.suggestions:
                h << suggestion

        h << comp.render(h, 'batch')

    return h.root


@presentation.render_for(SuggestionsPager, model='tabs')
def render_suggestions_pager_tabs(self, h, *args):
    h << self.menu

    return h.root
