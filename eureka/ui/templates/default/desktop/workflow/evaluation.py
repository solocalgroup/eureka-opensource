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

from nagare import component, presentation
from nagare.i18n import _, format_datetime

from eureka.domain.queries import search_users_fulltext
from eureka.ui.common.yui2 import Autocomplete
from eureka.ui.desktop.workflow import EvaluationMenu, EvalComment


@presentation.render_for(EvalComment, model='table_header')
def render_eval_comment_table_header(self, h, comp, *args):
    h << h.th(_(u'Date'))
    h << h.th(_(u'From'))
    h << h.th(_(u'Consulted expert'))
    h << h.th(_(u'Comment'))
    return h.root


@presentation.render_for(EvalComment, model='table_row')
def render_eval_comment_table_row(self, h, comp, *args):
    h << h.td(format_datetime(self.data.submission_date))
    h << h.td(self.data.created_by.fullname)
    h << h.td(self.data.expert.fullname)
    h << h.td(self.data.content)
    return h.root


# --------------------------------------------------------------------------


@presentation.render_for(EvaluationMenu)
def render_evaluation_menu(self, h, comp, *args):
    with h.ul(class_='eval-context-editor'):
        for model in ['context', 'expert', 'benefit', '' 'potential']:
            with h.li(class_='ideaForm'):
                h << comp.render(h, model=model)

    return h.root


@presentation.render_for(EvaluationMenu, model='context')
def render_evaluation_menu_context(self, h, comp, *args):
    label = _(u"I develop the author's idea")
    h << h.a(label, title=label).action(lambda: self.toggle_item('context'))
    h << h.div(_(u"I can edit or fill in the idea to reflect my analysis. "
                 u"This addition will only be visible by me and by the people "
                 u"who I will forward the idea (DSIG, another idea developer)."),
               class_="legend")

    if self.selected_item() == 'context':
        with h.form:
            with h.div(class_='fields'):
                with h.div(class_='title-field field'):
                    h << h.label(_(u'Title') + '*')
                    h << h.input(type='text',
                                 class_='text',
                                 value=self.title()).action(self.title).error(
                        self.title.error)
                    h << h.div(_(u'I can change the idea title'),
                               class_='legend')

                with h.div(class_='description-field field'):
                    h << h.label(_(u'Description') + '*')
                    h << h.textarea(self.description() or u'',
                                    class_='description wide',
                                    rows='',
                                    cols='').action(self.description).error(
                        self.description.error)
                    h << h.div(_(u'I can change the idea description'),
                               class_='legend')

                with h.div(class_='impact-field field'):
                    h << h.label(_(u'Impact'))
                    h << h.textarea(self.impact() or u'',
                                    rows='',
                                    cols='').action(self.impact).error(
                        self.impact.error)
                    h << h.div(
                        _(u'I can change the expected impacts of the idea'),
                        class_='legend')

            with h.div(class_='buttons'):
                h << h.input(type='submit',
                             value=_(u"Save"),
                             class_="ok").action(self.update_context)

    return h.root


@presentation.render_for(EvaluationMenu, model='expert')
def render_evaluation_menu_expert(self, h, comp, *args):
    label = _(u"I consulted experts")
    h << h.a(label, title=label).action(lambda: self.toggle_item('expert'))
    h << h.div(_(u"Write down the expert analysis"),
               class_="legend")

    if self.selected_item() == 'expert':
        h << comp.render(h, model='expert_comments')

        with h.form:
            with h.div(class_='fields'):
                with h.div(class_='expert-field field'):
                    h << h.label(_(u'Expert email'))
                    max_results_displayed = 20
                    h << component.Component(Autocomplete(
                        lambda s: search_users_fulltext(s,
                                                        limit=max_results_displayed),
                        type='text',
                        class_='text wide',
                        name='expert_email',
                        max_results_displayed=max_results_displayed,
                        value=self.expert_email(),
                        action=self.expert_email,
                        error=self.expert_email.error)).render(h)

                    h << h.div(
                        _(u'I fill in the email of the expert I consulted'),
                        class_='legend')

                with h.div(class_='comment-field field'):
                    h << h.label(_(u'Comment'))
                    h << h.textarea(self.comment() or u'',
                                    rows='',
                                    cols='').action(self.comment).error(
                        self.comment.error)
                    h << h.div(
                        _(u'I fill in the expert comment about the idea'),
                        class_='legend')

            with h.div(class_='buttons'):
                h << h.input(type='submit', value=_(u"Save"),
                             class_="ok").action(self.update_expert)

    return h.root


