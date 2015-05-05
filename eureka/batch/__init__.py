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

import sys
from nagare import security, local, log, i18n
from eureka.infrastructure import registry


def configure():
    """Configure the batch environment"""

    global apps
    # we suppose that the batch addresses only one application
    app_name, app = apps.items()[0]

    local.request = local.Process()
    local.worker = local.Process()

    log.set_logger('nagare.application.' + app.name)

    security.set_manager(app.security)

    # initialize the application context
    app.set_base_url('http://localhost/')  # dummy server host
    app.set_locale(i18n.Locale('en', 'US'))  # Set the default Locale

    # install the configuration
    registry.configure(app.configuration)

    # log the start of the script
    logger = log.get_logger('.' + __name__)
    logger.debug('----')
    logger.debug('Running %s\n' % sys.argv[0])
