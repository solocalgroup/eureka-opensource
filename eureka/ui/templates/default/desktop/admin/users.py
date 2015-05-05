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

import json
from nagare import presentation, ajax, component, security
from nagare.i18n import _

from eureka.domain.models import RoleLabels
from eureka.domain.repositories import UserRepository

from eureka.ui.desktop.admin import (UserFilter, FIEditor, DIEditor,
                                     UserEditor, UserLineEditor,
                                     UserAdmin, FIAdmin, DIAdmin)


# FIXME: remove dashboard related names

@presentation.render_for(UserFilter)
def render_user_filter(self, h, comp, *args):
    id = h.generate_id('filterline')
    on_change = ajax.js('this.form.submit();')

    with h.div(id=id, class_='filterline'):
        with h.form.post_action(self.post_action):
            with h.div(class_='cell'):
                h << h.input(type='text',
                             class_="text",
                             title=_(u'Login'),
                             value=self.uid()).action(self.uid)

            with h.div(class_='cell select-box'):
                with h.select(onchange=on_change).action(self.corporation_id) as s:
                    for v in self.get_corporations():
                        h << h.option(u'%s' % (v[0]), value=v[1]).selected(self.corporation_id())
                h << s.error(self.corporation_id.error)

            with h.div(class_='cell select-box'):
                with h.select(onchange=on_change).action(self.direction_id) as s:
                    for v in self.get_directions():
                        h << h.option(u'%s' % (v[0]),
                                      value=v[1]).selected(self.direction_id())
                h << s.error(self.direction_id.error)

            with h.div(class_='cell select-box'):
                with h.select(onchange=on_change).action(self.service_id) as s:
                    for v in self.get_services():
                        h << h.option(u'%s' % (v[0]), value=v[1]).selected(self.service_id())
                h << s.error(self.service_id.error)

            with h.div(class_='cell select-box'):
                with h.select(onchange=on_change).action(self.site_id) as s:
                    for v in self.get_sites():
                        h << h.option(u'%s' % (v[0]), value=v[1]).selected(self.site_id())
                h << s.error(self.site_id.error)

            with h.div(class_='cell select-box'):
                with h.select(onchange=on_change).action(self.fi_uid) as s:
                    h << h.option(_(u'All the facilitators'), value='-1').selected(self.fi_uid())
                    for user in self.get_facilitators():
                        h << h.option(user.fullname, value=user.uid).selected(self.fi_uid())
                h << s.error(self.fi_uid.error)

            with h.div(class_='cell select-box'):
                with h.select(onchange=on_change).action(self.enabled):
                    h << h.option(_(u'By state'), value='-1').selected(self.enabled())
                    h << h.option(_(u'Enabled'), value=_(u'Enabled')).selected(self.enabled())
                    h << h.option(_(u'Disabled'), value=_(u'Disabled')).selected(self.enabled())

            with h.div(class_='cell'):
                h << h.input(type="submit", class_="action", value=_(u'Filter'))

    return h.root


def text_input(h, field, disabled):
    if disabled:
        h << h.span(field(), class_='readonly-text-input')
    else:
        h << h.input(type='text', class_='text', value=field()).action(field).error(field.error)


def select(h, field, values, disabled, on_change):
    if disabled:
        selected = u'---------------'
        for label, value in values:
            if str(value) == str(field()):
                selected = label
                break
        h << h.span(selected, class_='readonly-text-input')
    else:
        options = [h.option(u'---------------', value='-1').selected(str(field()))]
        for label, value in values:
            options.append(h.option(u'%s' % label, value=value).selected(str(field())))
        _select = h.select(options, onchange=on_change).action(field)
        h << _select.error(field.error)


def selected_label(current_value, values, default=u'---------------'):
    current_value = str(current_value)
    for label, value in values:
        if str(value) == current_value:
            return label
    return default


