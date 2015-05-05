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

import operator

from nagare import presentation, component, security
from nagare.namespaces import xhtml
from nagare.i18n import _, format_datetime

from eureka.infrastructure.tools import text_to_html_elements
from eureka.domain.models import EventType, EventStatus, MailDeliveryFrequency
from eureka.infrastructure.workflow.voucher import get_acquired_point_categories, get_sorted_spent_point_categories, \
    get_manual_point_categories, PointCategory
from eureka.domain.queries import search_users_fulltext
from eureka.ui.common import ellipsize
from eureka.ui.common.choice import CheckboxChoice, RadioChoice
from eureka.ui.common.yui2 import Autocomplete

from eureka.ui.desktop.user import (User, ProfileBox, UserFIEditor,
                                    PasswordEditor, AvatarEditor,
                                    ProfileEditor, HomeSettingsEditor,
                                    MailSettingsEditor,
                                    SettingsEditor, UserPager, UserBrowser)
from eureka.ui.desktop.login import LogoutEvent


@presentation.render_for(User, model="avatar_photo")
def render_user_avatar_photo(self, h, comp, *args):
    h << h.img(class_="avatar", alt=self.user.fullname, title=self.user.fullname, src=self.photo_url)
    return h.root


@presentation.render_for(User, model="avatar_thumbnail")
def render_user_avatar_thumbnail(self, h, comp, *args):
    return render_avatar_thumbnail(self, h)  # use default avatar thumbnail size


@presentation.render_for(User, model="avatar40")
def render_user_avatar40(self, h, comp, *args):
    return render_avatar_thumbnail(self, h, '40x40')


@presentation.render_for(User, model="avatar30")
def render_user_avatar30(self, h, comp, *args):
    return render_avatar_thumbnail(self, h, '30x30')


@presentation.render_for(User, model="avatar90")
def render_user_avatar90(self, h, comp, *args):
    return render_avatar_thumbnail(self, h, '90x90')


@presentation.render_for(User, model="avatar100")
def render_user_avatar100(self, h, comp, *args):
    return render_avatar_thumbnail(self, h, '100x100')


# utility method for rendering avatar thumbnails
def render_avatar_thumbnail(self, h, size='100x100'):
    with h.a(href=self.profile_url(self.uid)).action(lambda: self.view_profile(self.uid)):
        if size:
            class_ = "avatar size_" + size
        else:
            class_ = "avatar"
        h << h.img(class_=class_, src=self.thumbnail_url(size), alt=self.user.fullname, title=self.user.fullname)
    return h.root


@presentation.render_for(User, model="fullname")
def render_user_fullname(self, h, comp, *args):
    with h.a(class_="username", href=self.profile_url(self.uid)).action(lambda: self.view_profile(self.uid)):
        h << self.user.fullname
    return h.root


@presentation.render_for(User, model="status")
def render_user_status(self, h, comp, *args):
    with h.span(class_='status-level'):
        h << self.user.status_level_label
    h << ' '
    with h.span(class_="points"):
        h << '(%s)' % (_(u"%d points") % self.user.acquired_points)
    return h.root


@presentation.render_for(User, model="status_image")
def render_user_status_image(self, h, comp, *args):
    h << h.img(class_='status-level-image',
               alt=self.user.status_level_label,
               title=self.user.status_level_label,
               src='%s/style/desktop/img/status_level%d.png' % (h.head.static_url, self.user.status_level))
    return h.root


@presentation.render_for(User, model="pager_row")
def render_user_pager_row(self, h, comp, *args):
    with h.td:
        h << comp.render(h, model='avatar100')
    with h.td:
        h << comp.render(h, model='fullname')
    h << h.td(self.user.corporation_label)
    h << h.td(self.user.position or '')
    h << h.td(comp.render(h, model='status'))
    return h.root


