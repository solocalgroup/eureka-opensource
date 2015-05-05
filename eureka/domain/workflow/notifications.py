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

from eureka.infrastructure.workflow.workflow import send_notifications

import peak.rules

from nagare.i18n import _

from .workflow import WFStates, WFEvents

from eureka.domain import mail_notification


# FIXME: fix every to=idea.submitted_by, should be either the di, fi or dsig depending on the email template. Update the template accordingly

@peak.rules.when(send_notifications,
                 "state == WFStates.INITIAL_STATE and "
                 "event == WFEvents.DRAFT_EVENT")
def send_notifications(from_user, idea, state, event, new_state, context, comment, notify, **kw):
    notify(_(u'Your idea has been saved as a draft'))


@peak.rules.when(send_notifications,
                 "state == WFStates.INITIAL_STATE and "
                 "event == WFEvents.SUBMIT_EVENT")
def send_notifications(from_user, idea, state, event, new_state, context, comment, notify, **kw):
    # SIGNAL f1
    for author in idea.authors:
        mail_notification.send('mail-idea-submitted-for-authors.html', to=author, idea=idea)

    # PROGRES a1
    mail_notification.send('mail-idea-submitted-for-ci.html', to=idea.submitted_by, idea=idea)

    notify(_(u'Your idea has been sent to your innovation facilitator'))


@peak.rules.when(send_notifications,
                 "state == WFStates.DRAFT_STATE and "
                 "event == WFEvents.SUBMIT_EVENT")
def send_notifications(from_user, idea, state, event, new_state, context, comment, notify, **kw):
    # SIGNAL f1
    for author in idea.authors:
        mail_notification.send('mail-idea-submitted-for-authors.html', to=author, idea=idea)

    # PROGRES a1
    mail_notification.send('mail-idea-submitted-for-ci.html', to=idea.submitted_by, idea=idea)

    notify(_(u'Your idea has been sent to your innovation facilitator'))


@peak.rules.when(send_notifications,
                 "state == WFStates.AUTHOR_NORMALIZE_STATE and "
                 "event == WFEvents.SUBMIT_EVENT")
def send_notifications(from_user, idea, state, event, new_state, context, comment, notify, **kw):
    # SIGNAL f1
    for author in idea.authors:
        mail_notification.send('mail-idea-submitted-for-authors.html', to=author, idea=idea)

    # PROGRES a1
    mail_notification.send('mail-idea-submitted-for-ci.html', to=idea.submitted_by, idea=idea)

    notify(_(u'Idea completed'))


@peak.rules.when(send_notifications,
                 "state == WFStates.RETURNED_BY_DI_STATE and "
                 "event == WFEvents.SUBMIT_EVENT")
def send_notifications(from_user, idea, state, event, new_state, context, comment, notify, **kw):
    notify(_(u'The idea has been sent to the idea developer'))


@peak.rules.when(send_notifications,
                 "state == WFStates.FI_NORMALIZE_STATE and "
                 "event == WFEvents.ASK_INFORMATIONS_EVENT")
def send_notifications(from_user, idea, state, event, new_state, context, comment, notify, **kw):
    # INFO a1
    for author in idea.authors:
        mail_notification.send('mail-idea-needs-info.html', to=author, comment=comment, idea=idea)

    notify(u'%s → %s' % (_(state), _(new_state)))


@peak.rules.when(send_notifications,
                 "state == WFStates.FI_NORMALIZE_STATE and "
                 "event == WFEvents.SEND_DI_EVENT")
def send_notifications(from_user, idea, state, event, new_state, context, comment, notify, **kw):
    # PROGRES a2
    for author in idea.authors:
        mail_notification.send('mail-idea-published.html', to=author, idea=idea)

    # SIGNAL d2
    mail_notification.send('mail-idea-submitted-for-di.html', to=idea.submitted_by, idea=idea)

    notify(u'%s → %s' % (_(state), _(new_state)))


@peak.rules.when(send_notifications,
                 "state == WFStates.DI_APPRAISAL_STATE and "
                 "event == WFEvents.SEND_DI_EVENT")
def send_notifications(from_user, idea, state, event, new_state, context, comment, notify, **kw):
    # RENVOI d2
    mail_notification.send('mail-idea-forward-for-di.html', to=idea.submitted_by, idea=idea, previous_di=kw['previous_di'])

    notify(u'%s → %s' % (_(state), _(new_state)))


@peak.rules.when(send_notifications,
                 "state == WFStates.DI_APPRAISAL_STATE and "
                 "event == WFEvents.ASK_INFORMATIONS_EVENT")
def send_notifications(from_user, idea, state, event, new_state, context, comment, notify, **kw):
    # INFO a2
    for author in idea.authors:
        mail_notification.send('mail-idea-needs-info-di.html', to=author, comment=comment, idea=idea)

    notify(u'%s → %s' % (_(state), _(new_state)))


