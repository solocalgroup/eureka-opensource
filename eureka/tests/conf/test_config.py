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
from optparse import OptionParser
from unittest import TestCase

from configobj import ConfigObj
from eureka.app import BaseApplication
from eureka.ui.desktop.shell import Shell
from mock import Mock
from nagare.admin.serve import publisher_options_spec
from nagare.admin.util import read_application


class ConfigError(Exception):
    pass


def config_error(msg):
    raise ConfigError(msg)


class TestConfigValidation(TestCase):

    def _get_filepath(self, filename):
        cur_dir = os.path.dirname(__file__)
        return os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'data', filename)

    def _load_config(self, filepath):
        _, app, _, conf = read_application(filepath, config_error)
        spec = ConfigObj({'DEFAULT': {'name': 'eureka'}})
        conf = ConfigObj(
            filepath,
            configspec=publisher_options_spec,
            interpolation='Template'
        )
        conf.merge(spec)
        return conf

    def test_validate_valid_config(self):
        config_filepath = self._get_filepath('valid_config.conf')
        conf = self._load_config(config_filepath)
        test_app = BaseApplication(Shell)
        result = test_app._validate_config(conf, config_filepath, config_error)
        self.assertTrue(result)

    def test_validate_invalid_chart_config(self):
        config_filepath = self._get_filepath('invalid_chart_config.conf')
        conf = self._load_config(config_filepath)
        test_app = BaseApplication(Shell)
        with self.assertRaises(ConfigError):
            test_app._validate_config(conf, config_filepath, config_error)