@presentation.render_for(User, model="login_status")
def render_user_login_box(self, h, comp, *args):
    def logout():
        comp.answer(LogoutEvent())

    with h.a(class_='bookmarks', href=self.profile_url()).action(self.view_tracked_ideas):
        h << h.i(class_='icon-bookmark')
        h << self.new_events_count()

    with h.a(class_='comments').action(self.view_basket):
        h << h.i(class_='icon-comment')
        h << self.ideas_count

    if security.has_permissions('show_dsig_basket', self):
        with h.a(class_='cart cart-dsig').action(self.view_dsig_basket):
            h << h.i(class_='icon-cart')
            h << h.span('ADM')

    if security.has_permissions('show_di_basket', self):
        with h.a(class_='cart').action(self.view_di_basket):
            h << h.i(class_='icon-cart')
            h << h.span('DI')
            h << self.get_di_ideas_basket_count()

    if security.has_permissions('show_fi_basket', self):
        with h.a(class_='cart').action(self.view_fi_basket):
            h << h.i(class_='icon-cart')
            h << h.span('FI')
            h << self.get_fi_ideas_basket_count()

    with h.a(class_='prefs', href=self.profile_url()).action(self.view_administration):
        h << h.i(class_='icon-pref')

    with h.div(class_='disconnect'):
        with h.a.action(logout):
            h << h.i(class_='icon-logout')

    with h.div(class_='user'):
        with h.a(href=self.profile_url()).action(self.view_profile):
            h << self.user.fullname

    return h.root


# -------------------------------------------------------------------

@presentation.render_for(PasswordEditor)
def render_password_editor(self, h, comp, *args):
    def commit():
        if self.commit():
            comp.answer(True)

    def cancel():
        comp.answer(False)

    # autocomplete='off' prevents Firefox & IE from remembering the password
    with h.form(class_='password-editor', autocomplete='off'):
        with h.div(class_='fields'):
            with h.div(class_='password-field field'):
                field_id = h.generate_id('field')

                h << h.input(type='password',
                             class_='text',
                             id=field_id).action(self.password).error(self.password.error)

                with h.label(for_=field_id):
                    h << _('New password')
                    with h.div(class_='legend'):
                        h << _('Enter your new password')

            with h.div(class_='password-confirmation-field field'):
                field_id = h.generate_id('field')

                h << h.input(type='password',
                             class_='text',
                             id=field_id).action(self.password_confirm).error(self.password_confirm.error)

                with h.label(for_=field_id):
                    h << _('Password confirmation')
                    with h.div(class_='legend'):
                        h << _('Confirm your new password')

        with h.div(class_='buttons'):
            h << h.input(type='submit',
                         value=_(u'Change your password')).action(commit)
            if self.with_cancel:
                h << h.input(type='submit',
                             value=_(u'Cancel')).action(cancel)

    return h.root


# -------------------------------------------------------------------

@presentation.render_for(AvatarEditor)
def render_avatar_editor(self, h, comp, *args):
    with h.form(class_="avatar-editor"):
        h << h.input(type='file',
                     class_='file',
                     name='photo').action(self.photo)
        h << h.div(_(u'Select a photo from a file'),
                   class_="legend")

        h << h.input(type='submit', value=_(u'Change your photo')).action(self.commit)

    return h.root


# -------------------------------------------------------------------

@presentation.render_for(UserFIEditor)
def render_user_fi_editor(self, h, comp, *args):
    with h.form(class_='user-fi-editor'):
        label = _(u"My facilitator:") if self.is_mine else _(u'Her facilitator:')
        h << h.label(label) << ' '

        with h.select().action(self.fi_uid) as s:
            h << h.option(_(u'Choose a facilitator'), value="", disabled=True)
            for u in self.get_facilitators():
                h << h.option(u.firstname, " ", u.lastname, value=u.uid).selected(str(self.fi_uid()))
        h << s.error(self.fi_uid.error)

        h << h.input(type='submit',
                     value=_(u'Change')).action(self.commit)

    return h.root


# -------------------------------------------------------------------

