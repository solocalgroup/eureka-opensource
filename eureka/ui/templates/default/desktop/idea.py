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

from nagare import component, presentation, security
from nagare.i18n import _, _N, format_datetime, format_date

from eureka.domain.models import IdeaData, attachments_max_size
from eureka.domain.queries import (get_all_published_ideas,
                                   get_idea_published_tag,
                                   search_users_fulltext, get_tags)
from eureka.domain.services import get_workflow
from eureka.infrastructure import event_management
from eureka.infrastructure.tools import limit_string, text_to_html_elements
from eureka.ui.common.yui2 import Autocomplete
from eureka.ui.common.yui2 import Calendar
from eureka.ui.desktop.attachment import Attachment
from eureka.ui.desktop.challenge import Challenge
from eureka.ui.desktop.user import User

from eureka.ui.desktop.idea import (ShareIdeaWithFriends, Idea, SubmitIdeaBox,
                                    ReportDuplicateIdea, DuplicateIdeaEditor,
                                    DirectionIdeaEditor, IdeaBarChart,
                                    IdeasActivityPager, IdeasActivityPagerMenu,
                                    IdeaPager, IdeaPagerBox, IdeasFilters,
                                    IdeaEditor)


def render_challenge_tags(idea, h):
    elements = []
    challenge = idea.challenge
    for t in challenge.tags:
        elements.append(h.span(class_='tag-%s' % t))
    return elements


@presentation.render_for(ReportDuplicateIdea)
def render_report_duplicate(self, h, comp, *args):
    with h.div:
        with h.h1(class_='tab active big'):
            with h.span:
                h << h.a(self.message)

    with h.div(class_='report-duplicate-idea'):
        h << self.report.render(h.AsyncRenderer())
    return h.root


@presentation.render_for(ReportDuplicateIdea, model='report')
def render_report_duplicate_report(self, h, comp, *args):
    h << self.menu
    if self.form():
        h << self.form.render(h.SyncRenderer())
    return h.root


@presentation.render_for(DuplicateIdeaEditor, model='form')
def render_ask(self, h, comp, *args):
    with h.form(name='report'):
        with h.div(class_='fields'):
            with h.div(class_='field'):
                h << h.label(_('Please fill in idea number'))
                h << h.input(type='text', name='idea_id',
                             value=self.value()).action(self.value).error(
                    self.value.error)

        with h.div(class_='buttons'):
            h << h.input(type='submit',
                         value=_('Send email'),
                         class_='confirm-button').action(
                lambda: self.submit(comp))
    return h.root


@presentation.render_for(DirectionIdeaEditor, model='form')
def render_direction_idea_editor(self, h, comp, *args):
    with h.form(name='report'):
        with h.div(class_='fields'):

            with h.div(class_='field'):
                h << h.label(_('Please pick a direction'))
                with h.select(name='direction_id').action(self.value):
                    for label, choice in self.choices:
                        h << h.option(label, value=choice).selected(
                            [self.value()])

            with h.div(class_='field'):
                h << h.label(_('Can you tell us more ?'))
                h << h.textarea(self.message(), class_='comment',
                                name='direction_message').action(self.message)

        with h.div(class_='buttons'):
            h << h.input(type='submit',
                         value=_('Send email'),
                         class_='confirm-button').action(
                lambda: self.submit(comp))
    return h.root


@presentation.render_for(Idea, model='submitter_name')
def render_idea_submitter_name(self, h, comp, *args):
    user_comp = component.Component(User(self, self.i.submitted_by.uid))
    h << user_comp.render(h, model="fullname")
    return h.root


@presentation.render_for(Idea, model='submitter_avatar')
def render_idea_submitter_avatar(self, h, comp, *args):
    user = User(self, self.i.submitted_by.uid)
    user_comp = component.Component(user)
    h << user_comp.render(h, model="avatar90")
    h << h.div(h.a(user.user.fullname).action(lambda: self.view_profile(user.uid)), class_='name')
    h << h.small(user.user.status_level_label, class_='title')

    return h.root


@presentation.render_for(Idea, model='authors_names')
def render_idea_authors_names(self, h, comp, *args):
    with h.span(class_='authors'):
        for index, author in enumerate(self.i.authors):
            if index > 0:
                h << ', '
            user_comp = component.Component(User(self, author))
            h << user_comp.render(h, model="fullname")
    return h.root


@presentation.render_for(Idea, model='title')
def render_idea_title(self, h, comp, *args):
    with h.h1:
        h << h.a(self.i.title, href=self.url)

    return h.root


@presentation.render_for(Idea, model='short_link')
def render_idea_short_link(self, h, comp, *args):
    with h.a(href=self.url):
        with h.span(class_='idea-number'):
            h << _(u'#%d') % self.i.id
        h << ' - '
        h << self.i.title
    return h.root


@presentation.render_for(Idea, model='info')
def render_idea_info(self, h, comp, *args):
    with h.small(class_="post"):
        # idea number

        id_ = self.id
        date = getattr(self.i.wf_context, self.display_date)
        if date:
            h << _(u'N°%d posted at %s') % (id_, format_datetime(date))
        else:
            h << _(u'N°%d') % id_

    return h.root


@presentation.render_for(Idea, model='link')
def render_idea_link(self, h, comp, *args):
    h << h.a(_(u'Read more'), class_='more')

    return h.root


@presentation.render_for(Idea, model='challenge_icon')
def render_idea_challenge_icon(self, h, comp, *args):
    if self.i.challenge:
        title = _(u'Challenge: %s') % self.i.challenge.title
        h << h.span(h.i(class_='icon-light'), title=title)
        h << render_challenge_tags(self, h)

    return h.root


@presentation.render_for(Idea, model='summary_short')
def render_idea_summary_short(self, h, comp, *args):
    with h.span(class_='idea-summary'):
        h << comp.render(h, model="title")
        h << comp.render(h, model="info")
    return h.root


