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

from nagare import presentation
from nagare.i18n import _, format_date

from eureka.ui.desktop.poll import PollEditor

from eureka.ui.desktop.admin import PollsAdmin


@presentation.render_for(PollsAdmin)
def render_polls_admin(self, h, comp, *args):
    with h.div(class_='polls-admin rounded'):
        if self.content():
            h << self.content
        else:
            h << comp.render(h, model='form')
    return h.root


@presentation.render_for(PollsAdmin, model='form')
def render_polls_admin_form(self, h, comp, *args):
    with h.h1(class_="tab active big"):
        h << h.span(h.a(_(u'Polls management')))

    with h.table(class_='datatable'):
        with h.thead:
            with h.tr:
                h << h.th(_(u'Title'))
                h << h.th(_(u'Question'))
                h << h.th(_(u'End date (included)'))
                h << h.th(_(u'Enabled'))
                h << h.th(_(u'Actions'), class_='actions')

        with h.tbody:
            for poll in self.polls:
                with h.tr:
                    with h.td:
                        h << h.a(
                            poll.title,
                            title=_(u'Edit the poll')
                        ).action(lambda id=poll.id: self.content.call(PollEditor(id)))

                    with h.td:
                        h << h.a(
                            poll.question,
                            title=_(u'Edit the poll')
                        ).action(lambda id=poll.id: self.content.call(PollEditor(id)))

                    with h.td:
                        one_day = timedelta(days=1)
                        end_date = format_date(poll.end_date - one_day)
                        h << end_date

                    with h.td:
                        if poll.enabled:
                            h << h.a(_(u'Yes'),
                                     title=_(u'Disable'),
                                     class_='yes').action(lambda id=poll.id: self.set_enabled(id, False))
                        else:
                            h << h.a(_(u'No'),
                                     title=_(u'Enable'),
                                     class_='no').action(lambda id=poll.id: self.set_enabled(id, True))

                    with h.td(class_='actions'):
                        title = _(u'Confirm delete?')
                        message = _(u'The poll will be deleted. Are you sure?')
                        js = 'return yuiConfirm(this.href, "%s", "%s", "%s", "%s")' % (title, message, _(u'Delete'), _(u'Cancel'))
                        h << h.a(_(u'Delete the poll'),
                                 title=_(u'Delete the poll'),
                                 class_='delete-poll',
                                 onclick=js).action(lambda id=poll.id: self.delete_poll(id))

    with h.div(class_='buttons'):
        h << h.a(_(u'Add a poll'),
                 class_='confirm-button').action(lambda: self.content.call(PollEditor()))

    return h.root
