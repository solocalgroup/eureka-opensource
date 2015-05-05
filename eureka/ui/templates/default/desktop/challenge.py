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

from nagare import presentation, component
from nagare.i18n import _, format_date

from eureka.domain.queries import search_users_fulltext
from eureka.ui.common.yui2 import Autocomplete
from eureka.ui.common.yui2 import Calendar
from eureka.ui.common.yui2 import RichTextEditor

from eureka.ui.desktop.challenge import Challenge, ChallengeEditor


def render_titlebox(h, title):
    return h.h1(h.span(title), class_="titlebox")


def render_title(h, title):
    return h.h1(h.span(title), class_="tab active big")


@presentation.render_for(Challenge, model='title')
def render_challenge_title(self, h, comp, *args):
    h << render_titlebox(h, self.challenge.title)
    return h.root


@presentation.render_for(Challenge, model='author')
def render_challenge_author(self, h, comp, *args):
    with h.span(class_="author"):
        h << _(u'from')
        h << ' '
        h << self.challenge.created_by.fullname
        h << ', '
        h << self.challenge.organization
    return h.root


@presentation.render_for(Challenge, model='period')
def render_challenge_period(self, h, comp, *args):
    one_day = timedelta(days=1)
    start_date = format_date(self.challenge.starting_date, format='long')
    end_date = format_date(self.challenge.ending_date - one_day, format='long')  # ending_date is not included
    with h.span(class_="period"):
        h << _(u'from %(start_date)s') % dict(start_date=start_date)
        h << " "
        h << _(u'to %(end_date)s') % dict(end_date=end_date)
    return h.root


@presentation.render_for(Challenge, model='summary')
def render_challenge_summary(self, h, comp, *args):
    with h.div(class_='summary'):
        h << h.parse_htmlstring(self.challenge.summary, fragment=True)
    return h.root


@presentation.render_for(Challenge, model='description')
def render_challenge_description(self, h, comp, *args):
    with h.div(class_='description'):
        h << h.parse_htmlstring(self.challenge.description, fragment=True)
    return h.root


@presentation.render_for(Challenge, model='outcome')
def render_challenge_outcome(self, h, comp, *args):
    if self.challenge.outcome:
        with h.div(class_='outcome'):
            with h.h2:
                h << _(u'Outcome of the challenge')
            h << h.parse_htmlstring(self.challenge.outcome, fragment=True)
    return h.root


@presentation.render_for(Challenge, model='ideas')
def render_challenge_ideas(self, h, comp, *args):
    with h.div(class_='challenge-ideas'):
        h << component.Component(self.ideas).render(h)
    return h.root


@presentation.render_for(Challenge, model='submit_idea_link')
def render_challenge_submit_idea_link(self, h, comp, *args):
    h << self.submit_idea_box
    return h.root


@presentation.render_for(Challenge, model='view_challenge_ideas_link')
def render_challenge_view_challenge_ideas_link(self, h, comp, *args):
    with h.a(class_="confirm-button",
             href=self.challenge_ideas_url):
        h << _(u"View challenge ideas")
        h << " (%s)" % self.challenge.popularity
    return h.root


@presentation.render_for(Challenge, model="banner")
def render_challenge_banner(self, h, comp, *args):
    h << h.h1(self.challenge.title, class_='title')
    with h.p:
        h << comp.render(h, model='author')
    return h.root


@presentation.render_for(Challenge)
def render_challenge(self, h, comp, *args):
    with h.div(class_="challengeBox details rounded"):
        # submit idea link
        h << comp.render(h, model='submit_idea_link')
        # title
        h << comp.render(h, model='title')
        # source of the challenge
        with h.p(class_='source'):
            h << comp.render(h, model='author')
        # summary
        h << comp.render(h, model='summary')
        # description
        h << comp.render(h, model='description')
        # outcome if any
        h << comp.render(h, model='outcome')
        # ideas
        # h << comp.render(h, model='ideas')
        with h.div(class_='buttons'):
            h << comp.render(h, model='view_challenge_ideas_link')

    return h.root


@presentation.render_for(Challenge, model='short_excerpt')
def render_challenge_short_excerpt(self, h, comp, *args):
    with h.div(class_='challenge-summary'):
        with h.h1(class_='title'):
            h << self.challenge.title
            h << ' (' << comp.render(h, model='period') << ')'

        # summary
        h << comp.render(h, model='summary')

        h << h.a(_(u'Read the whole challenge'),
                 href=self.challenge_url,
                 class_='view-challenge')  # FIXME: repair continuation

    return h.root


@presentation.render_for(Challenge, model='excerpt')
def render_challenge_excerpt(self, h, comp, *args):
    # short excerpt
    h << comp.render(h, model='short_excerpt')

    # challenge ideas
    h << comp.render(h, model='ideas')

    return h.root