@presentation.render_for(UserEditor)
def render_user_editor(self, h, comp, *args):
    # should not be rendered in ajax, or provide our own async renderer just in case
    on_change_corp = self.change_corp
    on_change_corp = ajax.Update(action=on_change_corp)
    on_change_corp = on_change_corp.generate_action(4, h)

    on_change_dir = self.change_dir
    on_change_dir = ajax.Update(action=on_change_dir)
    on_change_dir = on_change_dir.generate_action(4, h)

    on_change_service = self.change_service
    on_change_service = ajax.Update(action=on_change_service)
    on_change_service = on_change_service.generate_action(4, h)

    on_change_site = lambda: None
    on_change_site = ajax.Update(action=on_change_site)
    on_change_site = on_change_site.generate_action(4, h)

    # Profile was imported by a batch script, some fields must be set readonly
    profile_imported = self.profile_imported

    if profile_imported:
        h << h.div(_('This account was automatically imported and updated, some fields cannot be modified'),
                   class_='readonly-explain')

    with h.div(class_="userForm"):
        with h.form.pre_action(self.pre_action):
            with h.div(class_="left_form padded"):
                h << h.h1(_(u'Login'))

                # Editable in creation only
                text_input(h, self.login, not self.creation_mode)

                h << h.h1(_(u'Email'))
                text_input(h, self.email, profile_imported)

                h << h.h1(_(u'First name'))
                text_input(h, self.firstname, profile_imported)

                h << h.h1(_(u'Last name'))
                text_input(h, self.lastname, profile_imported)

                h << h.h1(_(u'Facilitator'))
                with h.select().action(self.fi_uid) as s:
                    h << h.option(_(u'Choose a facilitator'), value="")
                    for user in self.get_facilitators():
                        h << h.option(user.fullname, value=user.uid).selected(str(self.fi_uid()))
                h << s.error(self.fi_uid.error)

                h << h.h1(_(u'Roles and access rights'))
                for role in self.assignable_roles:
                    h << h.input(type="checkbox",
                                 class_='checkbox',
                                 value=role).selected(role in self.roles()).action(lambda role=role: self.add_role(role))
                    h << h.label(unicode(RoleLabels[role]))
                    h << h.br

                h << h.h1(_(u'Enabled'))
                h << h.input(type='radio',
                             class_='radio',
                             name="enabled").selected(self.enabled()).action(lambda: self.enabled(True))
                h << h.label(_(u"Yes"))
                h << h.br
                h << h.input(type='radio',
                             class_='radio',
                             name="enabled").selected(not self.enabled()).action(lambda: self.enabled(False))
                h << h.label(_(u"No"))
                h << h.br

            with h.div(class_="right_form"):
                h << h.h1(_(u'Office phone'))
                text_input(h, self.work_phone, profile_imported)

                h << h.h1(_(u'Mobile phone'))
                text_input(h, self.mobile_phone, profile_imported)

                h << h.h1(_(u'Position'))
                text_input(h, self.position, profile_imported)

                h << h.h1(_(u'Corporation'))
                select(h, self.corporation_id, self.get_corporations(), profile_imported, on_change_corp)

                if self.corporation_id() != '-1':
                    h << h.h1(_(u'Direction'))
                    select(h, self.direction_id, self.get_directions(), profile_imported, on_change_dir)

                if self.direction_id() != '-1':
                    h << h.h1(_(u'Service'))
                    select(h, self.service_id, self.get_services(), profile_imported, on_change_service)

                if self.service_id() != '-1':
                    h << h.h1(_(u'Site'))
                    select(h, self.site_id, self.get_sites(), profile_imported, on_change_site)

                h << h.h1(_(u'Incorporated'))
                h << h.input(type='radio',
                             class_='radio',
                             name="incorporated").selected(self.incorporated()).action(lambda: self.incorporated(True))
                h << h.label(_(u"Yes"))
                h << h.br
                h << h.input(type='radio',
                             class_='radio',
                             name="incorporated").selected(not self.incorporated()).action(lambda: self.incorporated(False))
                h << h.label(_(u"No"))
                h << h.br

            with h.div(class_="form_actions"):
                h << h.input(type="submit", class_="action",
                             value=_(u'Validate')).action(lambda: self.commit() and comp.answer(self.login.value))
                if self.uid:
                    sync = h.SyncRenderer()
                    h << sync.a(_(u'View profile'),
                                class_='profile_link',
                                href=self.profile_url)  # .action(self.view_profile)

    return h.root