@presentation.render_for(EvaluationMenu, model='expert_comments')
def render_evaluation_menu_expert_comments(self, h, comp, *args):
    comments = self.comments
    if len(comments) > 0:
        with h.table(class_='eval_history'):
            with h.tr(class_='head'):
                h << component.Component(comments[0]).render(h,
                                                             model='table_header')

            for idx, c in enumerate(comments):
                with h.tr(class_=['even', 'odd'][idx % 2]):
                    h << component.Component(c).render(h, model='table_row')

    return h.root


@presentation.render_for(EvaluationMenu, model='benefit')
def render_evaluation_menu_benefit(self, h, comp, *args):
    label = _(u"I evaluate the expected benefits of the idea")
    h << h.a(label, title=label).action(lambda: self.toggle_item('benefit'))

    if self.selected_item() == 'benefit':
        with h.form:
            with h.div(class_='fields'):
                with h.div(class_='financial-gain-field field'):
                    h << h.label(
                        _(u'Financial gain (additional turnover, savings, …)'))
                    h << h.textarea(self.financial_gain() or u'',
                                    rows='',
                                    cols='').action(self.financial_gain).error(
                        self.financial_gain.error)
                    h << h.div(_(u'e.g. 3000€/year savings, '
                                 u'potential 100 k€ turnover'),
                               class_='legend')

                with h.div(class_='customer-satisfaction-field field'):
                    h << h.label(_(u'Customer satisfaction'))
                    h << h.textarea(self.customer_satisfaction() or u'',
                                    rows='',
                                    cols='').action(
                        self.customer_satisfaction).error(
                        self.customer_satisfaction.error)

                with h.div(
                        class_='business-process-simplification-field field'):
                    h << h.label(_(u'Business process simplification'))
                    h << h.textarea(self.process_tier_down() or u'',
                                    rows='',
                                    cols='').action(
                        self.process_tier_down).error(
                        self.process_tier_down.error)
                    h << h.div(
                        _(u'e.g. 2 man-day saved per month, time saved, …'),
                        class_='legend')

                with h.div(class_='public-corporate-image-field field'):
                    h << h.label(_(u'Public image, corporate image'))
                    h << h.textarea(self.public_image() or u'',
                                    rows='',
                                    cols='').action(self.public_image).error(
                        self.public_image.error)
                    h << h.div(_(u'e.g. good citizen corporate image, …'),
                               class_='legend')

                with h.div(class_='office-environment-field field'):
                    h << h.label(_(u'Office environment improvement'))
                    h << h.textarea(self.environment_improvement() or u'',
                                    rows='',
                                    cols='').action(
                        self.environment_improvement).error(
                        self.environment_improvement.error)

                with h.div(class_='other-impact-field field'):
                    h << h.label(_(u'Other unlisted impact'))
                    h << h.textarea(self.other_impact() or u'',
                                    rows='',
                                    cols='').action(self.other_impact).error(
                        self.other_impact.error)

            with h.div(class_='buttons'):
                h << h.input(type='submit',
                             value=_(u"Save"),
                             class_="ok").action(self.update_benefit)

    return h.root


