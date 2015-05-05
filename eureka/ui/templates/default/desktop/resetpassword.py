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

from nagare import presentation
from nagare.i18n import _

from eureka.ui.desktop.resetpassword import (ResetPassword,
                                             ResetPasswordConfirmation)


@presentation.render_for(ResetPassword)
def render_reset_password(self, h, comp, *args):
    def commit():
        if self.commit():
            comp.answer(True)

    def cancel():
        comp.answer(False)

    with h.form(class_='reset-password'):
        with h.p:
            h << _(u"To reset your password, please enter your login. You will then receive "
                   "an email that contains a link to reset your password.")

        with h.div(class_='fields'):
            with h.div(class_='login-field field'):
                field_id = h.generate_id('field')
                h << h.label(_(u'Login'),
                             for_=field_id)
                h << h.input(id=field_id,
                             type='text',
                             class_='text',
                             value=self.login()).action(self.login).error(self.login.error)

        with h.div(class_='buttons'):
            h << h.input(type='submit',
                         value=_(u'Reset my password')).action(commit)
            h << h.input(type='submit',
                         value=_(u'Cancel')).action(cancel)

    return h.root


@presentation.render_for(ResetPasswordConfirmation, model='failure')
def render_reset_password_confirmation_failure(self, h, comp, *args):
    with h.div(class_='reset-password-confirmation'):
        with h.p:
            h << _("""Password reset failure! The token received is either expired or invalid. Please try again.""")

        with h.form:
            with h.div(class_='buttons'):
                h << h.input(type='submit',
                             class_='ok-button',
                             value=_("Ok")).action(comp.answer)

    return h.root