@presentation.render_for(Idea, model='summary')
def render_idea_summary(self, h, comp, *args):
    h << comp.render(h, model="title")
    h << comp.render(h.AsyncRenderer(), model="description_excerpt")
    h << comp.render(h, model="info")

    return h.root


@presentation.render_for(Idea, model='description_excerpt')
def render_idea_description_excerpt(self, h, comp, *args):
    limit = 420
    if len(self.i.description) > limit:
        description = limit_string(self.i.description, limit)
        display_more = True
    else:
        description = self.i.description
        display_more = False

    if display_more and not self.display_full_description():
        h << h.p(text_to_html_elements(h, description), class_="description")
        h << h.a(_(u'Read more'), class_='more').action(
            lambda: self.display_full_description(True))
    elif display_more and self.display_full_description():
        h << h.p(text_to_html_elements(h, self.i.description),
                 class_="description")
        h << h.a(_(u'Read less'), class_='more').action(
            lambda: self.display_full_description(False))
    else:
        h << h.p(text_to_html_elements(h, description), class_="description")

    return h.root


@presentation.render_for(Idea, model='change_tracking')
def render_idea_change_tracking(self, h, comp, *args):
    if security.has_permissions('track_idea', self):
        if security.get_user() and self.is_tracked():
            label = _(u'I untrack this idea')
            h << h.a(h.i(class_='icon-heart-small'),
                     title=label,
                     class_='untrack-idea').action(
                lambda: self.with_login(self.untrack_idea))
        else:
            label = _(u'I track this idea')
            h << h.a(h.i(class_='icon-heart-small-broken'),
                     title=label,
                     class_='track-idea').action(
                lambda: self.with_login(self.track_idea))

    return h.root


@presentation.render_for(Idea, model='list_tools')
def render_idea_list_tools(self, h, comp, *args):
    with h.div(class_="toolbar"):
        # show idea
        label = _(u'View the idea, comment, vote for it')
        h << h.a(label,
                 title=label,
                 class_="edit-comment",
                 href=self.url)

        # tracking
        h << comp.render(h, model='change_tracking')

    return h.root


@presentation.render_for(Idea, model='table_row')
def render_idea_table_row(self, h, comp, *args):

    with h.td(class_="title"):
        h << h.a(self.i.title, href=self.url).action(
            lambda: event_management._emit_signal(self, "VIEW_IDEA", idea_id=self.i.id))

    for user in self.i.authors:
        h << h.td(h.a(
            user.firstname, " ", user.lastname,
            href='profile/' + user.uid
        ).action(lambda uid=user.uid: event_management._emit_signal(self,
                                                                    "VIEW_USER_PROFILE",
                                                                    user_uid=uid)))

    h << h.td(format_date(self.i.submission_date, format='short'))
    h << h.td(self.i.total_votes)
    h << h.td(self.get_nb_comments())

    with h.td:
        a = h.a(
            self.i.domain.i18n_label,
            " (",
            get_all_published_ideas().filter(IdeaData.domain == self.i.domain).count(),
            ")"
        )

        a = a.action(lambda label=self.i.domain.i18n_label, id=self.i.domain.id: event_management._emit_signal(self, "VIEW_DOMAIN_IDEAS", domain_id=id, domain_label=label))
        h << a

    return h.root


@presentation.render_for(Idea, model='step')
def render_idea_step(self, h, comp, *args):
    h << self.wf_context.render(h, model='step')
    return h.root


@presentation.render_for(Idea, model='detail')
def render_idea_detail(self, h, comp, *args):
    with h.section(
            class_='idea %s' % self.i.domain.label.lower().replace('_', '-')):
        # early exit
        if not security.has_permissions('view_idea', self):
            h << _(u"You are not allowed to view this idea")
            return h.root

        h << comp.render(h, model='step')

        with h.div(class_='user'):
            h << comp.render(h, model="submitter_avatar")
            h << comp.render(h, model='score_vote')

        with h.div(class_='idea-content'):
            h << comp.render(h, model='info')

            a = h.a(
                self.i.domain.i18n_label,
                " (",
                get_all_published_ideas().filter(IdeaData.domain == self.i.domain).count(),
                ")",
                class_='thematic'
            )

            a = a.action(lambda label=self.i.domain.i18n_label, id=self.i.domain.id: event_management._emit_signal(self, "VIEW_DOMAIN_IDEAS", domain_id=id, domain_label=label))
            h << a
            h << comp.render(h, model='description')
            h << comp.render(h, model='detail_tools')

    class_ = ('tab-content comments %s' %
              self.i.domain.i18n_label.lower().replace('_', '-'))
    with h.section(class_=class_):

        # --------------------------------------
        # ajax renderer
        async = h.AsyncRenderer()

        # comment submission
        if security.has_permissions('submit_comment', self):
            h << comp.render(h, model="comment_submit")

        # info tabs
        h << component.Component(self).render(async, model="info_tabs")

        # workflow section
        h << self.workflow_section.render(async)

        # --------------------------------------

        if self._navigate_to_element:
            h << h.script(
                'document.getElementById("%s").scrollIntoView();' % self._navigate_to_element,
                type='text/javascript')
            self._navigate_to_element = None

    return h.root

    with h.div(class_='idea-details'):
        # early exit
        if not security.has_permissions('view_idea', self):
            h << _(u"You are not allowed to view this idea")
            return h.root

        # ajax renderer
        async = h.AsyncRenderer()

        # first author avatar
        h << component.Component(User(self, self.i.submitted_by.uid),
                                 model='avatar_photo')

        with h.div(class_='body'):
            # idea metadata
            h << comp.render(h, model='metadata')

            # domain
            with h.div(class_="tab active"):
                with h.span:

                    a = h.a(
                        self.i.domain.i18n_label,
                        " (",
                        get_all_published_ideas().filter(IdeaData.domain == self.i.domain).count(),
                        ")"
                    )

                    a = a.action(
                        lambda label=self.i.domain.i18n_label, id=self.i.domain.id: event_management._emit_signal(self, "VIEW_DOMAIN_IDEAS", domain_id=id, domain_label=label)
                    )

                    h << a

            with h.div(class_='content'):
                # score and vote
                h << comp.render(h, model='score_vote')
                # description
                h << comp.render(h, model='description')

            # toolbar
            h << comp.render(h, model='detail_tools')

        if self._navigate_to_element:
            h << h.script(
                'document.getElementById("%s").scrollIntoView();' % self._navigate_to_element,
                type='text/javascript')
            self._navigate_to_element = None

    return h.root


