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

import os
import random
import string
import sys
import unittest

import configobj
from eureka.app import BaseApplication
from eureka.domain.models import __metadata__
from eureka.domain.populate import populate
from eureka.infrastructure import registry
from eureka.pkg import resource_filename
from nagare import config, database, i18n, local, security
from nagare.admin.util import read_application_options


def test_resource_path(*path_elements):
    test_dir = resource_filename(os.path.join('eureka', 'tests', 'data'))
    return os.path.join(test_dir, *path_elements)


def random_string(length=10):
    chars = [random.choice(string.ascii_letters) for _ in range(length)]
    return u''.join(chars)


class ConfigurationEnabledTestCase(unittest.TestCase):
    def setUp(self):
        # call the base implementation
        super(ConfigurationEnabledTestCase, self).setUp()

        # configure the local service
        local.request = local.Process()
        local.worker = local.Process()

        # read the configuration
        conf_path = test_resource_path('conf', 'eureka.cfg.template')
        defaults = dict(
            here='string(default="%s")' %
            os.path.abspath(os.path.dirname(conf_path))
        )
        conf = read_application_options(conf_path, self.fail, defaults)

        # initialize the application context
        # no root component since we only want to perform the configuration
        app = BaseApplication(None)
        app.PLATFORM = "Eureka base"
        app.set_config(conf_path, conf, self.fail)
        app.set_base_url('http://localhost/')  # dummy server host
        app.set_locale(i18n.Locale('en', 'US'))  # Set the default Locale

        # install the configuration
        registry.configure(app.configuration)

        # configure the security manager
        security.set_manager(app.security)

    def tearDown(self):
        # clear the configuration
        registry.configure(None)

        # clear the local service
        local.request = None
        local.worker = None

        # call the base implementation
        super(ConfigurationEnabledTestCase, self).tearDown()


class DatabaseEnabledTestCase(ConfigurationEnabledTestCase):
    def __init__(self, methodName='runTest'):
        self.debug = False
        self.database_uri = 'sqlite:///:memory:'
        self.metadata = __metadata__
        self.engine_settings = {}
        super(DatabaseEnabledTestCase, self).__init__(methodName)

    def setUp(self):
        # call the base implementation
        super(DatabaseEnabledTestCase, self).setUp()

        # setup the database
        database.set_metadata(
            self.metadata,
            self.database_uri,
            self.debug,
            self.engine_settings
        )

        self.metadata.create_all()
        sys.argv = [test_resource_path('conf', 'eureka.cfg.template')]
        populate()
        database.session.flush()

    def tearDown(self):
        # clear the database
        database.session.flush()
        self.metadata.drop_all()
        database.session.expunge_all()
        database.session.close()

        # call the base implementation
        super(DatabaseEnabledTestCase, self).tearDown()
