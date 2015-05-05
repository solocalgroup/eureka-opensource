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

from eureka.domain.repositories import ChallengeRepository, UserRepository
from eureka.infrastructure.urls import get_url_service
from eureka.infrastructure import validators
from eureka.infrastructure.tools import is_integer
from eureka.domain.models import ChallengeStatus, RoleType


class ChallengeEditor(editor.Editor):
    def __init__(self, challenge=None, mobile_access=False):
        self.id = challenge if (is_integer(challenge) or challenge is None) else challenge.id
        self.challenge_repository = ChallengeRepository()
        self.mobile_access = mobile_access
        challenge = self.challenge

        # properties
        self.title = editor.Property(u'').validate(validators.non_empty_string)
        self.short_title = editor.Property(u'').validate(validators.non_empty_string)
        self.created_by = editor.Property(u'').validate(lambda t: validators.user_email(t, True))
        self.organization = editor.Property(u'').validate(validators.non_empty_string)
        self.associated_dis = editor.Property(u'').validate(validators.user_email_list)
        self.starting_date = editor.Property(u'').validate(validators.non_empty_date)
        self.ending_date = editor.Property(u'').validate(validators.non_empty_date)
        self.summary = editor.Property(u'').validate(validators.non_empty_string)
        self.description = editor.Property(u'').validate(validators.non_empty_string)
        self.mobile_description = editor.Property(u'')
        self.outcome = editor.Property(u'').validate(validators.string)
        self.tags = editor.Property(u'').validate(lambda t: validators.word_list(t, duplicates='remove'))

        if challenge:
            self.title.set(challenge.title)
            self.short_title.set(challenge.short_title)
            self.created_by.set(challenge.created_by.email)
            self.organization.set(challenge.organization)
            associated_dis_email = ','.join(user.email for user in challenge.associated_dis)
            self.associated_dis.set(associated_dis_email)
            self.starting_date.set(challenge.starting_date.date().strftime('%d/%m/%Y'))
            self.ending_date.set(challenge.ending_date.date().strftime('%d/%m/%Y'))
            self.summary.set(challenge.summary)
            self.description.set(challenge.description)
            self.mobile_description.set(challenge.mobile_description)
            self.outcome.set(challenge.outcome)
            self.tags.set(u', '.join(challenge.tags))

        # Because the mobile description is optional in each eureka instance
        # and the validator will be triggered if we do this before
        self.mobile_description.validate(validators.non_empty_string)

    def gallery_url(self, editor_id):
        return get_url_service().expand_url(['gallery-for', editor_id])

    def post_validate(self):
        """Inter-field validation"""
        if self.ending_date.value < self.starting_date.value:
            self.ending_date.error = _(u'Ending date must be later than starting date')

    @property
    def challenge(self):
        return self.challenge_repository.get_by_id(self.id)

    @property
    def finished(self):
        challenge = self.challenge
        return (challenge.status() == ChallengeStatus.Finished) if challenge else False

    def commit(self):
        properties = ('title', 'short_title', 'created_by', 'organization', 'associated_dis', 'starting_date',
                      'ending_date', 'summary', 'description', 'mobile_description', 'outcome', 'tags')
        if not super(ChallengeEditor, self).commit((), properties):
            return False

        user_repository = UserRepository()
        created_by = user_repository.get_by_email(self.created_by.value)
        associated_dis = [user_repository.get_by_email(email) for email in self.associated_dis.value]

        challenge = self.challenge or self.challenge_repository.create()

        challenge.title = self.title.value
        challenge.short_title = self.short_title.value
        challenge.created_by = created_by
        challenge.organization = self.organization.value
        challenge.associated_dis = associated_dis
        challenge.starting_date = self.starting_date.value
        challenge.ending_date = self.ending_date.value + timedelta(days=1)  # ending_date is not included
        challenge.summary = self.summary.value
        challenge.description = self.description.value
        challenge.mobile_description = self.mobile_description.value
        challenge.outcome = self.outcome.value
        challenge.tags = self.tags.value

        # For each selected DI, if the corresponding account isn't DI, add the role to the user
        di_role = RoleType.Developer
        for u in associated_dis:
            u.add_role(di_role)

        return True