@presentation.render_for(Idea, model='metadata')
def render_idea_metadata(self, h, comp, *args):
    with h.div(class_="metadata"):
        with h.div(class_='authors'):
            for idx, user in enumerate(self.i.authors):
                if idx > 0:
                    h << ', '
                label = user.fullname
                h << h.a(label,
                         title=label,
                         href=self.profile_url(user.uid)).action(
                    lambda uid=user.uid: self.view_profile(uid))

        with h.div(class_='metainfo'):
            h << _(u'#%d') % self.id << ' '
            h << _(u'submitted on') << ' '
            h << format_datetime(self.i.submission_date)

        h << comp.render(h, model='step')

    return h.root


@presentation.render_for(Idea, model='description')
def render_idea_description(self, h, comp, *args):
    with h.div(class_='description'):
        with h.h1:
            h << self.i.title
            h << comp.render(h, model='challenge_icon')

        h << h.p(text_to_html_elements(h, self.i.description))

        attachments = [getattr(self.i, 'attachment_%d' % (i + 1)) for i in
                       range(3)]
        attachment_comps = [component.Component(Attachment(attachment)) for
                            attachment in attachments
                            if attachment is not None]
        if attachment_comps:
            with h.ul(class_='attachments ideas'):
                for attachment_comp in attachment_comps:
                    with h.li:
                        h << attachment_comp.render(h)

        if self.i.origin:
            h << h.h2(_(u'Origin'))
            h << h.p(text_to_html_elements(h, self.i.origin))

        if self.i.impact:
            h << h.h2(_(u'Impact/benefit for the corporation'))
            h << h.p(text_to_html_elements(h, self.i.impact))

        if self.i.implementation:
            h << h.h2(_(u'Implementation'))
            h << h.p(text_to_html_elements(h, self.i.implementation))

        if self.comments_attachments:
            h << h.h2(_(u'Attachments contributed in comments'))
            with h.ul(class_='attachments comments'):
                for (attachment, by_user) in self.comments_attachments:
                    with h.li:
                        h << component.Component(
                            Attachment(attachment)).render(h) << ' '
                        with h.span(class_='author'):
                            h << '(' << _(u'from') << ' '
                            h << component.Component(
                                User(self, by_user)).render(h,
                                                            model="fullname")
                            h << ')'

        # refused idea: show the last workflow comment that explains why
        if self.wf_context().is_refused():
            h << self.wf_context.render(h, model='last_comment')

    return h.root


@presentation.render_for(Idea, model='unchanged_state_alert')
def render_idea_unchanged_state_alert(self, h, comp, *args):
    alert_date = self.alert_date
    if not alert_date:
        return h.root

    formatted_date = format_date(alert_date)
    label = _(u'Alert on %s') % formatted_date
    if security.has_permissions('edit_alert', self):
        calendar = Calendar('unchanged_state_alert_date',
                            title=_(u'Edit the alert setting'),
                            close_button=True,
                            on_select="document.unchanged_state_alert_date_form.ok_button.click()",
                            curdate=alert_date,
                            mindate=datetime.now())

        h << component.Component(calendar)

        h << h.a(h.i(class_='icon-clock'),
                 href='javascript:' + calendar.show(),
                 title=label,
                 class_="remind-idea")

        with h.form(name='unchanged_state_alert_date_form'):
            h << h.input(type='hidden',
                         id='unchanged_state_alert_date').action(
                self.change_alert_date)
            # get around a nagare bug not calling ajax callbacks when there's no submit button
            # or no action on the submit button
            h << h.input(type='submit',
                         name='ok_button',
                         value=_(u'Ok'),
                         class_='hidden').action(self.commit_alert_date)
    else:
        h << h.a(label,
                 title=label,
                 class_="remind-idea")

    return h.root


@presentation.render_for(Idea, model='list-items')
def render_idea_detail_tools(self, h, comp, *args):
    with h.tr(class_='ideas-list-items'):
        with h.td(class_=self.i.domain.label.lower().replace('_', '-')):
            with h.div(class_='wrapper'):
                h << self.wf_context.render(h, model='challenge-step')
                if self.i.challenge:
                    title = self.i.challenge.title
                    h << h.i(title=title, alt=title, class_="icon-light")
                user_comp = component.Component(
                    User(self, self.i.submitted_by.uid))
                h << user_comp.render(h, model="avatar90")
                h << h.a(
                    self.i.title,
                    href=self.url, class_='title'
                ).action(
                    lambda: event_management._emit_signal(self, "VIEW_IDEA",
                                                          idea_id=self.i.id))

                h << h.small(
                    _(u'#%d') % self.id,
                    ' ',
                    _(u'submitted on'),
                    ' ',
                    format_datetime(self.i.submission_date),
                    ' ',
                    comp.render(h, model='authors_names')
                )

        h << h.td(self.get_nb_comments())
        h << h.td(self.i.total_votes)

    return h.root


