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

from nagare import component

from eureka.ui.desktop.portal import Portal
from eureka.ui.common.yui2 import FlashHandler, flashmessage
from eureka.infrastructure import event_management, registry

from eureka.infrastructure.urls import get_url_service


class Shell(object):
    def __init__(self, configuration):
        self.configuration = configuration

        # create the singleton services for this session
        self.event_manager = event_management.Manager()
        self.flash_handler = FlashHandler()

        # install the singleton services in the current thread since the
        # portal component need them to initialize itself
        self._install_singleton_services()

        # the default content is the portal
        self.content = component.Component(Portal(self.configuration))

    def _install_singleton_services(self):
        registry.configure(self.configuration)
        event_management.set_manager(self.event_manager)
        flashmessage.set_handler(self.flash_handler)

    def on_start_request(self, root, request, response):
        """Install the singleton services"""
        self._install_singleton_services()
