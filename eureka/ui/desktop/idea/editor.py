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
from sqlalchemy import func

from nagare import editor
from nagare.i18n import _

from eureka.domain.models import AttachmentData
from eureka.domain.models import DomainData
from eureka.domain.models import TagData
from eureka.domain.services import get_workflow
from eureka.domain.repositories import (ChallengeRepository, UserRepository,
                                        IdeaRepository, DomainRepository)
from eureka.infrastructure.workflow.workflow import process_event as wf_process_event
from eureka.infrastructure import event_management, validators
from eureka.infrastructure.tools import fix_filename
from eureka.infrastructure.security import get_current_user
from eureka.ui.desktop.attachment import validate_attachment
from eureka.ui.common.yui2 import flashmessage


class IdeaEditor(editor.Editor):
    def __init__(self, parent, suggested_challenge_id=None):
        super(IdeaEditor, self).__init__(None)
        event_management._register_listener(parent, self)

        self.idea = None

        # mandatory fields
        self.title = editor.Property(u'').validate(validators.non_empty_string)
        self.description = editor.Property(u'').validate(
            validators.non_empty_string)
        self.domain_id = editor.Property(u'').validate(
            validators.non_empty_string)
        self.challenge_id = editor.Property(
            suggested_challenge_id or u'').validate(
            validators.non_empty_string)
        self.impact = editor.Property(u'').validate(
            validators.non_empty_string)
        self.tags = editor.Property(u'').validate(
            lambda t: validators.word_list(t, required=True,
                                           duplicates='remove'))

        # Optional fields
        self.benefit_department = editor.Property(u'').validate(
            validators.string)
        self.origin = editor.Property(u'').validate(validators.string)
        self.implementation = editor.Property(u'').validate(validators.string)
        self.co_author_1 = editor.Property(u'').validate(validators.user_email)
        self.co_author_2 = editor.Property(u'').validate(validators.user_email)
        self.co_author_3 = editor.Property(u'').validate(validators.user_email)
        self.co_author_4 = editor.Property(u'').validate(validators.user_email)
        self.co_author_5 = editor.Property(u'').validate(validators.user_email)

        self.attachment_1 = editor.Property(None).validate(validate_attachment)
        self.attachment_2 = editor.Property(None).validate(validate_attachment)
        self.attachment_3 = editor.Property(None).validate(validate_attachment)

        # checkboxes
        self.anonymous = editor.Property(False)
        self.already_done = editor.Property(False)

    def get_domains(self):
        return DomainData.query.order_by(DomainData.rank)

    def get_active_challenges(self, date):
        return list(ChallengeRepository().get_by_active_at_date(date))

    def get_tags(self):
        return [tag.label for tag in TagData.query.all()]

    def get_or_create_tag(self, label):
        tag = TagData.query.filter(
            func.lower(TagData.label) == func.lower(label)).first()
        if not tag:
            tag = TagData(label=label)
        return tag

    def edit_idea(self, draft):
        # read the fields
        submission_date = self.idea.i.submission_date if self.idea else datetime.now()
        title = self.title.value
        description = self.description.value
        impact = self.impact.value
        domain = DomainRepository().get_by_id(self.domain_id.value)

        challenge_id = self.challenge_id.value
        challenge = ChallengeRepository().get_by_id(
            challenge_id) if challenge_id else None
        # make sure the challenge was active at the submission_date
        if challenge and not challenge.is_active(submission_date):
            challenge = None

        tags = [self.get_or_create_tag(tag.lower()) for tag in self.tags.value]

        # create or update the idea
        # mandatory fields
        mandatory_fields = dict(
            title=title,
            description=description,
            impact=impact,
            domain=domain,
            challenge=challenge,
            tags=tags,
        )

        if not self.idea:
            idea = IdeaRepository().create(submitted_by=get_current_user(),
                                           submission_date=submission_date,
                                           **mandatory_fields)
        else:
            idea = IdeaRepository().get_by_id(self.idea.id)
            idea.set(**mandatory_fields)

        # Optional fields
        idea.benefit_department = self.benefit_department.value
        idea.origin = self.origin.value
        idea.implementation = self.implementation.value

        self.update_idea_authors(idea)

        for attr in ('attachment_1', 'attachment_2', 'attachment_3'):
            property_value = getattr(self, attr).value
            if property_value is not None:
                idea_attachment = getattr(idea, attr)
                if idea_attachment:
                    setattr(idea, attr, None)
                    # idea_attachment.delete()
                setattr(idea, attr, self.create_attachement(property_value))

        idea.show_creator = not self.anonymous.value
        idea.already_done = self.already_done.value

        # workflow
        workflow = get_workflow()
        draft_event = workflow.WFEvents.DRAFT_EVENT
        submit_event = workflow.WFEvents.SUBMIT_EVENT

        def process_event(idea, event):
            wf_process_event(from_user=get_current_user(),
                             idea=idea,
                             event=event,
                             notify=flashmessage.set_flash)

        if draft:  # save as a draft
            process_event(idea, draft_event)
        else:  # submit the idea
            process_event(idea, submit_event)

        return idea

    def update_idea_authors(self, idea):
        co_authors = [self.co_author_1.value, self.co_author_2.value,
                      self.co_author_3.value, self.co_author_4.value,
                      self.co_author_5.value]
        authors = [idea.submitted_by]
        user_repository = UserRepository()
        for email in co_authors:
            if email:
                email = email.strip().lower()
                authors.append(user_repository.get_by_email(email))
        idea.authors = authors

    @property
    def can_submit_draft(self):
        idea = self.idea
        return idea is None or idea.i.wf_context.state.label == get_workflow().WFStates.DRAFT_STATE

    def view_idea(self, idea_id):
        event_management._emit_signal(self, "VIEW_IDEA", mode='view',
                                      idea_id=idea_id)

    def update_idea(self, draft=False):
        properties = (
            'title', 'description', 'impact', 'tags', 'domain_id',
            'co_author_1',
            'co_author_2',
            'co_author_3', 'co_author_4', 'co_author_5',
            'attachment_1', 'attachment_2', 'attachment_3',
            'benefit_department')
        if super(IdeaEditor, self).commit((), properties):
            idea = self.edit_idea(draft)
            self.view_idea(idea.id)

    def reset_values(self):
        self.anonymous(False)
        self.already_done(False)

    def create_attachement(self, uploaded_file):
        return AttachmentData(filename=fix_filename(uploaded_file['filename']),
                              mimetype=uploaded_file['content_type'],
                              data=uploaded_file[
                                  'filedata']) if uploaded_file else None

    def delete_idea(self):
        self.idea.i.delete()
        flashmessage.set_flash(_(u'Idea deleted'))
        event_management._emit_signal(self, "VIEW_IDEAS")


# FIXME: to be merged to the IdeaEditor
class IdeaUpdater(IdeaEditor):
    def __init__(self, idea):
        super(IdeaUpdater, self).__init__(idea)
        self.idea = idea

        #  mandatory fields
        self.title(idea.i.title)
        self.description(idea.i.description)
        if idea.i.domain:
            self.domain_id(str(idea.i.domain.id))
        if idea.i.challenge:
            self.challenge_id(str(idea.i.challenge.id))
        self.impact(idea.i.impact)

        # Optional fields
        self.origin(idea.i.origin)
        self.benefit_department(idea.i.benefit_department)
        self.implementation(idea.i.implementation)
        coauthors = idea.i.authors[1:]
        if len(coauthors) > 0:
            self.co_author_1(coauthors[0].email)
        if len(coauthors) > 1:
            self.co_author_2(coauthors[1].email)
        if len(coauthors) > 2:
            self.co_author_3(coauthors[2].email)

        self.tags(', '.join([t.label for t in idea.i.tags]) + ', ')

        self.anonymous(not idea.i.show_creator)
        self.already_done(idea.i.already_done)
