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

from datetime import datetime, timedelta

from nagare import presentation
from nagare.i18n import _, format_date

from eureka.domain.models import ChallengeStatus
from eureka.ui.desktop.challenge import ChallengeEditor

from eureka.ui.desktop.admin import ChallengesAdmin


def render_title(h, title):
    return h.h1(h.span(h.a(title)), class_="tab active big")


@presentation.render_for(ChallengesAdmin)
def render_challenges_admin(self, h, comp, *args):
    with h.div(class_='challenges-admin rounded'):
        if self.content():
            h << self.content
        else:
            h << comp.render(h, model='menu')
    return h.root


@presentation.render_for(ChallengesAdmin, model='menu')
def render_challenges_admin_menu(self, h, comp, *args):
    ChallengeStatusMappings = {  # labels and CSS class for each status
        ChallengeStatus.NotStarted: (_(u'Not started'), 'status-not-started'),
        ChallengeStatus.InProgress: (_(u'In progress'), 'status-in-progress'),
        ChallengeStatus.Finished: (_(u'Finished'), 'status-finished')
    }

    h << render_title(h, _(u'Challenges management'))
    ref_date = datetime.now()
    with h.table(class_='datatable'):
        with h.thead:
            with h.tr:
                h << h.th(_(u'Challenge name'))
                h << h.th(_(u'Status'))
                h << h.th(_(u'Actions'), class_='actions')

        with h.tbody:
            for challenge in self.challenges:
                with h.tr:
                    with h.td:
                        h << h.a(
                            challenge.title,
                            title=_(u'Edit the challenge')
                        ).action(lambda id=challenge.id: self.content.call(ChallengeEditor(challenge=id, mobile_access=self.mobile_access)))

                    with h.td:
                        # status
                        status = challenge.status(ref_date)
                        label, css_class = ChallengeStatusMappings[status]

                        # dates
                        one_day = timedelta(days=1)
                        start_date = format_date(challenge.starting_date)
                        end_date = format_date(challenge.ending_date - one_day)
                        title = _(u'From %(start_date)s to %(end_date)s') % dict(start_date=start_date, end_date=end_date)

                        h << h.span(label,
                                    title=title,
                                    class_=css_class)

                    with h.td(class_='actions'):
                        if challenge.is_deletable:
                            title = _(u'Confirm delete?')
                            message = _(u'The challenge will be deleted. Are you sure?')
                            js = 'return yuiConfirm(this.href, "%s", "%s", "%s", "%s")' % (title, message, _(u'Delete'), _(u'Cancel'))
                            h << h.a(_(u'Delete the challenge'),
                                     title=_(u'Delete the challenge'),
                                     class_='delete-challenge',
                                     onclick=js).action(lambda id=challenge.id: self.delete_challenge(id))

    with h.div(class_='buttons'):
        h << h.a(_(u'Add a challenge'),
                 class_='confirm-button').action(lambda: self.content.call(ChallengeEditor(mobile_access=self.mobile_access)))

    return h.root
