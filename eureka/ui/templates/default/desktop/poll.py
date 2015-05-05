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

from nagare import presentation, component
from nagare.i18n import _, format_datetime

from eureka.ui.common.confirmation import Confirmation
from eureka.ui.common.yui2 import Calendar

from eureka.ui.desktop.poll import Poll, PollEditor


@presentation.render_for(Poll)
def render_poll(self, h, comp, *args):
    with h.div(class_="poll"):
        if self.is_poll_finished() or (self.user is not None and self.has_voted()):
            h << comp.render(h, model='results')
        else:
            h << comp.render(h, model='questionnaire')

    return h.root


@presentation.render_for(Poll, model='questionnaire')
def render_poll_question(self, h, comp, *args):
    # title
    # with h.h1:
    #    h << self.poll.title
    #
    # date
    # if self.should_display_date():
    #    one_day = timedelta(days=1)
    #    end_date = format_datetime(self.poll.end_date - one_day, format="d MMMM")
    #    with h.p(class_='end_date'):
    #        h << _(u'The poll ends on %s') % end_date

    # question
    with h.h2:
        h << self.poll.question

    # choices
    choices = []

    def add_vote(choice_id):
        choices.append(choice_id)

    is_anonymous = self.user is None
    disabled_option = {'disabled': True} if is_anonymous else {}
    disabled_class = ' disabled' if is_anonymous else ''

    with h.form:
        with h.div(class_='fields'):
            for choice in self.poll.choices:
                with h.div(class_='choice-field field'):
                    input_id = h.generate_id('choice')
                    if self.poll.multiple:
                        h << h.input(type='checkbox',
                                     class_='checkbox' + disabled_class,
                                     id=input_id,
                                     name='choice',
                                     value=choice.id,
                                     **disabled_option).action(lambda v: add_vote(int(v)))
                    else:
                        h << h.input(type='radio',
                                     class_='radio' + disabled_class,
                                     id=input_id,
                                     name='choice',
                                     **disabled_option).action(lambda choice_id=choice.id: add_vote(choice_id))
                    h << h.label(choice.label, for_=input_id)

        if is_anonymous:
            with h.div(class_='buttons poll-alert'):
                h << _('Please login to answer poll')
        else:
            with h.div(class_='buttons'):
                h << h.input(type='submit',
                             value=_(u'See results'),
                             class_="submit" + disabled_class,
                             **disabled_option).action(lambda choices=choices: self.commit(choices))

    return h.root


@presentation.render_for(Poll, model='results')
def render_poll_votes(self, h, comp, *args):
    # title
    # with h.h1:
    #    if self.is_poll_finished():
    #        h << _(u'Poll results')
    #    else:
    #        h << self.poll.title

    # question
    with h.h2:
        h << self.poll.question

    with h.ul(class_="votes"):
        for index, (choice, ratio) in enumerate(self.get_votes_ratios_per_choice()):
            with h.li(class_='item_%d' % index):
                h << h.p(choice.label)
                with h.div(class_='bar'):
                    h << h.div(class_='bar-inner', style="width: %d%%;" % ratio)
                h << h.div('%d%%' % ratio, class_="percentage")

    with h.p(class_="votes-totals"):
        h << _(u'Vote Total') << " " << self.nb_voters
        h << ' ' << _(u'voter')

    return h.root


@presentation.render_for(PollEditor)
def render_poll_editor(self, h, comp, *args):
    def commit():
        # show a confirmation message if the poll is currently active or when trying to suppress a poll choice that have votes
        if self.show_confirmation_message():
            message = _(u'The poll is currently enabled or/and has votes: are you sure you want to edit this poll? (some votes may be lost)')
            confirmation = Confirmation(message,
                                        confirm_text=_(u'Yes'),
                                        cancel_text=_(u'No'))
            if not comp.call(confirmation):
                return

        if self.commit():
            comp.answer()

    with h.div(class_='poll-editor'):
        # screen title
        with h.h1(class_="tab active big"):
            h << h.span(h.a(_(u'Edit the poll')))

        # date time picker for the end date
        end_date_id = h.generate_id('end_date')
        end_date_calendar = component.Component(Calendar(end_date_id,
                                                         title=_(u'Select a date'),
                                                         close_button=True,
                                                         mindate=datetime.now()))

        with h.form.pre_action(self.clear_checkboxes):
            with h.table(class_='phantom'):
                with h.colgroup:
                    h << h.col(class_='label')
                    h << h.col(class_='value')

                # title
                with h.tr:
                    with h.td:
                        h << h.label(_(u'Title'))
                    with h.td:
                        h << h.input(type='text',
                                     class_='text wide',
                                     value=self.title()).action(self.title).error(self.title.error)

                # question
                with h.tr:
                    with h.td:
                        h << h.label(_(u'Question'))
                    with h.td:
                        h << h.input(type='text',
                                     class_='text wide',
                                     value=self.question()).action(self.question).error(self.question.error)

                # choices
                for idx, choice in enumerate(self.choices):
                    with h.tr:
                        with h.td:
                            h << h.label(_(u'Choice %d') % (idx + 1))
                        with h.td:
                            h << h.input(type='text',
                                         class_='text wide',
                                         value=choice()).action(choice).error(choice.error)

                # multiple choice
                with h.tr:
                    with h.td:
                        h << h.label(_(u'Multiple choice'))
                    with h.td:
                        h << h.input(type='checkbox').selected(self.multiple.value).action(self.multiple)

                # end date
                with h.tr:
                    with h.td:
                        h << h.label(_(u'End date (included)'))
                    with h.td:
                        h << h.input(type='text',
                                     id=end_date_calendar().field_id,
                                     class_='date',
                                     value=self.end_date()).action(self.end_date).error(self.end_date.error)
                        h << end_date_calendar.render(h, model='date_picker')
                        h << end_date_calendar

            # buttons
            with h.div(class_='buttons'):
                h << h.input(type='submit',
                             class_='confirm-button',
                             value=_(u'Save')).action(commit)

                h << h.input(type='submit',
                             class_='cancel-button',
                             value=_(u'Cancel')).action(comp.answer)

    return h.root
