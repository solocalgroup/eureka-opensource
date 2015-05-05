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

from nagare import security, editor
from nagare.i18n import _, format_date

from eureka.domain.models import ImprovementDomainData, ImprovementData
from eureka.infrastructure import event_management, registry, validators
from eureka.infrastructure.tools import is_integer
from eureka.ui.common.yui2 import flashmessage
from eureka.domain import mail_notification


class SubmitSuggestion(editor.Editor):
    def __init__(self, parent, default_domain=None):
        event_management._register_listener(parent, self)
        self.domain = editor.Property(default_domain)
        self.content = editor.Property('').validate(validators.non_empty_string)

    @property
    def domains(self):
        return ImprovementDomainData.query.order_by(ImprovementDomainData.rank)

    def commit(self):
        current_user = security.get_user()
        assert current_user

        if not super(SubmitSuggestion, self).is_validated(('domain', 'content')):
            return False

        current_user = current_user.entity
        suggestion = self._create_suggestion(current_user, self.domain(), self.content())
        self._send_email(suggestion)

        confirmation_message = _(u'Your suggestion has been sent to the IPS team')
        flashmessage.set_flash(confirmation_message)
        event_management._emit_signal(self, "VIEW_FRONTDESK")
        return True

    def _create_suggestion(self, user, domain, content):
        domain = ImprovementDomainData.get(domain)
        return ImprovementData(user=user,
                               domain=domain,
                               content=content,
                               submission_date=datetime.now())

    def _send_email(self, suggestion):
        user = suggestion.user

        mail_notification.send('mail-suggest.html',
                               to=None,
                               suggestion_label=_(suggestion.domain.label),
                               suggestion_user=user.email,
                               suggestion_user_firstname=user.firstname,
                               suggestion_user_lastname=user.lastname,
                               suggestion_content=suggestion.content,
                               delivery_priority=mail_notification.DeliveryPriority.Low)


class Suggestion(object):
    def __init__(self, suggestion):
        self.id = suggestion if is_integer(suggestion) else suggestion.id

    @property
    def data(self):
        return ImprovementData.get(self.id)

    def toggle_visibility(self):
        self.data.visible = not self.data.visible

    def change_state(self, new_state):
        self.data.state = new_state