@presentation.render_for(EvaluationMenu, model='potential')
def render_evaluation_menu_potential(self, h, comp, *args):
    label = _(u"I assess the potential of implementing the idea")
    h << h.a(label, title=label).action(lambda: self.toggle_item('potential'))

    if self.selected_item() == 'potential':
        with h.form:
            with h.div(class_='fields'):
                with h.table(class_="five_cols"):
                    with h.tr:
                        h << h.th(
                            _(u'I describe the innovation level from 1 to 5'),
                            colspan="5",
                            class_="title")

                    with h.tr:
                        for i in range(1, 6):
                            with h.td:
                                h << _("%d:") % i << " "
                                selected = self.innovation_scale() == i
                                h << h.input(type='radio',
                                             class_='radio',
                                             name="innovation_scale").selected(
                                    selected).action(
                                    lambda i=i: self.innovation_scale(i))

                    with h.tr:
                        with h.td(colspan="2", class_="legend_left"):
                            h << _(u'improvement idea')
                            h << h.br
                            h << _(u'operational idea')

                        with h.td:
                            h << ""

                        with h.td(colspan="2", class_="legend_right"):
                            h << _(u'disruptive idea')
                            h << h.br
                            h << _(u'strategic idea')

                h << h.br

                with h.table(class_="five_cols"):
                    with h.tr:
                        h << h.th(
                            _(u'I describe the complexity level from 1 to 5'),
                            colspan="5",
                            class_="title")

                    with h.tr:
                        for i in range(1, 6):
                            with h.td:
                                h << _("%d:") % i << " "
                                selected = self.complexity_scale() == i
                                h << h.input(type='radio',
                                             class_='radio',
                                             name="complexity_scale").selected(
                                    selected).action(
                                    lambda i=i: self.complexity_scale(i))

                    with h.tr:
                        with h.td(colspan="2", class_="legend_left"):
                            h << _(u'simple implementation')
                            h << h.br
                            h << _(u'quick implementation')
                            h << h.br
                            h << _(u'low resources')

                        with h.td:
                            h << ""

                        with h.td(colspan="2", class_="legend_right"):
                            h << _(u'complex implementation')
                            h << h.br
                            h << _(u'long implementation')
                            h << h.br
                            h << _(u'high resources')

                h << h.br

                with h.table(class_="two_cols"):
                    with h.tr:
                        h << h.th(_(u'Can idea be duplicated?'),
                                  colspan="2", class_="title")

                    with h.tr:
                        with h.td:
                            h << _(u'Yes') << " : " << h.input(type='radio',
                                                               class_='radio',
                                                               name="duplicate").selected(
                                self.duplicate() == 0).action(
                                lambda: self.duplicate(0))

                        with h.td:
                            h << _(u'No') << " : " << h.input(type='radio',
                                                              class_='radio',
                                                              name="duplicate").selected(
                                self.duplicate() == 1).action(
                                lambda: self.duplicate(1))

                h << h.br

                with h.table(class_="three_cols"):
                    with h.tr:
                        h << h.th(_(u'What kind of idea is it?'),
                                  colspan="3", class_="title")

                    with h.tr:
                        with h.td:
                            h << _(u'Local') << " : " << h.input(type='radio',
                                                                 class_='radio',
                                                                 name="localization").selected(
                                self.localization() == 0).action(
                                lambda: self.localization(0))

                        with h.td:
                            h << _(u'Global') << " : " << h.input(type='radio',
                                                                  class_='radio',
                                                                  name="localization").selected(
                                self.localization() == 1).action(
                                lambda: self.localization(1))

                        with h.td:
                            h << _(u'Strategic') << " : " << h.input(
                                type='radio',
                                class_='radio',
                                name="localization").selected(
                                self.localization() == 2).action(
                                lambda: self.localization(2))

            with h.div(class_='buttons'):
                h << h.input(type='submit',
                             value=_(u"Save"),
                             class_="ok").action(self.update_potential)

    return h.root