@presentation.render_for(Idea, model='detail_tools')
def render_idea_detail_tools(self, h, comp, *args):
    async = h.AsyncRenderer()
    with h.div(class_="links"):

        # delete
        if security.has_permissions('delete_idea', self):

            js = ('return yuiConfirm(this.href, "%s", "%s")' %
                  (_(u'Confirm delete?'),
                   _(u'This idea will be deleted permanently: are you sure?')))

            label = _(u'I delete the idea')
            h << h.a(h.i(class_='icon-close'),
                     title=label,
                     class_="delete-idea",
                     onclick=js).action(self.delete)

        # report duplicate
        if security.has_permissions('report_duplicate', self):
            label = _(u'I report a duplicate idea')
            h << h.a(h.i(class_='icon-remark-small'),
                     title=label,
                     class_="report-duplicate-idea").action(
                lambda: comp.call(ReportDuplicateIdea(self)))

        # edit idea
        if security.has_permissions('edit_idea', self):
            label = _(u'I Edit')
            if self.wf_context().state in get_workflow().get_author_edit_states():
                label = _(u'I Develop')
            h << h.a(h.i(class_='icon-edit'),
                     title=label,
                     href=self.url, class_="edit-idea").action(self.edit_idea)

        # send idea to a friend
        if security.has_permissions('email_idea', self):
            label = _(u'Share with a friend')
            h << h.a(h.i(class_='icon-mail'),
                     title=label,
                     class_="email-idea").action(
                lambda: comp.call(ShareIdeaWithFriends(self.id)))

        # tracking
        h << comp.render(h, model='change_tracking')

        # navigate to the comment submission form
        if security.has_permissions('submit_comment', self):
            link = h.a(h.i(class_='icon-speak-small'),
                       title=_(u'I comment'),
                       href='#%s' % self._comment_submit_id,
                       class_='comment-idea')

            if not security.get_user():
                link.action(
                    lambda: self.with_login(self.navigate_to_comment_submit))

            h << link

        # alert
        if security.has_permissions('view_alert', self):
            with h.div(class_='idea-action'):
                h << component.Component(self).render(async,
                                                      model='unchanged_state_alert')

    return h.root


@presentation.render_for(Idea, model='score_vote')
def render_idea_score_vote(self, h, comp, *args):
    if security.has_permissions('vote_idea', self):
        h << h.h3(_(u'I vote!'))
        for rate in range(1, 4):
            h << h.a('+%d' % rate, class_='vote').action(
                lambda rate=rate: self.with_login(self.vote, rate))

    h << h.h3(_(u'Score'))
    with h.div(class_="score"):
        h << self.i.total_votes

    return h.root


@presentation.render_for(Idea, model='comment_submit')
def render_idea_comment_submit(self, h, comp, *args):
    with h.div(id=self._comment_submit_id):
        h << self.comment_creator.render(h)
    return h.root


@presentation.render_for(Idea, model='info_tabs')
def render_idea_info_tabs(self, h, comp, *args):
    if not (self.has_tags() or self.has_challenge() or self.has_comments()):
        return h.root

    h << self.menu

    with h.div(class_="tab-content"):
        h << comp.render(h, model="tab_" + self.selected_tab())

    return h.root


@presentation.render_for(Idea, model='tab_comments')
def render_idea_tab_comments(self, h, comp, *args):
    h << self.comment_pager.render(h)
    return h.root


@presentation.render_for(Idea, model='tab_challenge')
def render_idea_tab_challenge(self, h, comp, *args):
    with h.div(class_='challenge-info'):
        challenge = Challenge(self, self.i.challenge.id)
        h << component.Component(challenge).render(h, model="banner")
    return h.root


@presentation.render_for(Idea, model='tab_tags')
def render_idea_tab_tags(self, h, comp, *args):
    h << comp.render(h.SyncRenderer(), model='tags')
    return h.root


@presentation.render_for(Idea, model='tags')
def render_idea_tags(self, h, comp, *args):
    for t in get_idea_published_tag(self.id):
        if t[1] > 0:
            h << h.a(t[0]).action(
                lambda label=t[0]: event_management._emit_signal(self,
                                                                 "VIEW_TAG_IDEAS",
                                                                 label=label))
        else:
            h << h.span(t[0])

        h << " "

    return h.root


# ---------------------------------------

@presentation.render_for(ShareIdeaWithFriends)
def render_share_idea_with_friends(self, h, comp, *args):
    with h.div(class_='share-idea-with-friends'):
        with h.h1(class_='tab active big'):
            with h.span:
                h << h.a(_(u'Share the idea with friends'))

        with h.form:
            with h.div(class_='fields'):
                if not self.user:
                    with h.div(class_='sender-field field'):
                        h << h.label(_(u'Your email address'))
                        h << h.input(type='text',
                                     class_='text wide',
                                     value=self.sender_email()).action(
                            self.sender_email).error(self.sender_email.error)

                with h.div(class_='recipients-field field'):
                    with h.label:
                        h << _(u'Recipients')
                        with h.span(class_='legend'):
                            h << _(
                                u"If there's more than one recipient, separate them with a comma")

                    autocomplete = Autocomplete(
                        lambda s: search_users_fulltext(s, limit=20),
                        delim_char=",",
                        type='text',
                        class_='text wide',
                        max_results_displayed=20,
                        value=self.recipients(),
                        action=self.recipients,
                        error=self.recipients.error)
                    h << component.Component(autocomplete).render(h)

                with h.div(class_='subject-field field'):
                    h << h.label(_(u'Subject'))
                    h << h.input(type='text',
                                 class_='text wide',
                                 value=self.subject()).action(
                        self.subject).error(self.subject.error)

                with h.div(class_='message-field field'):
                    h << h.label(_(u'Message'))
                    h << h.textarea(self.message(),
                                    class_='wide',
                                    rows=15).action(self.message).error(
                        self.message.error)

            with h.div(class_='buttons'):
                h << h.input(type='submit',
                             value=_(u'Send the email'),
                             class_='confirm-button').action(
                    lambda: self.send_email() and comp.answer(True))
                h << h.input(type='submit',
                             value=_(u'Cancel'),
                             class_='confirm-button').action(
                    lambda: comp.answer(False))

    return h.root