@presentation.render_for(ProfileEditor)
def render_profile_editor(self, h, comp, *args):
    with h.form(class_='profile-editor'):
        # expert's business area
        if self.user.di_business_area and security.has_permissions('view_di_business_area', self):
            with h.h3:
                h << _(u"Expert's Business Area")
            with h.p:
                h << self.user.di_business_area

        if self.user.is_developer():
            h << h.h3(_(u'My speciality'))
            h << h.input(type='text',
                         class_='text wide',
                         value=self.specialty()).action(self.specialty).error(self.specialty.error)

        h << h.h3(_(u'Mobile phone'))
        h << h.input(type='text',
                     class_='text wide',
                     value=self.mobile_phone()).action(self.mobile_phone).error(self.mobile_phone.error)

        h << h.h3(_(u'Office phone'))
        h << h.input(type='text',
                     class_='text wide',
                     value=self.work_phone()).action(self.work_phone).error(self.work_phone.error)

        h << h.h3(_(u'Who am I?'))
        h << h.textarea(self.description(),
                        class_='wide',
                        rows=5,
                        cols=30).action(self.description).error(self.description.error)

        h << h.h3(_(u'Skills'))
        h << h.textarea(self.competencies(),
                        class_='wide',
                        rows=5,
                        cols=30).action(self.competencies).error(self.competencies.error)
        h << h.div(_(u'List your skills, knowledge, learning, know-how, … then submit your profile'),
                   class_='legend')

        h << h.h3(_(u'Expertises'))
        h << h.textarea(self.expertises(),
                        class_='wide',
                        rows=5,
                        cols=30).action(self.expertises).error(self.expertises.error)
        h << h.div(_(u'Tell us about your expertises, … then submit your profile'),
                   class_='legend')

        h << h.h3(_(u'Hobbies'))
        h << h.textarea(self.hobbies(),
                        class_='wide',
                        rows=5,
                        cols=30).action(self.hobbies).error(self.hobbies.error)
        h << h.div(_(u'Describe your hobbies, passions outside the company, … then submit your profile'),
                   class_='legend')

        with h.div(class_='buttons'):
            h << h.input(type='submit',
                         value=_(u'Submit the profile')).action(self.commit)

    return h.root


# -------------------------------------------------------------------

@presentation.render_for(HomeSettingsEditor)
def render_home_settings_editor(self, h, comp, *args):
    def commit_and_answer():
        if self.commit():
            comp.answer(True)

    with h.form(class_='home-settings-editor').pre_action(self.reset_fields):
        with h.div(class_='fields'):
            with h.div(class_='show-progressing-ideas field'):
                field_id = h.generate_id('field')
                h << h.input(type='checkbox', class_='checkbox').selected(self.show_progressing_ideas()).action(self.show_progressing_ideas)
                h << h.label(_("Show progressing ideas"), for_=field_id)

            with h.div(class_='show-tracked-ideas field'):
                field_id = h.generate_id('field')
                h << h.input(type='checkbox', class_='checkbox').selected(self.show_tracked_ideas()).action(self.show_tracked_ideas)
                h << h.label(_("Show tracked ideas"), for_=field_id)

            with h.div(class_='show-challenges-ideas field'):
                field_id = h.generate_id('field')
                h << h.input(type='checkbox', class_='checkbox').selected(self.show_challenges_ideas()).action(self.show_challenges_ideas)
                h << h.label(_("Show challenges published ideas"), for_=field_id)

            with h.div(class_='show-domains field'):
                with h.fieldset:
                    with h.legend:
                        h << _("Show domain ideas")

                    domain_items = [(domain.i18n_label, domain.id)
                                    for domain in self.domains]
                    h << component.Component(
                        CheckboxChoice(self.domains_choice, domain_items))

            with h.div(class_="field"):
                with h.label:
                    h << _(u'Keyword filter')
                    h << h.input(type='text', value=self.keyword_filter(), class_='text wide').action(self.keyword_filter).error(self.keyword_filter.error)

            with h.div(class_='recipients-field field'):
                with h.label:
                    h << _(u'User filter')
                    with h.span(class_='legend'):
                        h << _(u"If there's more than one user, separate them with a comma")

                autocomplete = Autocomplete(lambda s: search_users_fulltext(s, limit=20),
                                            delim_char=",",
                                            type='text',
                                            class_='text wide',
                                            max_results_displayed=20,
                                            value=self.users_filter(),
                                            action=self.users_filter,
                                            error=self.users_filter.error)
                h << component.Component(autocomplete).render(h)

        with h.div(class_='buttons'):
            h << h.input(type='submit',
                         value=_("Ok")).action(commit_and_answer)

    return h.root


# -------------------------------------------------------------------

