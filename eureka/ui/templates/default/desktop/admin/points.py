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

from nagare import presentation, component
from nagare.i18n import _

from eureka.domain.queries import search_users_fulltext
from eureka.ui.common.choice import RadioChoice
from eureka.ui.common.yui2 import Autocomplete

from eureka.ui.desktop.admin import PointsAdmin


@presentation.render_for(PointsAdmin)
def render_points_admin(self, h, comp, *args):
    with h.div(class_='points-admin rounded'):
        h << comp.render(h, model='form')
    return h.root


@presentation.render_for(PointsAdmin, model='form')
def render_points_admin_form(self, h, comp, *args):
    def commit():
        if self.commit():
            comp.answer()

    with h.h1(class_="tab active big"):
        with h.span:
            h << h.a(_(u'Points management'))

    with h.form.post_action(self.check_users_have_enough_points):
        with h.div(class_='fields'):
            with h.fieldset:
                with h.legend:
                    h << _(u'Category:')

                items = list((label, value) for value, label, _ in self._ActionList)
                h << component.Component(RadioChoice(self.category, items))

            with h.div(class_='recipients-field field'):
                h << h.label(_(u'Recipients email addresses:'))
                autocomplete = Autocomplete(lambda s: search_users_fulltext(s, limit=20),
                                            delim_char=",",
                                            type='text',
                                            class_='text wide',
                                            max_results_displayed=20,
                                            value=self.users_emails(),
                                            action=self.users_emails,
                                            error=self.users_emails.error)
                h << component.Component(autocomplete).render(h)

            with h.div(class_='how-many-points-field field'):
                h << h.label(_(u'How many points?'))
                h << h.input(type='text',
                             class_='text wide',
                             value=self.points()).action(self.points).error(self.points.error)

            with h.div(class_='reason-field field'):
                h << h.label(_(u'Reason?'))
                h << h.input(type='text',
                             class_='text wide',
                             value=self.reason()).action(self.reason).error(self.reason.error)

        with h.div(class_='buttons'):
            h << h.input(type='submit',
                         class_='confirm-button',
                         value=_(u'Confirm')).action(commit)

    return h.root