@presentation.render_for(UserLineEditor)
def render_user_line_editor(self, h, comp, *args):
    current_uid = security.get_user().uid
    id = h.generate_id('userline')

    on_change_corp = self.change_corp
    on_change_corp = ajax.Update(action=on_change_corp)
    on_change_corp = on_change_corp.generate_action(4, h)

    on_change_dir = self.change_dir
    on_change_dir = ajax.Update(action=on_change_dir)
    on_change_dir = on_change_dir.generate_action(4, h)

    on_change_service = self.change_service
    on_change_service = ajax.Update(action=on_change_service)
    on_change_service = on_change_service.generate_action(4, h)

    on_change = lambda: None
    on_change = ajax.Update(action=on_change)
    on_change = on_change.generate_action(4, h)

    # Profile was imported by a batch script, some fields must be set readonly
    profile_imported = self.profile_imported

    with h.form:
        with h.div(id=id):
            with h.span(class_='name'):
                h << h.a(self.fullname,
                         href=('users_admin/%s' % self.uid)).action(lambda: self.edit_user(comp))

            if profile_imported:
                with h.span(class_="select-box readonly"):
                    h << selected_label(self.corporation_id(), self.get_corporations())
                with h.span(class_="select-box readonly"):
                    h << selected_label(self.direction_id(), self.get_directions())
                with h.span(class_="select-box readonly"):
                    h << selected_label(self.service_id(), self.get_services())
                with h.span(class_="select-box readonly"):
                    h << selected_label(self.site_id(), self.get_sites())
            else:
                with h.span(class_="select-box"):
                    with h.select(onchange=on_change_corp).action(self.corporation_id):
                        h << h.option(u'---------------', value='-1').selected(str(self.corporation_id()))
                        for v in self.get_corporations():
                            h << h.option(u'%s' % (v[0]), value=v[1]).selected(str(self.corporation_id()))

                with h.span(class_="select-box"):
                    with h.select(onchange=on_change_dir).action(self.direction_id):
                        h << h.option(u'---------------', value='-1').selected(str(self.direction_id()))
                        for v in self.get_directions():
                            h << h.option(u'%s' % (v[0]), value=v[1]).selected(str(self.direction_id()))

                with h.span(class_="select-box"):
                    with h.select(onchange=on_change_service).action(self.service_id):
                        h << h.option(u'---------------', value='-1').selected(str(self.service_id()))
                        for v in self.get_services():
                            h << h.option(u'%s' % (v[0]), value=v[1]).selected(str(self.service_id()))

                with h.span(class_="select-box"):
                    with h.select(onchange=on_change).action(self.site_id):
                        h << h.option(u'---------------', value='-1').selected(str(self.site_id()))
                        for v in self.get_sites():
                            h << h.option(u'%s' % (v[0]), value=v[1]).selected(str(self.site_id()))

            with h.span(class_="select-box"):
                with h.select(onchange=on_change).action(self.fi_uid) as s:
                    for user in self.get_facilitators():
                        h << h.option(user.fullname, value=user.uid).selected(self.fi_uid())
                h << s.error(self.fi_uid.error)

            with h.span(class_="no_border"):
                input_ = h.input(type='checkbox',
                                 class_='checkbox',
                                 name='activated').selected(self.enabled())
                if current_uid != self.uid:
                    input_.action(ajax.Update(action=lambda v: self.enabled(not self.enabled())))
                else:
                    input_.set('disabled', 'disabled')
                h << input_

            with h.span(class_="last"):
                if self.need_update():
                    h << h.input(type="submit", class_="action",
                                 value=_(u'Validate')).action(lambda: self.update_user())

    return h.root


# --------- user administration ---------

@presentation.render_for(UserAdmin)
def render_user_admin(self, h, comp, *args):
    async = h.AsyncRenderer()

    with h.div(class_="user-admin rounded"):
        h << comp.render(h, model='users_list')

        with h.div(class_='user-admin-item user_list'):
            h << h.h1(_(u'Create user'))
            h << self.create_user.render(async)

    return h.root