@presentation.render_for(MailSettingsEditor)
def render_mail_settings_editor(self, h, comp, *args):
    def commit_and_answer():
        if self.commit():
            comp.answer(True)

    with h.form(class_='mail-settings-editor'):
        with h.div(class_='fields'):
            with h.fieldset:
                with h.legend:
                    h << _("Delivery frequency")

                mail_delivery_items = (
                    (_("Immediately"), MailDeliveryFrequency.Immediately),
                    (_("Daily"), MailDeliveryFrequency.Daily),
                )
                h << component.Component(RadioChoice(self.mail_delivery_frequency, mail_delivery_items))

        with h.div(class_='buttons'):
            h << h.input(type='submit',
                         value=_('Ok')).action(commit_and_answer)

    return h.root


# -------------------------------------------------------------------

@presentation.render_for(SettingsEditor)
def render_settings_editor(self, h, comp, *args):
    with h.div(class_='settings-editor'):
        with h.h2:
            h << _("Home Settings")
        h << self.home_settings.on_answer(comp.answer)

        with h.h2:
            h << _("Mail Settings")
        h << self.mail_settings.on_answer(comp.answer)

        with h.h2:
            h << _("Edit password")
        h << self.password_settings.on_answer(comp.answer)

        h << h.script('scrollToFirstErrorField();', type='text/javascript')
    return h.root


# -------------------------------------------------------------------

def render_user_pager_body(h, comp, with_options=True):
    with h.div(class_='user-pager'):
        if with_options:
            h << comp.render(h, model='options')
        h << comp.render(h, model='list')
        h << comp.render(h, model='batch')


@presentation.render_for(UserPager)
def render_user_pager(self, h, comp, *args):
    render_user_pager_body(h, comp)
    return h.root


@presentation.render_for(UserPager, model='minimal')
def render_user_pager_minimal(self, h, comp, *args):
    render_user_pager_body(h, comp, with_options=False)
    return h.root


@presentation.render_for(UserPager, model="list")
def render_user_pager_list(self, h, comp, *args):
    users = self.get_pager_elements()
    with h.div(class_='list'):
        if len(users) == 0:
            with h.p(class_='empty'):
                h << _(u'No user found')
            return h.root

        with h.table(cellpadding="0", cellspacing="0"):
            with h.tr:
                h << h.th(_(u'Photo'))
                h << h.th(_(u'Name'))
                h << h.th(_(u'Corporation'))
                h << h.th(_(u'Position'))
                h << h.th(_(u'Status (Points)'))

            for idx, elt in enumerate(users[:self.batch_size]):
                with h.tr(class_=['even', 'odd'][idx % 2]):
                    sync = xhtml.Renderer(h)
                    h << component.Component(User(self, elt)).render(sync, model='pager_row')

    return h.root


@presentation.render_for(UserPager, model='options')
def render_user_pager_options(self, h, comp, *args):
    with h.div(class_="options"):
        count = self.count()
        if count > 0:
            with h.span(class_='count'):
                h << _(u'%s users found') % count

        # XLS export button
        h << comp.render(h, model='xls_export')

        # batch size
        with h.form(class_='batch-size'):
            h << h.label(_(u'Users per page'), ": ")
            submit_js = "this.form.submit();"
            with h.select(onchange=submit_js).action(self.change_batch_size):
                h << (h.option(v, value=v).selected(str(self.batch_size))
                      for v in (10, 20, 50, 100))

    return h.root


@presentation.render_for(UserPager, model='xls_export')
def render_user_pager_xls_export(self, h, comp, *args):
    if security.has_permissions('export_xls', self):
        h << h.a(_(u'Export to Excel'),
                 class_='xls-export',
                 title=_(u'Export all users')).action(self.export_xls)
    return h.root


# -------------------------------------------------------------------