# ---------------------------------------

class SortFieldFactory(object):
    def __init__(self, text, hint_asc, hint_desc, cls_prefix, order):
        self.text = text
        self.hint_asc = hint_asc
        self.hint_desc = hint_desc
        self.cls_prefix = cls_prefix
        self.order = order

    def create_for(self, h, pager, use_icon=False):

        if use_icon:
            return self._create_for_icon(h, pager)
        else:
            return self._create_for(h, pager)

    def _create_for_icon(self, h, pager):

        if pager._order.startswith(self.order):
            if pager._order.endswith('_desc'):
                cls = 'active icon-down'
                tt = self.hint_asc
                target_order = self.order
            else:
                cls = 'active icon-up'
                tt = self.hint_desc
                target_order = self.order + '_desc'
        else:
            cls = "icon-down"
            tt = self.hint_desc
            target_order = self.order + '_desc'

        return h.a(h.i(class_=cls), self.text, href='ideas', title=tt).action(
            lambda: pager.change_order(target_order))

    def _create_for(self, h, pager):
        if pager._order == self.order + '_desc':
            cls = self.cls_prefix
            tt = self.hint_asc
            target_order = self.order
        else:
            cls = (self.cls_prefix + ' down' if pager._order == self.order
                   else self.cls_prefix)
            tt = self.hint_desc
            target_order = self.order + '_desc'

        return h.a(self.text, title=tt, href='ideas', class_=cls).action(
            lambda: pager.change_order(target_order))


# ---------------------------------------

@presentation.render_for(IdeaPager, model='tabs')
def render_idea_pager_tabs(self, h, comp, *args):
    h << self.menu
    return h.root


@presentation.render_for(IdeaPager, model='sort')
def render_idea_pager_sort(self, h, comp, *args):
    factories = [
        SortFieldFactory(_(u'Publication date'),
                         _(u'Sort from oldest to latest'),
                         _(u'Sort from latest to oldest'),
                         'pub-date date', 'publication_date'),
        SortFieldFactory(_(u'Recommendation date'),
                         _(u'Sort from oldest to latest'),
                         _(u'Sort from latest to oldest'),
                         'rec-date date', 'recommendation_date'),
        SortFieldFactory(_(u'Comments'),
                         _(u'Sort ascendingly'), _(u'Sort descendingly'),
                         'com', 'total_comments'),
        SortFieldFactory(_(u'Votes'),
                         _(u'Sort ascendingly'), _(u'Sort descendingly'),
                         'note', 'total_votes')]

    # creates a sort_criterion => SortFieldFactory mapping
    factory_by_order = dict(map(lambda f: (f.order, f), factories))

    # adds the requested sort criteria
    with h.div(class_="sorts"):
        criteria = self.sort_criteria
        criteria = [c for c in criteria if c in factory_by_order.keys()]

        for c in criteria:
            c = c.replace('_desc', '')
            h << factory_by_order[c].create_for(h, self)

    return h.root


@presentation.render_for(IdeaPager, model='list')
def render_idea_pager_list(self, h, comp, *args):
    ideas = self.get_ideas()

    if not ideas:
        with h.p(class_='empty'):
            h << _(u'No idea found')
        return h.root

    # displays the ideas
    with h.ul(class_="home-items"):
        # FIXME: this code should be moved into an idea "item" view
        progressing_ideas_states = get_workflow().get_progressing_ideas_states()
        h1 = h.SyncRenderer()
        for idea in ideas:
            idea_comp = component.Component(idea)

            with h.li(class_=idea.domain.label.lower().replace('_', '-')):
                with h.div(class_='user'):
                    h << idea_comp.render(h1, model="submitter_avatar")
                    h << idea_comp.render(h1, model='score_vote')

                with h.div(class_='idea-data'):
                    h << idea_comp.render(h, model="summary")
                    with h.div(class_="links"):
                        if idea.i.wf_context.state.label in progressing_ideas_states:
                            with h.a:
                                h << h.i(class_="icon-arrow-up",
                                         title=_(u'Progressing idea'))
                        if idea.i.challenge:
                            with h.a:
                                title = idea.i.challenge.title
                                h << h.i(title=title, alt=title,
                                         class_="icon-light")
                        with h.a:
                            count = len(idea.i.tracked_by)
                            if count:
                                h << h.i(class_="icon-heart",
                                         title=_N(u"%(count)d follower",
                                                  u"%(count)d followers",
                                                  count, count=count))
                            else:
                                h << h.i(class_="icon-heart",
                                         title=_(u"No follower"))
                            h << count
                        with h.a:
                            count = idea.i.total_comments
                            if count:
                                h << h.i(count, class_="icon-speak",
                                         title=_N(u"%(count)d comment",
                                                  u'%(count)d comments', count,
                                                  count=count))
                            else:
                                h << h.i(count, class_="icon-speak",
                                         title=_(u"No comment"))

    return h.root


@presentation.render_for(IdeaPager, model='options')
def render_idea_pager_options(self, h, comp, *args):
    with h.div(class_="options"):
        count = self.count()
        if count > 0:
            with h.span(class_='count'):
                h << _(u'%s ideas found') % count

        # export button
        h << comp.render(h, model='xls_export')

        # batch size
        with h.form(class_='batch-size'):
            h << h.label(_(u'Ideas per page:')) << " "

            submit_js = "this.form.submit();"

            with h.select(onchange=submit_js).action(self.set_batch_size):
                h << (h.option(v, value=v).selected(str(self.batch_size))
                      for v in (10, 20, 50, 100))

    return h.root