@presentation.render_for(UserAdmin, model='users_list')
def render_user_admin_users_list(self, h, comp, *args):
    current_uid = security.get_user().uid
    protected_uids = [e.uid for e in UserRepository().protected_accounts if e]
    async = h.AsyncRenderer()
    with h.h1(class_="tab active big"):
        h << h.span(h.a(_(u'User management')))

    with h.div(class_='user-admin-item user_list'):
        h << h.h1(_(u'Manage users'))
        with h.div:
            # filters
            h << self.filter.render(h)

            with h.table(class_="inline-edit-list with-delete"
                         if self.with_delete else 'inline-edit-list'):
                with h.thead:
                    with h.tr:
                        with h.th:
                            h << h.span(_(u'Name'), class_='name')
                            h << h.span(_(u'Corporation'))
                            h << h.span(_(u'Direction'))
                            h << h.span(_(u'Service'))
                            h << h.span(_(u'Site'))
                            h << h.span(_(u'Facilitator'))
                            h << h.span(_(u'Enabled'), class_='enabled')
                            h << h.span("", class_="last")
                        if self.with_delete:
                            with h.th(class_='delete-column'):
                                h << h.span(_(u'Delete'))
                with h.tbody:
                    for ind, elt in enumerate(self.get_users_comp()[:self.batch_size]):
                        with h.tr(class_=['odd', 'even'][ind % 2]):
                            with h.td:
                                h << elt.render(async)
                            if self.with_delete:
                                with h.td(class_='delete-column'):
                                    if current_uid != elt().uid and elt().uid not in protected_uids:
                                        link = h.a(_('Delete')).action(lambda uid=elt().uid: self.delete(uid))
                                        msg = _('''User deletion can't be reverted, are you sure you want to delete the account %s ?''') % elt().fullname
                                        link.set('onclick', 'if (! confirm(%s)) return false;' % (json.dumps(msg)))
                                        h << link

            h << comp.render(h, 'batch')

    return h.root


@presentation.render_for(UserAdmin, model='batch')
def render_user_admin_batch(self, h, *args):
    """ Batch part screen """
    has_previous = (self.start != 0)
    has_next = (self.get_users().count() > self.batch_size)
    if has_previous or has_next:
        with h.div(class_="batch"):
            nb_users = self.get_nb_users()
            if nb_users % self.batch_size:
                total_page = max((nb_users / self.batch_size) + 1, 1)
            else:
                total_page = max((nb_users / self.batch_size), 1)

            first_page = 1
            last_page = total_page

            page_num = (self.start / self.batch_size) + 1

            leftmost_page = max(first_page, (page_num - self.radius))
            rightmost_page = min(last_page, (page_num + self.radius))

            if has_previous:
                h << h.a('<< ', _(u'Previous'), class_="back").\
                    action(self.decrease)
            else:
                h << h.a('', class_="back")

            if has_next:
                h << h.a(_(u'Next'), " >>", class_="next").\
                    action(self.increase)
            else:
                h << h.a('', class_="next")

            with h.div(class_="pages"):

                page_list = range(leftmost_page, rightmost_page + 1)

                if leftmost_page != first_page:
                    if page_num == first_page:
                        h << h.span(first_page, class_='current')
                    else:
                        h << h.a(first_page, href="users_admin").\
                            action(lambda: self.goto_page(first_page))

                if leftmost_page > first_page + 1:
                    h << h.a("...")

                for ind in page_list:
                    if ind == page_num:
                        h << h.span(ind, class_='current')
                    else:
                        h << h.a(ind, href="users_admin").\
                            action(lambda p=ind: self.goto_page(p))

                if rightmost_page < last_page - 1:
                    h << h.a("...")

                if rightmost_page != last_page:
                    if page_num == last_page:
                        h << h.span(last_page, class_='current')
                    else:
                        h << h.a(last_page, href="users_admin").\
                            action(lambda: self.goto_page(last_page))
    return h.root


# --------- facilitator administration ---------

# FIXME: we should factor the user list that appear multiple times

