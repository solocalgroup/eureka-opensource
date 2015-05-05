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

from nagare import security, var, component, editor
from nagare.database import session
from nagare.i18n import _, _N

from eureka.domain.repositories import (ChallengeRepository, IdeaRepository,
                                        DomainRepository)
from eureka.infrastructure.urls import get_url_service
from eureka.domain.services import get_workflow
from eureka.infrastructure import event_management, registry, validators, mail
from eureka.infrastructure.content_types import download_content_response
from eureka.infrastructure.validators import DateValidator
from eureka.infrastructure.tools import is_integer, generate_id
from eureka.infrastructure.security import get_current_user
from eureka.domain.models import StateData
from eureka.ui.common.yui2 import flashmessage
from eureka.ui.common.htmlcharts import BarChart
from eureka.ui.common.menu import Menu
from eureka.ui.desktop.comment import CommentCreator
from eureka.ui.desktop.workflow import IdeaWFContext, WorkflowSection
from eureka.ui.desktop.comment import CommentPager
from eureka.domain.queries import get_direction_label
from eureka.domain.models import OrganizationData
from eureka.domain.mail_notification import (_perform_substitutions,
                                             _extract_metadata, render_link)


class Idea(object):
    def __init__(self, parent, idea):
        event_management._register_listener(parent, self)

        self.id = idea if is_integer(idea) else idea.id
        self.display_date = 'publication_date'

        self.comment_pager = component.Component(CommentPager(self))
        self.comment_creator = component.Component(
            CommentCreator(self, self.id))
        self.comment_creator.on_answer(lambda a: self.comments_updated())

        self.wf_context = component.Component(IdeaWFContext(self.id))
        event_management._register_listener(self, self.wf_context())
        self.workflow_section = component.Component(WorkflowSection(self.id))
        event_management._register_listener(self, self.workflow_section())

        self.selected_tab = var.Var('')

        self.menu_items = []

        if self.has_comments():
            nb_comments = self.get_nb_comments()
            self.menu_items.append((
                _N(u"Comment (%d)", u"Comments (%d)",
                   nb_comments) % nb_comments,
                'comments', None, '', None
            ))

        if self.has_challenge():
            self.menu_items.append(
                (_(u"Challenge"), 'challenge', None, '', None))

        if self.has_tags():
            self.menu_items.append((_(u"Tags"), 'tags', None, '', None))

        self.menu = component.Component(Menu(self.menu_items),
                                        model='tab_renderer')
        self.menu.on_answer(self.select_tab)
        self.select_default_tab()

        self._navigate_to_element = None
        self._comment_submit_id = generate_id('comment-submit')

        self.display_full_description = var.Var(False)

    def comments_updated(self):
        if self.has_comments():
            nb_comments = self.get_nb_comments()
            label = _N(u"Comment (%d)", u"Comments (%d)",
                       nb_comments) % nb_comments
            if self.menu().has_entry('comments'):
                self.menu().change_label_entry('comments', label)
            else:
                menu_item = (label, 'comments', None, '', None)
                self.menu().add_entry_before(menu_item)
            self.select_tab_by_name('comments')
        else:
            if self.menu().has_entry('comments'):
                self.menu().remove_entry('comments')

        self.comment_pager().refresh_comments()

    def navigate_to_comment_submit(self):
        self._navigate_to_element = self._comment_submit_id

    @property
    def url(self):
        return get_url_service().expand_url(['idea', self.id])

    @property
    def absolute_url(self):
        return get_url_service().expand_url(['idea', self.id], relative=False)

    def select_tab(self, value):
        id = self.menu().select_by_index(value)
        self.selected_tab(id)

    def select_tab_by_name(self, name):
        self.menu().select_by_id(name)
        self.selected_tab(name)

    def select_default_tab(self):

        if self.has_challenge():
            self.select_tab_by_name('challenge')

        if self.has_tags():
            self.select_tab_by_name('tags')

        if self.has_comments():
            self.select_tab_by_name('comments')

    def profile_url(self, uid):
        return 'profile/%s' % uid

    def view_profile(self, uid):
        event_management._emit_signal(self, "VIEW_USER_PROFILE", user_uid=uid)

    def goto(self):
        event_management._emit_signal(self, "VIEW_IDEA", idea_id=self.id)

    @property
    def challenge(self):
        return self.i.challenge

    @property
    def domain(self):
        return self.i.domain

    def with_login(self, action, *args, **kwargs):
        event_management._emit_signal(self, "WITH_LOGIN", action, *args,
                                      **kwargs)

    def is_tracked(self):
        user = get_current_user()
        assert user
        return self.i in user.tracked_ideas

    def track_idea(self):
        user = get_current_user()
        assert user

        user.track_idea(self.id)
        flashmessage.set_flash(_(u'Idea added to tracking'))

    def untrack_idea(self):
        user = get_current_user()
        assert user
        user.untrack_idea(self.id)
        flashmessage.set_flash(_(u'Idea removed from tracking'))

    def edit_idea(self):
        event_management._emit_signal(self, "VIEW_IDEA", idea_id=self.i.id,
                                      mode=u"edit")

    def find_vote(self, user=None):
        user = user or get_current_user()
        assert user
        return self.i.find_vote(user)

    def vote(self, rate, user=None):
        user = user or get_current_user()

        if not security.has_permissions('vote_idea', self):
            flashmessage.set_flash(
                _("Sorry but you can't vote for this idea anymore"))
            return

        vote = self.find_vote(user)
        if not vote:
            self.i.vote(user, rate)
        elif user.is_dsig():  # a DSIG can cheat by voting more than once
            self.i.vote(user, rate + vote.rate)  # accumulate the rates

    @property
    def i(self):
        return IdeaRepository().get_by_id(self.id)

    def has_tags(self):
        return len(self.i.tags) > 0

    def has_challenge(self):
        return self.i.challenge is not None

    def has_comments(self):
        return self.get_nb_comments() > 0

    def get_all_comments(self):
        if security.has_permissions('view_moderated_comments', self):
            comments = [c for c in self.i.comments if not c.deleted]
        else:
            comments = [c for c in self.i.comments if
                        not c.moderated and not c.deleted]
        return reversed(comments)

    def get_nb_comments(self):
        return len(list(self.get_all_comments()))

    def change_state(self, state):
        self.i.wf_context.state = state

    def get_domains(self):
        return DomainRepository().get_all()

    def form_edit(self, comp):
        event_management._emit_signal(self, "EDIT_IDEA")

    @property
    def comments_attachments(self):
        return [(comment.attachment, comment.created_by)
                for comment in self.i.comments
                if comment.attachment and comment.visible]

    def download_attachment(self, filename_attr):
        file_number = filename_attr.split('_')[1]
        filename = getattr(self.i, 'filename_' + file_number)
        filedata = getattr(self.i, 'filedata_' + file_number)
        content_type = getattr(self.i, 'content_type_' + file_number)
        raise download_content_response(content_type, str(filedata), filename)

    def description_excerpt(self, n_lines):
        t = self.i.description.split('\n')
        if len(t) > n_lines:
            t = t[:n_lines] + ['...']
        return '\n'.join(t)

    @property
    def alert_date(self):
        return self.i.unchanged_state_reminder_date

    def change_alert_date(self, date):
        self.i.unchanged_state_reminder_date = DateValidator(date).to_date()

    def commit_alert_date(self):
        pass

    def delete(self):
        # Need to use session.delete to trigger delete cascades
        session.delete(self.i)
        flashmessage.set_flash(_(u'Idea deleted'))
        event_management._emit_signal(self, "VIEW_IDEAS")