@presentation.render_for(ChallengeEditor)
def render_challenge_editor(self, h, comp, *args):
    with h.div(class_='challenge-editor'):
        h << render_title(h, _(u'Edit the challenge'))

        with h.form.post_action(self.post_validate):
            with h.div(class_='fields'):
                # title
                with h.div(class_='title'):
                    field_id = h.generate_id('field')
                    h << h.label(_(u'Title'), for_=field_id) << ' '
                    h << h.input(type='text',
                                 id=field_id,
                                 class_='text wide',
                                 value=self.title()).action(self.title).error(self.title.error)

                with h.div(class_='short-title'):
                    field_id = h.generate_id('field')
                    h << h.label(_(u'Short title'), for_=field_id) << ' '
                    h << h.input(type='text',
                                 id=field_id,
                                 class_='text wide',
                                 value=self.short_title()).action(self.short_title).error(self.short_title.error)

                with h.div(class_='tags'):
                    field_id = h.generate_id('field')
                    h << h.label(_(u'Tags'), for_=field_id) << ' '
                    h << h.input(type='text',
                                 id=field_id,
                                 class_='text wide',
                                 value=self.tags()).action(self.tags).error(self.tags.error)

                # author information
                with h.div(class_='created-by'):
                    field_id = h.generate_id('field')
                    h << h.label(_(u'Created by (email)'), for_=field_id) << ' '
                    autocomplete = Autocomplete(lambda s: search_users_fulltext(s, limit=20),
                                                ac_class='zindex999',
                                                type='text',
                                                class_='text wide',
                                                id=field_id,
                                                max_results_displayed=20,
                                                value=self.created_by(),
                                                action=self.created_by,
                                                error=self.created_by.error)
                    h << component.Component(autocomplete).render(h)

                with h.div(class_='organization'):
                    field_id = h.generate_id('field')
                    h << h.label(_(u'Organization'), for_=field_id) << ' '
                    h << h.input(type='text',
                                 id=field_id,
                                 class_='text wide',
                                 value=self.organization()).action(self.organization).error(self.organization.error)

                with h.div(class_='associated-dis'):
                    field_id = h.generate_id('field')
                    h << h.label(_(u"Challenge's developers (emails)"), for_=field_id) << ' '
                    autocomplete = Autocomplete(lambda s: search_users_fulltext(s, limit=20),
                                                ac_class='zindex998',
                                                delim_char=",",
                                                type='text',
                                                class_='text wide',
                                                id=field_id,
                                                max_results_displayed=20,
                                                value=self.associated_dis(),
                                                action=self.associated_dis,
                                                error=self.associated_dis.error)
                    h << component.Component(autocomplete).render(h)

                with h.div(class_='period'):
                    # starting date
                    with h.span(class_='starting-date'):
                        starting_date_calendar = component.Component(Calendar('challenge_starting_date',
                                                                              title=_(u'Select a date'),
                                                                              close_button=True))
                        h << h.label(_(u'Start date (included)'), for_=starting_date_calendar().field_id) << ' '
                        h << h.input(type='text',
                                     id=starting_date_calendar().field_id,
                                     class_='date',
                                     value=self.starting_date()).action(self.starting_date)
                        h << starting_date_calendar.render(h, model='date_picker')
                        if self.starting_date.error:
                            h << h.div(self.starting_date.error, class_='nagare-error-message')

                    # ending date
                    with h.span(class_='ending-date'):
                        ending_date_calendar = component.Component(Calendar('challenge_ending_date',
                                                                            title=_(u'Select a date'),
                                                                            close_button=True))
                        h << h.label(_(u'End date (included)'), for_=ending_date_calendar().field_id) << ' '
                        h << h.input(type='text',
                                     id=ending_date_calendar().field_id,
                                     class_='date',
                                     value=self.ending_date()).action(self.ending_date)
                        h << ending_date_calendar.render(h, model='date_picker')
                        if self.ending_date.error:
                            h << h.div(self.ending_date.error, class_='nagare-error-message')

                    h << starting_date_calendar
                    h << ending_date_calendar

                # summary
                with h.div(class_='summary'):
                    field_id = h.generate_id('field')
                    h << h.label(_(u'Summary'), for_=field_id)
                    summary_rte = RichTextEditor(property=self.summary,
                                                 height=150,
                                                 id=field_id,
                                                 gallery_url=self.gallery_url(field_id))
                    h << component.Component(summary_rte)

                # description
                with h.div(class_='desktop-description'):
                    field_id = h.generate_id('field')
                    h << h.label(_(u'Desktop Description'), for_=field_id)
                    description_rte = RichTextEditor(property=self.description,
                                                     height=300,
                                                     id=field_id,
                                                     gallery_url=self.gallery_url(field_id))
                    h << component.Component(description_rte)

                if self.mobile_access:
                    # mobile description
                    with h.div(class_='mobile-description'):
                        field_id = h.generate_id('field')
                        h << h.label(_(u'Mobile Description'), for_=field_id)
                        mobile_description_rte = RichTextEditor(property=self.mobile_description,
                                                                height=400,
                                                                max_chars=200,
                                                                id=field_id,
                                                                gallery_url=self.gallery_url(field_id))
                        h << component.Component(mobile_description_rte)

                # outcome
                if self.finished:
                    with h.div(class_='outcome'):
                        field_id = h.generate_id('field')
                        h << h.label(_(u'Outcome'), for_=field_id)
                        outcome_rte = RichTextEditor(property=self.outcome,
                                                     height=300,
                                                     id=field_id,
                                                     gallery_url=self.gallery_url(field_id))
                        h << component.Component(outcome_rte)

            # buttons
            with h.div(class_='buttons'):
                h << h.input(type='submit',
                             class_='confirm-button',
                             value=_(u'Save')).action(lambda: self.commit() and comp.answer())

    return h.root
