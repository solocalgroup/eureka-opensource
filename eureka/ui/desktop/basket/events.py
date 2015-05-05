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

import peak.rules

from nagare import security

from .comp import IdeaBasket  # @UnusedImport - needed for peak rules
from eureka.domain.queries import get_all_user_ideas_with_state
from eureka.domain.queries import get_fi_ideas_with_state
from eureka.domain.queries import get_di_ideas_with_state
from eureka.domain.queries import get_dsig_ideas_with_state
from eureka.infrastructure import event_management


@peak.rules.when(event_management._handle_signal,
                 "isinstance(self, IdeaBasket) and "
                 "signal == 'VIEW_MY_IDEAS' and "
                 "kwds.get('state')")
def _handle_signal_view_my_ideas(self, sender, signal, *args, **kwds):
    user_uid = security.get_user().uid
    self.show_ideas(user_uid, kwds.get('state'), get_all_user_ideas_with_state)


@peak.rules.when(event_management._handle_signal,
                 "isinstance(self, IdeaBasket) and "
                 "signal == 'VIEW_FI_IDEAS' and "
                 "kwds.get('state')")
def _handle_signal_view_fi_ideas(self, sender, signal, *args, **kwds):
    user_uid = security.get_user().uid
    self.show_ideas(user_uid, kwds.get('state'), get_fi_ideas_with_state)


@peak.rules.when(event_management._handle_signal,
                 "isinstance(self, IdeaBasket) and "
                 "signal == 'VIEW_FI_DSIG_IDEAS' and "
                 "kwds.get('state') and "
                 "kwds.get('user_uid')")
def _handle_signal_view_fi_dsig_ideas(self, sender, signal, *args, **kwds):
    user_uid = kwds.get('user_uid')
    self.show_ideas(user_uid, kwds.get('state'), get_fi_ideas_with_state)


@peak.rules.when(event_management._handle_signal,
                 "isinstance(self, IdeaBasket) and "
                 "signal == 'VIEW_DI_IDEAS' and "
                 "kwds.get('state')")
def _handle_signal_view_di_ideas(self, sender, signal, *args, **kwds):
    user_uid = security.get_user().uid
    self.show_ideas(user_uid, kwds.get('state'), get_di_ideas_with_state)


@peak.rules.when(event_management._handle_signal,
                 "isinstance(self, IdeaBasket) and "
                 "signal == 'VIEW_DI_DSIG_IDEAS' and "
                 "kwds.get('state') and "
                 "kwds.get('user_uid')")
def _handle_signal_view_di_dsig_ideas(self, sender, signal, *args, **kwds):
    user_uid = kwds.get('user_uid')
    self.show_ideas(user_uid, kwds.get('state'), get_di_ideas_with_state)


@peak.rules.when(event_management._handle_signal,
                 "isinstance(self, IdeaBasket) and "
                 "signal == 'VIEW_DSIG_IDEAS' and "
                 "kwds.get('state')")
def _handle_signal_view_dsig_ideas(self, sender, signal, *args, **kwds):
    user_uid = security.get_user().uid
    self.show_ideas(user_uid, kwds.get('state'), get_dsig_ideas_with_state)


@peak.rules.when(event_management._handle_signal,
                 "isinstance(self, IdeaBasket) and "
                 "signal == 'HIDE_IDEAS'")
def _handle_signal_hide_ideas(self, sender, signal, *args, **kwds):
    self.hide_ideas()