class ShareIdeaWithFriends(editor.Editor):
    def __init__(self, idea_id):
        self.idea_id = idea_id
        self.sender_email = editor.Property(u'').validate(validators.email)
        self.recipients = editor.Property(u'').validate(
            validators.user_email_list)
        self.subject = editor.Property(self.default_subject).validate(
            validators.non_empty_string)
        self.message = editor.Property(self.default_message).validate(
            validators.non_empty_string)

    @property
    def idea_url(self):
        return get_url_service().expand_url(['idea', self.idea_id], relative=False)

    @property
    def user(self):
        user = security.get_user()
        if user:
            return user.entity

    @property
    def default_subject(self):
        return _(u"Eureka: this idea may interest you")

    @property
    def default_message(self):
        firstname = self.user.firstname if self.user else _('<Your firstname>')
        return _(u"Hello,\n\nConnect to Eurêka and take a look at this "
                 u"idea: %s\n\nCheers, %s") % (self.idea_url, firstname)

    def send_email(self):
        properties = ('recipients', 'subject', 'message')
        if not self.user:
            properties += ('sender_email',)

        if not self.is_validated(properties):
            return False  # failure

        recipients = self.recipients.value
        subject = self.subject.value
        message = self.message.value
        sender_email = self.user.email if self.user else self.sender_email.value
        mailer = mail.get_mailer()
        mailer.send_mail(subject=subject, from_=sender_email, to=recipients,
                         content=message)
        return True  # success