@presentation.render_for(ProfileBox, model='header')
def render_profile_box_header(self, h, comp, *args):

    user_comp = component.Component(User(self, self.user))
    with h.section(class_='profile'):
        with h.div(class_='user'):
            # user info
            # avatar image
            h << user_comp.render(h, model='avatar_photo')
            h << h.div(self.user.fullname, class_='name')
            h << h.small(self.user.status_level_label, class_='title')

            if security.has_permissions('edit_avatar', self):
                h << component.Component(self.avatar_editor)

        with h.div(class_='user-info'):

            h << h.h1(self.user.fullname)
            l1 = '-'.join([elt for elt in [self.user.corporation_label, self.user.site_label] if elt])
            l2 = '-'.join([elt for elt in [self.user.direction_label, self.user.service_label] if elt])
            l3 = self.user.position
            if l1 or l2 or l3:
                with h.ul:
                    if l1:
                        h << h.li(l1)
                    if l2:
                        h << h.li(l2)
                    if l3:
                        h << h.li(l3)

            h << h.h2(_('Contact'))
            h << h.a(self.user.email, href="mailto:" + self.user.email)
            h << h.br
            h << (self.user.work_phone or '')
            h << h.br
            h << (self.user.mobile_phone or '')
            h << h.br
            h << h.br

            # FI
            user_fi = self.user.fi
            if security.has_permissions('edit_fi', self):
                h << component.Component(self.fi_editor).render(h)
            elif user_fi:
                h << _(u'Facilitator: ')
                h << h.a(user_fi.fullname,
                         href=self.profile_url(user_fi.uid)).action(lambda uid=user_fi.uid: self.view_profile(uid))
            else:
                with h.p:
                    h << h.a(_(u'No facilitator associated'))

        h << comp.render(h, model='tabs')

    return h.root


@presentation.render_for(ProfileBox, model='tabs')
def render_profile_box_tabs(self, h, comp, *args):
    tab_labels = self.tab_labels

    can_view_points = security.has_permissions('view_points', self)

    with h.ul(class_='tabs'):
        for name in self.tabs:
            if self.selected_tab() == name:
                class_ = 'current'
            else:
                class_ = ''

            with h.li(class_=class_):
                with h.span:
                    if name == 'points' and not can_view_points:
                        h << h.a(tab_labels[name], title=tab_labels[name])
                    else:
                        h << h.a(tab_labels[name], title=tab_labels[name]).action(lambda v=name: self.selected_tab(v))
    return h.root


@presentation.render_for(ProfileBox)
def render_profile_box(self, h, comp, *args):

    h << comp.render(h, model="header")

    # content
    with h.section(class_='tab-content'):
        h << comp.render(h, model=self.selected_tab())

    return h.root


@presentation.render_for(ProfileBox, model='profile')
def render_profile_box_profile(self, h, comp, *args):
    if security.has_permissions('edit_user', self):
        h << comp.render(h, model='profile_edit')
    else:
        h << comp.render(h, model='profile_view')

    with h.div(class_='group'):
        h << h.h2(_("My Timeline") if self.is_mine else _("Her Timeline"))
        h << comp.render(h, model='timeline')

    return h.root


@presentation.render_for(ProfileBox, model='settings')
def render_profile_box_settings(self, h, comp, *args):
    h << self.settings_editor.on_answer(lambda a: None)  # do nothing on answer
    return h.root


@presentation.render_for(ProfileBox, model='profile_view')
def render_profile_box_profile_view(self, h, comp, *args):
    user = self.user

    # expert's business area
    if user.di_business_area and security.has_permissions('view_di_business_area', self):
        with h.h2:
            h << _(u"Expert's Business Area")
        with h.p:
            h << user.di_business_area or ''

    with h.div(class_='group'):
        h << h.h2(_(u'Who am I?'))
        if user.description:
            with h.p:
                h << '"%s"' % user.description

    with h.div(class_='group'):
        with h.table:
            with h.tbody:
                with h.tr:
                    with h.td:
                        h << h.h2(_(u'Skills'))
                        if user.competencies:
                            h << text_to_html_elements(h, user.competencies)
                    with h.td:
                        h << h.h2(_(u'Expertises'))
                        if user.expertises:
                            h << text_to_html_elements(h, user.expertises)
                    with h.td:
                        h << h.h2(_(u'Hobbies'))
                        if user.hobbies:
                            h << text_to_html_elements(h, user.hobbies)

    return h.root


def render_timeline_item(h, elt, parent, user):
    if elt.get_type() == 'IDEA':
        # FIXME: late import to avoid circular dependencies problem
        from eureka.ui.desktop.idea import Idea
        return h.span(_(u'%s follows idea') % user.firstname, " ",
                      component.Component(Idea(parent, elt.target),
                                          model='short_link'))

    if elt.get_type() == 'USER':
        return h.span(_(u'%s follows') % user.firstname, " ",
                      component.Component(User(parent, elt.target),
                                          model='fullname'))

    return ''