@presentation.render_for(IdeaPager, model='batch_size')
def render_idea_pager_options(self, h, comp, *args):
    with h.form:
        with h.div(class_='select'):
            h << h.span(_(u'Ideas per page:'))
            submit_js = "this.form.submit();"
            with h.div(class_='styled-select'):
                h << h.i(class_='icon-down')
                with h.select(onchange=submit_js).action(self.set_batch_size):
                    h << (h.option(v, value=v).selected(str(self.batch_size))
                          for v in (10, 20, 50, 100))
    return h.root


@presentation.render_for(IdeaPager, model='xls_export')
def render_idea_pager_xls_export(self, h, comp, *args):
    if security.has_permissions('export_xls', self):
        h << h.a(h.i(class_='icon-excel'),
                 class_='export',
                 title=_(u'Export all filtered ideas')).action(self.export_xls)
    return h.root


# FIXME: should viewing an idea be the responsibility of the pager ?!
@presentation.render_for(IdeaPager, model='detail')
def render_idea_pager_detail(self, h, comp, *args):
    h << self.content
    return h.root


# FIXME: should editing an idea be the responsibility of the pager ?!
@presentation.render_for(IdeaPager, model='detail_edit')
def render_idea_pager_detail_edit(self, h, comp, *args):
    h << self.content
    return h.root


@presentation.render_for(IdeaPager)
def render_idea_pager(self, h, comp, *args):
    if self.challenge_excerpt():
        h << self.challenge_excerpt

    h << comp.render(h, model="options")
    with h.table:
        with h.tbody:
            with h.tr(class_='ordered'):
                h << comp.render(h, model='filter')
            with h.tr(class_='filter'):
                h << comp.render(h, model='sort')
            with h.tr(class_='ideas-list-items'):
                h << comp.render(h, model='list')

    h << comp.render(h, model='batch')

    return h.root


@presentation.render_for(IdeaPager, model='full')
def render_idea_pager_full(self, h, comp, *args):
    h << comp.render(h, model='tabs')
    if self.challenge_excerpt():
        h << self.challenge_excerpt
    h << comp.render(h, model="options")
    h << comp.render(h, model='filter')
    h << comp.render(h, model='sort')
    h << comp.render(h, model='list')
    h << comp.render(h, model='batch')

    return h.root


@presentation.render_for(IdeaPager, model='simple')
def render_idea_pager_simple(self, h, comp, *args):
    if self.challenge_excerpt():
        h << self.challenge_excerpt
    h << comp.render(h, model="options")
    h << comp.render(h, model='list')
    h << comp.render(h, model='batch')

    return h.root


@presentation.render_for(IdeaPager, model='minimal')
def render_idea_pager_minimal(self, h, comp, *args):
    h << comp.render(h, model='filter')
    h << comp.render(h, model='list')

    return h.root


@presentation.render_for(IdeaPager, model='ideas-list')
@presentation.render_for(IdeaPager, model='domain-ideas-list')
def render_idea_pager_minimal(self, h, comp, *args):
    ideas = self.get_ideas_comp()

    with h.table:
        with h.tbody:
            h1 = h.SyncRenderer()
            for i in ideas:
                h << i.render(h1, 'list-items')
    return h.root


@presentation.render_for(IdeaPager, model='ordered')
def render_idea_pager_minimal(self, h, comp, *args):
    factories = [
        SortFieldFactory(_(u'Publication date'),
                         _(u'Sort from oldest to latest'),
                         _(u'Sort from latest to oldest'),
                         'pub-date date', 'publication_date'),
        SortFieldFactory(_(u'Recommendation date'),
                         _(u'Sort from oldest to latest'),
                         _(u'Sort from latest to oldest'),
                         'rec-date date', 'recommendation_date'),
        SortFieldFactory(_(u'Comments'),
                         _(u'Sort ascendingly'), _(u'Sort descendingly'),
                         'com', 'total_comments'),
        SortFieldFactory(_(u'Votes'),
                         _(u'Sort ascendingly'), _(u'Sort descendingly'),
                         'note', 'total_votes')]

    # creates a sort_criterion => SortFieldFactory mapping
    factory_by_order = dict(map(lambda f: (f.order, f), factories))

    # adds the requested sort criteria
    with h.table:
        with h.tbody:
            with h.tr(class_="filter"):
                criteria = self.sort_criteria
                criteria = [c for c in criteria if
                            c in factory_by_order.keys()]

                for c in criteria:
                    c = c.replace('_desc', '')
                    h << h.td(
                        factory_by_order[c].create_for(h, self, use_icon=True))

    return h.root


@presentation.render_for(IdeaPager, model='count')
def render_idea_pager_minimal(self, h, comp, *args):
    h << h.span(
        _N(u'%d found idea', u'%d found ideas', self.count()) % self.count(),
        class_='count')
    return h.root

# ---------------------------------------


@presentation.render_for(IdeasActivityPager)
def render_ideas_activity_pager(self, h, comp, *args):
    with h.div(class_='ordered'):
        h << self.menu.render(h.AsyncRenderer())

    with h.div(class_='ideas-list-items'):
        h << self.ideas_infinite_pager.render(h, model='first-page')

    return h.root


@presentation.render_for(IdeasActivityPagerMenu)
def render_ideas_activity_pager_menu(self, h, comp, *args):
    with h.div:
        h << _(u'Filter by :')
        h << self.menu_state
        h << self.menu_challenge
        h << self.menu_period
        h << self.menu_domain

    return h.root

# ---------------------------------------


@presentation.render_for(SubmitIdeaBox)
def render_submit_idea_box(self, h, comp, *args):
    with h.div(class_="submit-idea-box"):
        with h.a(title=_(u"Click here to fill the form"), class_='highlight',
                 href=self.submit_idea_url).action(
                lambda: self.with_login(self.submit_idea)):
            with h.span:
                h << _(u'Submit a new idea')

    return h.root

# ---------------------------------------


