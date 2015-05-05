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

from datetime import timedelta

from nagare import editor
from nagare.i18n import _

from eureka.domain.repositories import PollRepository
from eureka.domain.models import PollChoiceData
from eureka.infrastructure import validators
from eureka.infrastructure.tools import is_integer


ONE_DAY = timedelta(days=1)


class PollEditor(editor.Editor):
    MAX_CHOICES = 10

    def __init__(self, poll=None):
        super(PollEditor, self).__init__(None)
        self.id = poll if (is_integer(poll) or poll is None) else poll.id
        poll = self.poll

        self.title = editor.Property(_(u'Poll')).validate(validators.non_empty_string)
        self.question = editor.Property(u'').validate(validators.non_empty_string)
        self.choices = [editor.Property(u'').validate(validators.string) for __ in range(self.MAX_CHOICES)]
        self.multiple = editor.Property(u'')
        self.end_date = editor.Property(u'').validate(validators.non_empty_date)

        if poll:
            self.title.set(poll.title)
            self.question.set(poll.question)
            for idx, choice in enumerate(poll.choices):
                self.choices[idx].set(choice.label)
            self.multiple.set(poll.multiple)
            self.end_date.set((poll.end_date - ONE_DAY).strftime('%d/%m/%Y'))

    @property
    def poll(self):
        return PollRepository().get_by_id(self.id)

    def show_confirmation_message(self):
        return self.poll and (self.poll.enabled or len(self.poll.votes) > 0)

    def clear_checkboxes(self):
        self.multiple.set(False)

    def is_validated(self):
        properties = ('title', 'question', 'multiple', 'end_date')
        return super(PollEditor, self).is_validated(properties) and all(choice.error is None for choice in self.choices)

    def commit(self):
        if not self.is_validated():
            return False

        poll = self.poll or PollRepository().create()
        poll.title = self.title.value
        poll.question = self.question.value
        poll.multiple = self.multiple.value
        poll.end_date = self.end_date.value + ONE_DAY

        # insert/update choices
        polls_to_delete = []
        for idx, choice_property in enumerate(self.choices):
            choice_label = choice_property.value
            if choice_label:
                choice = poll.choices[idx] if idx < len(poll.choices) else PollChoiceData(poll=poll)
                choice.label = choice_label
            else:
                if idx < len(poll.choices):
                    polls_to_delete.append(poll.choices[idx].id)

        # delete choices
        for id in polls_to_delete:
            for choice in poll.choices:
                if choice.id == id:
                    choice.delete()

        return True