@presentation.render_for(ProfileBox, model='timeline')
def render_profile_box_timeline(self, h, comp, *args):
    timeline = self.user.get_timeline()
    with h.ul(class_='list-even-odd'):
        h << (
            [h.li(render_timeline_item(h, elt, self, self.user))
             for elt in timeline] or
            h.li(_(u'No event in timeline')))
    return h.root


@presentation.render_for(ProfileBox, model='profile_edit')
def render_profile_box_profile_edit(self, h, comp, *args):
    h << component.Component(self.profile_editor).render(h)
    return h.root


@presentation.render_for(ProfileBox, model='tracked_ideas')
def render_profile_box_tracked_ideas(self, h, comp, *args):
    with h.div(class_='tracking-details'):
        with h.div(class_='events'):
            with h.h2:
                h << _(u"Latest events")
                if self.new_events_count():
                    h << h.a(_(u'Mark everything as read'),
                             class_="consume_link",
                             href="").action(lambda: self.read_all_events())

            with h.ul:
                for i, event in enumerate(self.events()):
                    idea = event.idea
                    css_class = ' '.join((['odd', 'even'][i % 2],
                                          ('read' if event.status == EventStatus.Read else 'unread')))

                    event_date = format_datetime(event.date)

                    event_type_display = {
                        EventType.CommentAdded: ('comment', "style/desktop/icons/comment_delete.png"),
                        EventType.StateChanged: ('worflow', "style/desktop/icons/chart_bar_delete.png")
                    }
                    css_specific_class, icon_src = event_type_display[event.label]
                    with h.li(class_=css_specific_class + " " + css_class):
                        with h.a(title=_(u'Remove the event'),
                                 class_='remove-event').action(lambda event_id=event.id: self.hide_event(event_id)):
                            h << h.img(title=_(u'Remove the event'),
                                       alt=_(u'Remove the event'),
                                       src=icon_src)
                        h << h.a(_(u'New comment for the idea %s') % idea.title,
                                 href="idea/%d" % idea.id,
                                 title=event_date).action(lambda event_id=event.id: self.read_event(event_id))

        with h.div(class_='ideas rounded'):
            with h.h2:
                h << _(u"My Tracked Ideas")

            with h.ul:
                for i, idea in enumerate(self.tracked_ideas()):
                    with h.li(class_=['odd', 'even'][i % 2]):
                        h << h.a(_(u'Remove tracking'),
                                 title=_(u'Remove tracking'),
                                 class_='remove-tracking').action(lambda id=idea.id: self.remove_tracked_idea(id))
                        h << ' '
                        h << h.a(idea.title,
                                 title=_(u"View the idea"),
                                 href="idea/%d" % idea.id).action(lambda id=idea.id: self.view_idea(id))

    return h.root


@presentation.render_for(ProfileBox, model='ideas')
def render_profile_box_ideas(self, h, comp, *args):
    h << component.Component(self.idea_pager).render(h)
    return h.root


@presentation.render_for(ProfileBox, model='points')
def render_profile_box_points(self, h, comp, *args):
    # display a shop button if I'm looking my own profile
    if self.is_mine:
        h << component.Component(self.online_shop).render(h, model='link_box')

    with h.div(class_='point-details'):
        # finds out the points
        points_by_label = self.user.get_points_by_category()
        used_point_labels = points_by_label.keys()

        # no points?
        if len(points_by_label) == 0:
            h << h.h2(_(u'You do not have any point yet.'))
            return h.root

        # renders the available points
        h << h.h2(_(u'Available points: %d') % self.user.available_points)

        # renders the acquired points
        h << h.h2(_(u'Acquired points: %d') % self.user.acquired_points)
        labels = [l for l in get_acquired_point_categories() if l in used_point_labels]
        render_point_labels(self, h, comp, labels, points_by_label)

        # renders the spent points
        h << h.h2(_(u'Spent points: %d') % self.user.spent_points)
        labels = [l for l in get_sorted_spent_point_categories() if l in used_point_labels]
        render_point_labels(self, h, comp, labels, points_by_label)

    return h.root


