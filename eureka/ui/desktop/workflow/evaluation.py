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

from nagare import component, presentation, editor, security
from nagare.i18n import _, format_datetime

from eureka.domain.queries import search_users_fulltext
from eureka.domain.models import EvalCommentData
from eureka.domain.repositories import UserRepository, IdeaRepository
from eureka.infrastructure import validators
from eureka.infrastructure.tools import is_integer
from eureka.ui.common.yui2 import flashmessage
from eureka.ui.common.yui2 import Autocomplete


class EvalComment(object):
    def __init__(self, eval_comment_data):
        self.id = eval_comment_data.id

    @property
    def data(self):
        return EvalCommentData.get(self.id)


class EvaluationMenu(editor.Editor):
    def __init__(self, idea):
        self.idea_id = idea if is_integer(idea) else idea.id

        # first form (context)
        self.title = editor.Property(self.data.title).validate(
            validators.non_empty_string)
        self.description = editor.Property(self.data.description).validate(
            validators.non_empty_string)
        self.impact = editor.Property(self.data.impact).validate(
            validators.non_empty_string)
        self.benefit_department = editor.Property(self.idea.benefit_department or '')

        # second form (expert)
        self.expert_email = editor.Property('').validate(
            lambda t: validators.user_email(t, required=True))
        self.comment = editor.Property('').validate(
            validators.non_empty_string)

        # form (evaluation)
        if self.data.target_date:
            self.target_date = editor.Property(
                datetime.strftime(self.data.target_date, '%d/%m/%Y'))
        else:
            self.target_date = editor.Property('')
        self.goal = editor.Property(self.data.goal).validate(
            validators.FloatValidator)
        self.revenues_first_year = editor.Property(
            self.data.revenues_first_year)
        self.revenues_first_year_value = editor.Property(
            self.data.revenues_first_year_value).validate(
            validators.FloatValidator)
        self.revenues_second_year = editor.Property(
            self.data.revenues_second_year)
        self.revenues_second_year_value = editor.Property(
            self.data.revenues_second_year_value).validate(
            validators.FloatValidator)
        self.expenses_first_year = editor.Property(
            self.data.expenses_first_year)
        self.expenses_first_year_value = editor.Property(
            self.data.expenses_first_year_value)
        self.expenses_second_year = editor.Property(
            self.data.expenses_second_year)
        self.expenses_second_year_value = editor.Property(
            self.data.expenses_second_year_value)
        self.evaluation_impact = editor.Property(self.data.evaluation_impact)

        # third form (benefit)
        self.financial_gain = editor.Property(self.data.financial_gain)
        self.customer_satisfaction = editor.Property(
            self.data.customer_satisfaction)
        self.process_tier_down = editor.Property(self.data.process_tier_down)
        self.public_image = editor.Property(self.data.public_image)
        self.environment_improvement = editor.Property(
            self.data.environment_improvement)
        self.other_impact = editor.Property(self.data.other_impact)

        # fourth form (potential)
        self.innovation_scale = editor.Property(
            self.data.innovation_scale or 1).validate(validators.integer)
        self.complexity_scale = editor.Property(
            self.data.complexity_scale or 1).validate(validators.integer)
        self.duplicate = editor.Property(self.data.duplicate).validate(
            validators.integer)
        self.localization = editor.Property(self.data.localization).validate(
            validators.integer)

        self.selected_item = editor.Property('')

    @property
    def idea(self):
        return IdeaRepository().get_by_id(self.idea_id)

    @property
    def data(self):
        return self.idea.eval_context

    @property
    def state(self):
        return self.idea.wf_context.state.label

    @property
    def comments(self):
        data = self.data

        if not data:
            return []

        return [EvalComment(c) for c in data.comments]

    def reset_values(self):
        self.expenses_first_year_value(False)
        self.expenses_second_year_value(False)

    def add_comment(self, expert_email, content):
        current_user = security.get_user()
        assert current_user

        creator = current_user.entity
        expert = UserRepository().get_by_email(expert_email)

        c = EvalCommentData(created_by=creator,
                            expert=expert,
                            content=content,
                            submission_date=datetime.today())
        self.data.comments.append(c)

    def reset(self):
        self.selected_item('')

    def toggle_item(self, item):
        if item == self.selected_item():
            self.selected_item('')
        else:
            self.selected_item(item)

    def update_context(self):
        properties = ('title', 'description', 'impact', 'benefit_department')
        if super(EvaluationMenu, self).is_validated(properties):
            self.data.title = self.title.value
            self.data.description = self.description.value
            self.data.impact = self.impact.value
            self.idea.benefit_department = self.benefit_department.value

            flashmessage.set_flash(_(u'Context changed'))
            self.reset()

    def update_expert(self):
        properties = ('expert_email', 'comment')
        if super(EvaluationMenu, self).is_validated(properties):
            self.add_comment(self.expert_email.value,
                             self.comment.value)

            flashmessage.set_flash(_(u'Expert added'))
            self.reset()

    def update_benefit(self):
        properties = (
            'financial_gain', 'customer_satisfaction', 'process_tier_down',
            'public_image', 'environment_improvement', 'other_impact')
        if super(EvaluationMenu, self).is_validated(properties):
            self.data.financial_gain = self.financial_gain.value
            self.data.customer_satisfaction = self.customer_satisfaction.value
            self.data.process_tier_down = self.process_tier_down.value
            self.data.public_image = self.public_image.value
            self.data.environment_improvement = self.environment_improvement.value
            self.data.other_impact = self.other_impact.value

            flashmessage.set_flash(_(u'Benefit changed'))
            self.reset()

    def update_potential(self):
        properties = (
            'innovation_scale', 'complexity_scale', 'duplicate',
            'localization')
        if super(EvaluationMenu, self).is_validated(properties):
            self.data.innovation_scale = self.innovation_scale.value
            self.data.complexity_scale = self.complexity_scale.value
            self.data.duplicate = self.duplicate.value
            self.data.localization = self.localization.value

            flashmessage.set_flash(_(u'Potential changed'))
            self.reset()

    def update_evaluation(self):
        properties = (
            'innovation_scale', 'complexity_scale', 'duplicate',
            'localization', 'goal', 'revenues_first_year', 'revenues_first_year_value',
            'revenues_second_year', 'revenues_second_year_value', 'expenses_first_year',
            'expenses_second_year')
        if super(EvaluationMenu, self).is_validated(properties):
            if self.target_date.value:
                self.data.target_date = datetime.strptime(
                    self.target_date.value,
                    '%d/%m/%Y')
            else:
                self.data.target_date = None

            self.data.goal = self.goal.value
            self.data.revenues_first_year = self.revenues_first_year.value
            self.data.revenues_first_year_value = self.revenues_first_year_value.value
            self.data.revenues_second_year = self.revenues_second_year.value
            self.data.revenues_second_year_value = self.revenues_second_year_value.value
            self.data.expenses_first_year = self.expenses_first_year.value
            self.data.expenses_first_year_value = self.expenses_first_year_value.value
            self.data.expenses_second_year = self.expenses_second_year.value
            self.data.expenses_second_year_value = self.expenses_second_year_value.value
            self.data.evaluation_impact = self.evaluation_impact.value
            flashmessage.set_flash(_(u'evaluation changed'))

            self.goal(self.data.goal)
            self.revenues_first_year(self.data.revenues_first_year)
            self.revenues_first_year_value(self.data.revenues_first_year_value)
            self.revenues_second_year(self.data.revenues_second_year)
            self.revenues_second_year_value(self.data.revenues_second_year_value)
            self.expenses_first_year_value(self.data.expenses_first_year_value)
            self.expenses_second_year(self.data.expenses_second_year)
            self.expenses_second_year_value(self.data.expenses_second_year_value)
            self.evaluation_impact(self.data.evaluation_impact)

            self.reset()