@presentation.render_for(IdeaBarChart)
def render_idea_bar_chart(self, h, comp, *args):
    h << self.chart
    return h.root

# ---------------------------------------


@presentation.render_for(IdeaPagerBox)
def render_pager_box_body(self, h, comp, *args):
    with h.section(class_='ideas ideas-list'):
        with h.div(class_='filter-tab'):
            if self.menu():
                h << self.menu

            with h.div(id='pager-counter'):
                h << self.idea_counter.render(h.AsyncRenderer())

        with h.div(class_='ordered'):
            h << self.filtered.render(h.AsyncRenderer())

            h << self.excel_exporter
            h << self.batch_size_changer

        h << self.ordered
        with h.div:
            h << self.pager.render(h.AsyncRenderer(), model='first-page')

    return h.root


@presentation.render_for(IdeasFilters)
def render_pager_box_body(self, h, comp, *args):
    with h.div:
        h << _(u'Filter by :')
        h << self.menu_state
        if self.show_challenge:
            h << self.menu_challenge
        h << self.menu_period
        h << self.menu_domain

    return h.root


@presentation.render_for(IdeaEditor, model='form')
def render_idea_editor_form(self, h, comp, *args):
    with h.form.pre_action(self.reset_values):
        h << comp.render(h, model='inner_form')
        h << comp.render(h, model='action_form')
    return h.root


@presentation.render_for(IdeaEditor, model='action_form')
def render_idea_editor_action_form(self, h, comp, *args):
    with h.div(class_='buttons'):
        h << h.input(type='submit',
                     value=_(u"Submit the idea"),
                     class_="confirm-button large").action(lambda: self.update_idea(draft=False))

        if self.can_submit_draft:
            h << h.input(type='submit',
                         value=_(u"Save draft"),
                         class_="confirm-button large").action(lambda: self.update_idea(draft=True))
    return h.root


@presentation.render_for(IdeaEditor, model='inner_form_title')
def render_idea_editor_inner_form_title(self, h, comp, *args):
    h << h.h1(h.span(_(u'My idea')), class_="tab active big")
    if self.idea and security.has_permissions('delete_idea', self):
        js = 'return yuiConfirm(this.href, "%s", "%s")' % (_(u'Confirm delete?'), _(u'This idea will be deleted permanently: are you sure?'))
        h << h.a('', title=_(u'Delete the idea'), class_="delete", onclick=js).action(self.delete_idea)
    return h.root


@presentation.render_for(IdeaEditor, model='inner_form')
def render_idea_editor_inner_form(self, h, comp, *args):
    with h.div(class_="ideaForm"):
        h << comp.render(h, model="inner_form_title")

        with h.div(class_='fields'):
            h << comp.render(h, model='mandatory_fields')
            h << comp.render(h, model='optional_fields')

        with h.div(class_="form_help"):
            h << comp.render(h, model='help_message')

    return h.root


@presentation.render_for(IdeaEditor, model='help_message')
def render_idea_editor_help_message(self, h, comp, *args):
    with h.div(class_="help_message"):
        with h.p:
            h << h.strong(_(u"You have an idea?"))
            h << _(u" Did you checked it has already been expressed? Perform a quick search to make it certain.")

        with h.h1:
            h << _(u"Find the good arguments to convince!")

        with h.p:
            h << h.strong(_(u"The more detailed and precisely described your idea is"))
            h << _(u" in terms of benefits for the company, the more chance it has to be selected by the idea developers.")

        with h.p:
            h << _("Example questions to ask yourself:")

        with h.ul:
            with h.li:
                h << h.em(_(u"Why"))
                h << _(u" has the company an interest in implementing it? (impacts, benefits, gains)")

            with h.li:
                h << h.em(_(u"Which means"))
                h << _(u"/investments are necessary?")

            with h.li:
                h << h.em(_(u"How"))
                h << _(u" can we implement it?")

            with h.li:
                h << _(u"Is there some ") << h.em(_(u"examples")) << _(u"? (sites, firms, contractors, articles, …)")

    return h.root


@presentation.render_for(IdeaEditor, model='mandatory_fields')
def render_idea_editor_mandatory_fields(self, h, comp, *args):
    with h.table(class_='mandatory-fields'):
        with h.tr:
            h << h.th
            with h.td:
                h << h.small("*: " + _(u'Mandatory fields'), class_='info')

        with h.tr:
            with h.th:
                h << h.label(_(u'Title') + '*')
            with h.td:
                h << h.input(type='text',
                             class_='text wide',
                             value=self.title()).action(self.title).error(self.title.error)
                h << h.div(_(u'Indicate the title of your idea (e.g. Recycling)'),
                           class_='legend')

        # challenge
        h << comp.render(h, model='challenge_choice')

        with h.tr:
            with h.th:
                h << h.label(_(u'Description') + '*')
            with h.td:
                h << h.textarea(self.description() or u'',
                                class_='description wide',
                                rows=u'',
                                cols=u'').action(self.description).error(self.description.error)
                h << h.div(_(u'Describe how your idea can make the company progress. Propose some means for implementing it.'),
                           class_='legend')

        with h.tr:
            with h.th:
                h << h.label(_(u'Domain') + '*')
            with h.td:
                with h.select().action(self.domain_id) as s:
                    h << h.option(_(u'Please choose a domain'), value="")
                    for t in self.get_domains():
                        h << h.option(t.i18n_label, value=t.id).selected(str(self.domain_id()))
                h << s.error(self.domain_id.error)
                h << h.div(_(u'Choose a domain in the list above'),
                           class_='legend')

        with h.tr:
            with h.th:
                h << h.label(_(u"Impact") + '*')
            with h.td:
                h << h.textarea(self.impact() or u'',
                                class_='impact wide',
                                rows="",
                                cols="").action(self.impact).error(self.impact.error)
                h << h.div(_(u'Describe what are the benefits of implementing your idea'),
                           class_='legend')

        with h.tr:
            with h.th:
                h << h.label(_(u"Keywords") + '*')
            with h.td:
                h << component.Component(Autocomplete(get_tags,
                                                      delim_char=",",
                                                      type='text',
                                                      class_='text wide',
                                                      value=self.tags(),
                                                      action=self.tags,
                                                      error=self.tags.error)).render(h)
                h << h.div(_(u'Write down the tags that describe your idea, separated by commas (e.g. innovation, communication, computing)'),
                           class_='legend')

    return h.root