@presentation.render_for(FIAdmin)
def render_fi_admin(self, h, comp, *args):
    with h.div(class_="fi-admin rounded"):
        with h.h1(class_="tab active big"):
            h << h.span(h.a(_(u'Facilitator management')))

        with h.div(class_='user-admin-item'):
            with h.p:
                h << _(u'You can delete a facilitator by clicking on the icon of the first '
                       'column, or replace a facilitator by clicking on its name.')

            with h.div:
                with h.table(class_="edit-list"):
                    for c in ('select', 'name', 'company', 'direction', 'service', 'site', 'fi', 'enabled'):
                        h << h.col(class_=c)

                    with h.thead:
                        with h.tr:
                            h << h.th(class_="first_col")
                            h << h.th(_(u'Name'), class_='name')
                            h << h.th(_(u'Corporation'))
                            h << h.th(_(u'Direction'))
                            h << h.th(_(u'Service'))
                            h << h.th(_(u'Site'))
                            h << h.th(_(u'Facilitator'))
                            h << h.th(_(u'Enabled'))

                    with h.tbody:
                        for idx, user in enumerate(self._users()):
                            with h.tr(class_=['odd', 'even'][idx % 2]):
                                with h.td(class_="first_col"):
                                    label = _(u"Delete the facilitator")
                                    h << h.a(label, title=label, class_="delete-user").\
                                        action(lambda uid=user.uid: self.confirm_delete_fi(uid, comp))

                                with h.td:
                                    h << h.a(user.fullname).\
                                        action(lambda uid=user.uid: comp.call(FIEditor(uid)))

                                h << h.td(user.corporation_label)
                                h << h.td(user.direction_label)
                                h << h.td(user.service_label)
                                h << h.td(user.site_label)
                                h << h.td(user.fi.fullname)
                                h << h.td(_(u'Yes') if user.enabled else _(u'No'))

    return h.root


@presentation.render_for(FIEditor)
def render_fi_editor(self, h, comp, *args):
    async = h.AsyncRenderer()

    with h.div(class_='fi-editor rounded'):
        with h.h1(class_="tab active big"):
            h << h.span(h.a(_(u'Facilitator: %s') % self.user.fullname))

        with h.div(class_='user-admin-item'):
            h << component.Component(self).render(async, model='add_entity')

        with h.div(class_='user-admin-item'):
            h << comp.render(h, model='replace_facilitator')

    return h.root


@presentation.render_for(FIEditor, model='replace_facilitator')
def render_fi_editor_replace_facilitator(self, h, comp, *args):
    def commit():
        if self.replace_facilitator():
            comp.answer()

    with h.h1:
        h << _(u'Replace this facilitator')

    with h.p:
        h << _(u'Select the new facilitator to replace "%s" by. This will '
               'change the facilitator of all the matching users.') % self.user.fullname

    h << self.filter.render(h)

    with h.form.pre_action(self.clear_successor):
        with h.table(class_="edit-list replace-facilitator"):
            for c in ('select', 'name', 'corporation', 'direction', 'service', 'site', 'fi', 'enabled'):
                h << h.col(class_=c)

            with h.thead:
                with h.tr:
                    h << h.th('')
                    h << h.th(_(u'Name'), class_='name')
                    h << h.th(_(u'Corporation'))
                    h << h.th(_(u'Direction'))
                    h << h.th(_(u'Service'))
                    h << h.th(_(u'Site'))
                    h << h.th(_(u'Facilitator'))
                    h << h.th(_(u'Enabled'))

            with h.tbody:
                for idx, user in enumerate(self.get_fi_users()):
                    with h.tr(class_=['odd', 'even'][idx % 2]):
                        with h.td:
                            h << h.input(type='radio',
                                         class_='radio',
                                         name='new_fi').action(lambda uid=user.uid: self.successor(uid))

                        h << h.td(user.fullname)
                        h << h.td(user.corporation_label)
                        h << h.td(user.direction_label)
                        h << h.td(user.service_label)
                        h << h.td(user.site_label)
                        h << h.td(user.fi.fullname)
                        h << h.td(_(u'Yes') if user.enabled else _(u'No'))

        with h.div(class_='buttons'):
            h << h.input(type="submit",
                         value=_(u'Validate')).action(commit)

    return h.root