class ReportDuplicateIdea(object):
    def __init__(self, idea):

        self.idea = idea

        self.message = _('Report idea #%s as duplicated') % self.idea.id

        self.choices = [
            (DuplicateIdeaEditor, _('This idea is already submitted')),
            (DirectionIdeaEditor,
             _('This idea is already carried on by a direction'))]

        self.report = component.Component(self, model='report')

        self.menu = component.Component(Menu([elt[1] for elt in self.choices]))
        self.menu.on_answer(self.show_form)

        self.form = component.Component(None)

    def show_form(self, id):
        self.menu().selected(id)

        factory = self.choices[id][0]()
        elt_id, message, action = self.form.call(factory, model='form')

        if action in ['idea', 'direction']:
            if action == 'idea':
                idea = Idea(None, IdeaRepository().get_by_id(elt_id))
                self.send_email_idea(idea)
            else:
                direction_label = get_direction_label(elt_id)
                self.send_email_direction(direction_label, message)

            flashmessage.set_flash(_(
                u'Your message has been sent. Thank you for your awareness !'))

        self.idea.goto()

    def send_email_idea(self, idea):
        user = get_current_user()

        if user:
            mailer = mail.get_mailer()

            base_url = get_url_service().base_url

            substitutions = {
                u'SENDER': user.email,
                u'FIRSTNAME': user.firstname,
                u'LASTNAME': user.lastname,
                u'IDEA_LINK': self.idea.absolute_url,
                u'IDEA_ID': str(self.idea.id),
                u'OLD_IDEA_LINK': idea.absolute_url,
                u'OLD_IDEA_ID': str(idea.id),
                u'EUREKA_LINK': render_link(_(u'Eurêka'), base_url),
                u'RECIPIENTS': mailer.get_substitutions()[u'DSIG_EMAIL']
            }

            content = _perform_substitutions('mail-idea-duplicated.html',
                                             'fr', substitutions)
            (content, subject, sender, to_recipients,
             cc_recipients, bcc_recipients) = _extract_metadata(content)

            mailer.send_mail(subject, from_=sender, to=to_recipients,
                             cc=cc_recipients, bcc=bcc_recipients,
                             content=content, type='html')

    def send_email_direction(self, direction_label, message):
        user = get_current_user()

        if user:
            mailer = mail.get_mailer()

            base_url = get_url_service().base_url

            substitutions = {
                u'SENDER': user.email,
                u'FIRSTNAME': user.firstname,
                u'LASTNAME': user.lastname,
                u'IDEA_LINK': self.idea.absolute_url,
                u'IDEA_ID': str(self.idea.id),
                u'DIRECTION_LABEL': direction_label,
                u'MESSAGE': message,
                u'EUREKA_LINK': render_link(_(u'Eurêka'), base_url),
                u'RECIPIENTS': mailer.get_substitutions()[u'DSIG_EMAIL']
            }

            content = _perform_substitutions(
                'mail-idea-duplicated-direction.html',
                'fr', substitutions)
            (content, subject, sender, to_recipients,
             cc_recipients, bcc_recipients) = _extract_metadata(content)

            mailer.send_mail(subject, from_=sender, to=to_recipients,
                             cc=cc_recipients, bcc=bcc_recipients,
                             content=content, type='html')


class DuplicateIdeaEditor(editor.Editor):
    def __init__(self):
        super(DuplicateIdeaEditor, None)

        self.value = editor.Property(u'')
        validator = lambda v: validators.ExtendedIntValidator(v, msg=_(
            u'Idea id must be an integer')).to_int()
        self.value.validate(validator)

    def submit(self, comp):
        if self.commit((), ('value', )):
            idea_data = IdeaRepository().get_by_id(int(self.value()))
            if idea_data:
                comp.answer((int(self.value()), '', 'idea'))
            else:
                self.value.error = _('No such idea')


class DirectionIdeaEditor(editor.Editor):
    def __init__(self):
        super(DirectionIdeaEditor, None)

        self.value = editor.Property(u'')
        validator = lambda v: validators.ExtendedIntValidator(v, msg=_(
            u'Idea id must be an integer')).to_int()
        self.value.validate(validator)

        self.message = editor.Property(u'')

    @property
    def choices(self):
        return OrganizationData.get_directions()

    def submit(self, comp):
        if self.commit((), ('value', 'message')):
            comp.answer((int(self.value()), self.message(), 'direction'))


class SubmitIdeaBox(object):
    ActiveChallenge = object()

    def __init__(self, parent, challenge=ActiveChallenge):
        if parent:
            self.bind_parent(parent)

        if challenge is self.ActiveChallenge:
            self.challenge_id = self._active_challenge_id
        else:
            self.challenge_id = challenge if ((challenge is None) or is_integer(challenge)) else challenge.id

    @property
    def _active_challenge_id(self):
        challenges = list(ChallengeRepository().get_by_active_at_date())
        return challenges[0].id if challenges else None

    @property
    def submit_idea_url(self):
        if not self.challenge_id:
            return get_url_service().expand_url(['submit'])

        return get_url_service().expand_url(['submit', self.challenge_id])

    def bind_parent(self, parent):
        event_management._register_listener(parent, self)

    def submit_idea(self):
        event_management._emit_signal(self, "SUBMIT_IDEA",
                                      challenge_id=self.challenge_id)

    def with_login(self, action):
        event_management._emit_signal(self, "WITH_LOGIN", action)


class IdeaBarChart(object):
    def __init__(self, parent):
        event_management._register_listener(parent, self)

        items = StateData.get_ideas_count_by_states(get_workflow().get_chart_states())
        self.items = [(r.state, r.count) for r in reversed(items.all())]
        self.chart = component.Component(
            BarChart(self.items, _('Your ideas have potential'), clickable=True)
        )

        self.chart.on_answer(self.call_ideas)

    def call_ideas(self, state):
        event_management._emit_signal(self, "VIEW_IDEAS_WITH_STATE", state=state)