@presentation.render_for(IdeaEditor, model='challenge_choice')
def render_idea_editor_challenge_choice(self, h, comp, *args):
    # preselect the challenge when possible, but let the user select another one if he wants
    submission_date = self.idea.i.submission_date if self.idea else datetime.now()
    active_challenges = self.get_active_challenges(submission_date)

    # display nothing when there's no active challenge
    if len(active_challenges) == 0:
        return h.root

    with h.tr(class_="challenge-choice field"):
        with h.th:
            h << h.label(_(u'Challenge'))

        with h.td:
            with h.select().action(self.challenge_id) as s:
                h << h.option(_(u'Off challenge'), value=0)
                for challenge in active_challenges:
                    h << h.option(challenge.short_title, value=challenge.id).selected(str(self.challenge_id()))
            h << s.error(self.challenge_id.error)
            h << h.div(_(u'Choose a challenge in the list above'),
                       class_='legend')

    return h.root


@presentation.render_for(IdeaEditor, model='optional_fields')
def render_idea_editor_optional_fields(self, h, comp, *args):
    table_id = h.generate_id('id')
    with h.p:
        h << h.a(_(u'Optional fields'),
                 class_='show-optional-fields',
                 href='javascript:toggleCollapseExpand("%s")' % table_id)

    with h.table(id=table_id, class_='optional-fields collapse'):
        with h.tr:
            with h.th:
                h << h.label(_(u"Origin"))
            with h.td:
                h << h.textarea(self.origin() or u'',
                                class_='wide',
                                rows="",
                                cols="").action(self.origin).error(self.origin.error)
                h << h.div(_(u'Describe how this idea came up to you (e.g. competitors propose this product, seen on the internet, recurring problem, …)'),
                           class_='legend')

        with h.tr:
            with h.th:
                h << h.label(_(u"Implementation"))
            with h.td:
                h << h.textarea(self.implementation() or u'',
                                class_='wide',
                                rows="",
                                cols="").action(self.implementation).error(self.implementation.error)
                h << h.div(_(u'Describe how to implement this idea'),
                           class_='legend')

        # authors
        with h.tr:
            with h.th:
                h << h.label(_(u'First co-author'))
            with h.td:
                h << component.Component(Autocomplete(lambda s: search_users_fulltext(s, limit=20),
                                                      type='text',
                                                      class_='text wide',
                                                      max_results_displayed=20,
                                                      value=self.co_author_1(),
                                                      action=self.co_author_1,
                                                      error=self.co_author_1.error)).render(h)

        with h.tr:
            with h.th:
                h << h.label(_(u'Second co-author'))
            with h.td:
                h << component.Component(Autocomplete(lambda s: search_users_fulltext(s, limit=20),
                                                      type='text',
                                                      class_='text wide',
                                                      max_results_displayed=20,
                                                      value=self.co_author_2(),
                                                      action=self.co_author_2,
                                                      error=self.co_author_2.error)).render(h)

        with h.tr:
            with h.th:
                h << h.label(_(u'Third co-author'))
            with h.td:
                h << component.Component(Autocomplete(lambda s: search_users_fulltext(s, limit=20),
                                                      type='text',
                                                      class_='text wide',
                                                      max_results_displayed=20,
                                                      value=self.co_author_3(),
                                                      action=self.co_author_3,
                                                      error=self.co_author_3.error)).render(h)
                h << h.div(_(u'Add up to 3 co-authors'),
                           class_='legend')

        # attachments
        attachments_labels = (_(u'First attached file'), _(u'Second attached file'), _(u'Third attached file'))
        attachments_legends = (None, None, _(u'Add up to 3 attached files to illustrate your idea (%d KB max per attachment)') % attachments_max_size())
        for i, (label, legend) in enumerate(zip(attachments_labels, attachments_legends)):
            with h.tr:
                with h.th:
                    h << h.label(label)
                with h.td:
                    attr_name = 'attachment_%d' % (i + 1)  # start at 1
                    property = getattr(self, attr_name)
                    h << h.input(type="file",
                                 class_='file').action(property).error(property.error)

                    if self.idea is not None:
                        attachment = getattr(self.idea.i, attr_name)
                        if attachment is not None:
                            with h.p:
                                h << component.Component(Attachment(attachment)).render(h)

                    if legend:
                        h << h.div(legend, class_='legend')

        h << comp.render(h, model='checkboxes')

    return h.root


@presentation.render_for(IdeaEditor, model='checkboxes')
def render_idea_editor_checkboxes(self, h, comp, *args):
    with h.tr:
        h << h.th
        with h.td:
            h << h.input(type='checkbox',
                         class_='checkbox',
                         name='anonymous').selected(self.anonymous())\
                                          .action(lambda v: self.anonymous(True))\
                                          .error(self.anonymous.error)

            h << h.label(_(u'I want to hide my name: it will not be visible to my innovation facilitator. It will be visible to everybody when my idea is published'),
                         class_='checkbox')

    with h.tr:
        h << h.th
        with h.td:
            h << h.input(type='checkbox',
                         name='My idea has already been implemented locally',
                         class_='checkbox').selected(self.already_done())\
                                           .action(lambda v: self.already_done(True))\
                                           .error(self.already_done.error)

            h << h.label(_(u'My idea has already been implemented locally'),
                         class_='checkbox')

    return h.root
