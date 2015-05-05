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

from nagare import security, var
from nagare.i18n import _

from eureka.ui.common.yui2 import flashmessage


class LoginEvent(object):
    """Answer returned when a user logged in successfully"""


class LogoutEvent(object):
    """Answer returned when a user click on the logout button"""


class CancelLoginEvent(object):
    """Answer returned when a user click on the cancel button"""


class Login(object):

    def __init__(self):
        self.form_opened = var.Var(False)

    def commit(self):
        if not security.get_user():
            flashmessage.set_flash(_(u"Wrong login or password"))
            return False

        # display a message if the user has missed events in the last month
        user = security.get_user().entity
        one_month_ago = user.last_connection_date - timedelta(days=30)
        if any(user.unread_events(one_month_ago)):
            flashmessage.set_flash(_(u"You have new events to browse"))

        return True
