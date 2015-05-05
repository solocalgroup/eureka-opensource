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

import threading

from nagare import log


_current = threading.local()


def set_manager(manager):
    _current.manager = manager


def get_manager():
    return _current.manager


class Manager(object):
    def __init__(self):
        self.connections = dict()

    def connect(self, listener, sender):
        l = self.connections.get(sender, [])
        l.append(listener)
        self.connections.update({sender: l})

    def get_listeners(self, sender):
        return self.connections.get(sender, [])


def _register_listener(listener, sender):
    get_manager().connect(listener, sender)


def _get_listeners(sender):
    return get_manager().get_listeners(sender)


def _handle_signal(self, sender, signal, *args, **kwds):
    # forwards the signal
    logger = log.get_logger('.' + __name__)
    logger.debug('%s is forwarding the signal %s' % (self, signal))
    _emit_signal(self, signal, *args, **kwds)


def _emit_signal(self, signal, *args, **kwds):
    logger = log.get_logger('.' + __name__)
    logger.debug('%s is sending a signal %s with args=%s and kwargs=%s' % (self, signal, args, kwds))
    listeners = _get_listeners(self)
    if listeners:
        for listener in listeners:
            logger.debug('%s is receiving the signal' % listener)
            _handle_signal(listener, self, signal, *args, **kwds)
    else:
        logger.debug('No listener registered for this sender: %s' % self)
