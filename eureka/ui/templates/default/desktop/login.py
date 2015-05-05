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

from nagare import presentation, ajax
from nagare.i18n import _

from eureka.ui.desktop.login import Login, LoginEvent, CancelLoginEvent
from eureka.ui.desktop.resetpassword import ResetPasswordEvent


def render_login(self, h, comp, with_cancel, with_forgot_password, with_help):

    def login():
        if self.commit():
            comp.answer(LoginEvent())

    def cancel():
        self.form_opened(False)
        comp.answer(CancelLoginEvent())

    def reset_password():
        comp.answer(ResetPasswordEvent())

    with h.div(class_='connect'):
        with h.form:
            with h.div(class_='fields'):
                with h.div(class_='login-field field'):
                    field_id = h.generate_id('field')
                    help = _(u"Enter you login: first letter of your firstname + your name (e.g. jdoe)")
                    h << h.input(id=field_id,
                                 type='text',
                                 class_='text',
                                 title=help,
                                 name='__ac_name',
                                 placeholder=_(u'Login'))

                with h.div(class_='password-field field'):
                    field_id = h.generate_id('field')
                    help = _(u"Enter your password: on first connection, enter the one you received by email")
                    h << h.input(id=field_id,
                                 type='password',
                                 class_='text',
                                 title=help,
                                 name='__ac_password',
                                 placeholder=_(u'Password'))

            with h.div(class_='buttons'):
                if with_forgot_password:
                    label = _(u'Forgot your password?')
                    h << h.a(label,
                             title=label,
                             class_='forgot-password').action(reset_password)

                with h.div:
                    label = _(u'Connect')
                    h << h.input(type='submit',
                                 value=label,
                                 title=label).action(login)

                    if with_cancel:
                        # WARNING: this is not a submit button, otherwise __ac
                        # fields are submitted and the login is performed
                        label = _(u'Cancel')
                        cancel_url = h.a.action(cancel).get('href')
                        h << h.input(type='submit',
                                     onclick='window.location="%s";return false' % cancel_url,
                                     value=label,
                                     title=label).action(cancel)

            if with_help:
                with h.div(class_='help rounded'):
                    with h.h2:
                        h << _(u"First connection?")

                    with h.p:
                        h << _(u"Enter you login: first letter of your firstname + your name (e.g. jdoe)")

                    with h.p:
                        h << _(u"Enter the temporary password that have been sent to you by email")


@presentation.render_for(Login)
def render_login_default(self, h, comp, *args):
    if self.form_opened():
        render_login(self, h, comp, with_cancel=True, with_forgot_password=True, with_help=False)
    else:
        with h.div(class_="connect"):
            h << h.a(_(u'Connection')).action(lambda: self.form_opened(True))

    return h.root


@presentation.render_for(Login, model='form')
def render_login_default(self, h, comp, *args):
    render_login(self, h, comp, with_cancel=True, with_forgot_password=True, with_help=False)
    return h.root


@presentation.render_for(Login, model='prompt')
def render_login_dialog(self, h, comp, *args):
    render_login(self, h, comp, with_cancel=True, with_forgot_password=True, with_help=True)
    return h.root