@peak.rules.when(send_notifications,
                 "event == WFEvents.REFUSE_EVENT")
def send_notifications(from_user, idea, state, event, new_state, context, comment, notify, **kw):
    # REFUS a1-7
    for author in idea.authors:
        mail_notification.send('mail-idea-refused-by-ips.html', to=author, comment=comment, idea=idea)

    notify(u'%s → %s' % (_(state), _(new_state)))


@peak.rules.when(send_notifications,
                 "event == WFEvents.APPROVAL_EVENT")
def send_notifications(from_user, idea, state, event, new_state, context, comment, notify, **kw):
    # PROGRES a3
    for author in idea.authors:
        mail_notification.send('mail-idea-recommended.html', to=author, idea=idea)
    _report_state_changed(from_user, idea, new_state)

    notify(u'%s → %s' % (_(state), _(new_state)))


@peak.rules.when(send_notifications,
                 "event == WFEvents.SELECT_EVENT")
def send_notifications(from_user, idea, state, event, new_state, context, comment, notify, **kw):
    # PROGRES a4
    for author in idea.authors:
        mail_notification.send('mail-idea-selected.html', to=author, idea=idea)
    _report_state_changed(from_user, idea, new_state)

    notify(u'%s → %s' % (_(state), _(new_state)))


@peak.rules.when(send_notifications,
                 "event == WFEvents.SEND_PROJECT_EVENT")
def send_notifications(from_user, idea, state, event, new_state, context, comment, notify, **kw):
    # PROGRES a5
    for author in idea.authors:
        mail_notification.send('mail-idea-to-project.html', to=author, idea=idea)
    _report_state_changed(from_user, idea, new_state)

    notify(u'%s → %s' % (_(state), _(new_state)))


@peak.rules.when(send_notifications,
                 "event == WFEvents.SEND_PROTOTYPE_EVENT")
def send_notifications(from_user, idea, state, event, new_state, context, comment, notify, **kw):
    # PROGRES a6
    for author in idea.authors:
        mail_notification.send('mail-idea-to-prototype.html', to=author, idea=idea)
    _report_state_changed(from_user, idea, new_state)

    notify(u'%s → %s' % (_(state), _(new_state)))


@peak.rules.when(send_notifications,
                 "event == WFEvents.EXTEND_EVENT")
def send_notifications(from_user, idea, state, event, new_state, context, comment, notify, **kw):
    # PROGRES a7
    for author in idea.authors:
        mail_notification.send('mail-idea-deployed.html', to=author, idea=idea)
    _report_state_changed(from_user, idea, new_state)

    notify(u'%s → %s' % (_(state), _(new_state)))


@peak.rules.when(send_notifications,
                 "state == WFStates.FI_NORMALIZE_STATE and "
                 "event == WFEvents.DISTURBING_IDEA_EVENT")
def send_notifications(from_user, idea, state, event, new_state, context, comment, notify, **kw):
    # RENVOI Ips1
    mail_notification.send('mail-idea-forward-for-dsig-fi.html', to=idea.submitted_by, idea=idea)

    notify(u'%s → %s' % (_(state), _(new_state)))


@peak.rules.when(send_notifications,
                 "state == WFStates.DI_APPRAISAL_STATE and "
                 "event == WFEvents.DISTURBING_IDEA_EVENT")
def send_notifications(from_user, idea, state, event, new_state, context, comment, notify, **kw):
    # RENVOI Ips2
    mail_notification.send('mail-idea-forward-for-dsig-di.html', to=idea.submitted_by, comment=comment, idea=idea)

    notify(u'%s → %s' % (_(state), _(new_state)))


@peak.rules.when(send_notifications,
                 "(state == WFStates.DSIG_BASKET_STATE and "
                 "event == WFEvents.NOT_DISTURBING_IDEA_EVENT)")
def send_notifications(from_user, idea, state, event, new_state, context, comment, notify, **kw):
    notify(u'%s → %s' % (_(state), _(new_state)))


@peak.rules.when(send_notifications,
                 "event == WFEvents.REOPEN_EVENT")
def send_notifications(from_user, idea, state, event, new_state, context, comment, notify, **kw):
    notify(_(u'Idea successfully reissued'))


def _report_state_changed(from_user, idea, new_state):
    from eureka.domain.models import EventType, StateData
    new_state_data = StateData.get_by(label=new_state)

    # send the state change event
    event_users = set(user for user in (idea.tracked_by + idea.authors) if user.uid != from_user.uid)
    for user in event_users:
        user.add_event(EventType.StateChanged, idea)

    # send the state change email
    comment = _(new_state_data.step.label).lower()
    mail_users = set(user for user in idea.tracked_by if user.uid != from_user.uid)
    for user in mail_users:
        mail_notification.send('mail-event-state-changed.html', to=user, comment=comment, idea=idea,
                               delivery_priority=mail_notification.DeliveryPriority.Low)