@presentation.render_for(FIEditor, model='add_entity')
def render_fi_editor_add_entity(self, h, comp, *args):
    on_change_corp = self.change_corp
    on_change_corp = ajax.Update(action=on_change_corp)
    on_change_corp = on_change_corp.generate_action(4, h)

    on_change_dir = self.change_dir
    on_change_dir = ajax.Update(action=on_change_dir)
    on_change_dir = on_change_dir.generate_action(4, h)

    on_change_service = self.change_service
    on_change_service = ajax.Update(action=on_change_service)
    on_change_service = on_change_service.generate_action(4, h)

    on_change_site = lambda: None
    on_change_site = ajax.Update(action=on_change_site)
    on_change_site = on_change_site.generate_action(4, h)

    with h.h1:
        h << _(u'Assign an entity to the facilitator')

    with h.p:
        h << _(u'Select the entity to assign to "%s". This will reassign all users '
               'of this entity to the facilitator.') % self.user.fullname

    with h.form:
        with h.table(class_="edit-list add-entity"):
            for c in ('corporation', 'direction', 'service', 'site'):
                h << h.col(class_=c)

            with h.thead:
                with h.tr:
                    h << h.th(_(u'Corporation'))
                    h << h.th(_(u'Direction'))
                    h << h.th(_(u'Service'))
                    h << h.th(_(u'Site'))

            with h.tbody:
                with h.td:
                    with h.select(onchange=on_change_corp).action(self.corporation_id) as s:
                        h << h.option('---------------', value='-1').selected(str(self.corporation_id()))
                        for v in self.get_corporations():
                            h << h.option(u'%s' % v[0], value=v[1]).selected(str(self.corporation_id()))
                    h << s.error(self.corporation_id.error)

                with h.td:
                    with h.select(onchange=on_change_dir).action(self.direction_id) as s:
                        h << h.option('---------------', value='-1').selected(str(self.direction_id()))
                        for v in self.get_directions():
                            h << h.option(u'%s' % v[0], value=v[1]).selected(str(self.direction_id()))
                    h << s.error(self.direction_id.error)

                with h.td:
                    with h.select(onchange=on_change_service).action(self.service_id) as s:
                        h << h.option('---------------', value='-1').selected(str(self.service_id()))
                        for v in self.get_services():
                            h << h.option(u'%s' % v[0], value=v[1]).selected(str(self.service_id()))
                    h << s.error(self.service_id.error)

                with h.td:
                    with h.select(onchange=on_change_site).action(self.site_id) as s:
                        h << h.option('---------------', value='-1').selected(str(self.site_id()))
                        for v in self.get_sites():
                            h << h.option(u'%s' % v[0], value=v[1]).selected(str(self.site_id()))
                    h << s.error(self.site_id.error)

        with h.div(class_='buttons'):
            h << h.input(type="submit", class_="action",
                         value=_(u'Validate')).action(lambda: self.add_entity())

    return h.root


# --------- developer administration ---------

@presentation.render_for(DIAdmin)
def render_di_admin(self, h, comp, *args):
    with h.div(class_="di-admin rounded"):
        with h.h1(class_="tab active big"):
            h << h.span(h.a(_(u'Experts management')))

        with h.div(class_='user-admin-item'):
            with h.p:
                h << _(u'You can delete an expert by clicking on the icon '
                       u'of the first column, or change its domain by '
                       u'clicking on its name.')

            with h.div:
                with h.table(class_="edit-list"):
                    for c in ('select', 'name', 'company', 'direction',
                              'service', 'site', 'business-area', 'fi',
                              'enabled'):
                        h << h.col(class_=c)

                    with h.thead:
                        with h.tr:
                            h << h.th(class_="first_col")
                            h << h.th(_(u'Name'), class_='name')
                            h << h.th(_(u'Corporation'))
                            h << h.th(_(u'Direction'))
                            h << h.th(_(u'Service'))
                            h << h.th(_(u'Site'))
                            h << h.th(_(u'Business Area'))
                            h << h.th(_(u'Facilitator'))
                            h << h.th(_(u'Enabled'))

                    with h.tbody:
                        for idx, user in enumerate(self._users()):
                            with h.tr(class_=['odd', 'even'][idx % 2]):
                                with h.td(class_="first_col"):
                                    label = _(u'Delete the expert')
                                    h << h.a(label, title=label, class_="delete-user").\
                                        action(lambda uid=user.uid: self.confirm_delete_di(uid, comp))

                                with h.td:
                                    h << h.a(user.fullname).\
                                        action(lambda uid=user.uid: comp.call(DIEditor(uid)))

                                h << h.td(user.corporation_label)
                                h << h.td(user.direction_label)
                                h << h.td(user.service_label)
                                h << h.td(user.site_label)
                                h << h.td(user.di_business_area or '')
                                h << h.td(user.fi.fullname)
                                h << h.td(_(u'Yes') if user.enabled else _(u'No'))

    return h.root