def render_point_labels(self, h, comp, labels, points_by_label):
    # render the labels
    with h.ul:
        for label in labels:
            with h.li(class_='point-category collapse'):
                render_point_items(self, h, comp, label, points_by_label[label])


def render_point_items(self, h, comp, category, points):
    # configuration of the view
    reason_title = _(u"Reason")
    subject_title = _(u"Subject")
    if category == PointCategory.REMOVE_COMMENT:
        subject_title = _(u'Deleted comment')
    elif category == PointCategory.ADD_COMMENT:
        subject_title = _(u'Added comment')

    show_reason = any(p.reason for p in points)
    show_subject = any(p.subject_as_string() for p in points)
    show_delete = (category in get_manual_point_categories()) and security.has_permissions('edit_points', self)
    categories_to_highlight = (PointCategory.PUBLISH_IDEA,
                               PointCategory.PUBLISH_CHALLENGE_FIRST_IDEA,
                               PointCategory.APPROVAL,
                               PointCategory.SELECTED_IDEA)
    must_highlight = category in categories_to_highlight

    points_sum = sum([p.nb_points for p in points])

    # title
    with h.div(class_='title ' + ('highlight' if must_highlight else '')):
        if security.has_permissions('view_points_detail', self):
            h << h.a(class_="toggle on", onclick='toggleCollapseExpand(this);')
            h << h.a(class_="toggle off", onclick='toggleCollapseExpand(this);')
        else:
            h << h.a(class_="toggle off", style='display:block;')
        h << h.span(_(category), class_='label')
        h << _(u': ')
        h << h.span(_(u'%d point(s)') % points_sum, class_='nb_points')

    # expandable details
    points.sort(key=operator.attrgetter('date'), reverse=True)
    if security.has_permissions('view_points_detail', self):
        with h.table(class_='items'):
            with h.thead:
                with h.colgroup:
                    h << h.col(class_='date') << h.col(class_='points')
                    if show_subject:
                        h << h.col(class_='subject')
                    if show_reason:
                        h.col(class_='reason')
                    if show_delete:
                        h.col(class_='action')
            with h.tbody:
                with h.tr:
                    h << h.th(_(u'Date')) << h.th(_(u'Points'))
                    if show_subject:
                        h << h.th(subject_title)
                    if show_reason:
                        h << h.th(reason_title)
                    if show_delete:
                        h << h.th
                for idx, p in enumerate(points):
                    with h.tr(class_='odd' if idx % 2 == 0 else 'even'):
                        formatted_date = format_datetime(p.date, format='short')
                        h << h.td(formatted_date, class_='date')
                        h << h.td(p.nb_points or '-', class_='nb_points')
                        if show_subject:
                            subj = p.subject_as_string()
                            h << h.td(ellipsize(subj, 60), title=subj)
                        if show_reason:
                            reason = p.reason or ''
                            h << h.td(ellipsize(reason, 50), title=reason, class_='reason')
                        if show_delete:
                            js = 'return yuiConfirm(this.href, "%s", "%s")' % (_(u'Confirm delete?'), _(u'This point item will be deleted permanently: are you sure?'))
                            h << h.td(h.a(_(u'Delete'),
                                          title=_(u'Delete'),
                                          class_='delete',
                                          onclick=js).action(lambda id=p.id: self.remove_point(id)))


# -------------------------------------------------------------------

@presentation.render_for(UserBrowser, model='filters')
def render_user_browser_filters(self, h, comp, *args):
    # field filter
    if self.pattern:
        results_counts = self.get_results_counts_per_field()
        with h.ul(class_='field-filter'):
            for field, name in self.SEARCH_FIELDS:
                count = results_counts.get(field, 0)
                if count > 0:
                    with h.li:
                        label = u"%s (%s)" % (name, count)
                        h << h.input(type='submit',
                                     class_='activated' if (field == self.search_field.value) else '',
                                     value=label).action(lambda field=field: self.search_field(field))

    return h.root


@presentation.render_for(UserBrowser)
def render_user_browser(self, h, comp, *args):
    with h.div(class_='user-browser user-pager'):
        # search bar & filters
        with h.form:
            h << comp.render(h, model='filters')

        # list of results
        if self.count() > 0:
            h << comp.render(h, model='list')
            h << comp.render(h, model='batch')

    return h.root