@presentation.render_for(DIEditor)
def render_di_editor(self, h, comp, *args):
    with h.div(class_='di-editor rounded'):
        with h.h1(class_="tab active big"):
            user = self.user
            h << h.span(h.a(_(u'Expert: %s') % user.fullname))

        with h.div(class_='user-admin-item'):
            h << comp.render(h, model='update_di_business_area')

        with h.div(class_='user-admin-item'):
            h << comp.render(h, model='update_domains')

        with h.div(class_='user-admin-item'):
            h << comp.render(h, model='replace_developer')

    return h.root


@presentation.render_for(DIEditor, model='update_domains')
def render_di_editor_update_domains(self, h, comp, *args):
    def commit():
        if self.update_domains():
            comp.answer()

    with h.h1:
        h << _(u'Assign domains to the expert')

    with h.p:
        h << _(u'Select one or more domains that the expert can handle')

    with h.form.pre_action(self.clear_domains):
        with h.select(multiple="multiple").action(self.domains) as s:
            for domain in self.get_all_domains():
                h << h.option(domain.i18n_label, value=domain.id).selected(self.domains())
        h << s.error(self.domains.error)

        with h.div(class_='buttons'):
            h << h.input(type="submit",
                         value=_(u'Validate')).action(commit)

    return h.root


@presentation.render_for(DIEditor, model='update_di_business_area')
def render_di_editor_update_di_business_area(self, h, comp, *args):
    def commit():
        if self.update_di_business_area():
            comp.answer()

    with h.h1:
        h << _(u"Expert's Business Area")

    with h.form:
        with h.p:
            h << _(u"Please enter the expert's business area")

        with h.div(class_='fields'):
            h << h.input(type='text',
                         class_='text wide',
                         value=self.di_business_area()).action(self.di_business_area).error(self.di_business_area.error)

        if self.user.specialty:
            with h.p:
                h << _("For your information, here is the specialty defined in the expert's profile:") << h.br
                h << self.user.specialty

        with h.div(class_='buttons'):
            h << h.input(type="submit",
                         value=_(u'Validate')).action(commit)

    return h.root


@presentation.render_for(DIEditor, model='replace_developer')
def render_di_editor_replace_developer(self, h, comp, *args):
    def commit():
        if self.replace_developer():
            comp.answer()

    with h.h1:
        h << _(u'Replace the expert')

    with h.p:
        h << _(u'Select the new expert to replace "%s" by. This will '
               'change the expert of all the matching ideas.') % self.user.fullname

    with h.form.pre_action(self.clear_successor):
        with h.table(class_="edit-list replace-developer"):
            for c in ('select', 'name', 'company', 'direction', 'service', 'site', 'business-area', 'fi', 'enabled'):
                h << h.col(class_=c)

            with h.thead:
                with h.tr:
                    h << h.th('')
                    h << h.th(_(u'Name'), class_='name')
                    h << h.th(_(u'Corporation'))
                    h << h.th(_(u'Direction'))
                    h << h.th(_(u'Service'))
                    h << h.th(_(u'Site'))
                    h << h.th(_(u'Business Area'))
                    h << h.th(_(u'Facilitator'))
                    h << h.th(_(u'Enabled'))

            with h.tbody:
                for idx, user in enumerate(self.get_di_users()):
                    with h.tr(class_=['odd', 'even'][idx % 2]):
                        with h.td:
                            h << h.input(type='radio',
                                         class_='radio',
                                         name='new_di').action(lambda uid=user.uid: self.successor(uid))

                        h << h.td(user.fullname)
                        h << h.td(user.corporation_label)
                        h << h.td(user.direction_label)
                        h << h.td(user.service_label)
                        h << h.td(user.site_label)
                        h << h.td(user.di_business_area or '')
                        h << h.td(user.fi.fullname)
                        h << h.td(_(u'Yes') if user.enabled else _(u'No'))

        if self.successor.error:
            with h.div(class_='error-message'):
                h << self.successor.error

        with h.div(class_='buttons'):
            h << h.input(type="submit",
                         value=_(u'Validate')).action(commit)

        return h.root
