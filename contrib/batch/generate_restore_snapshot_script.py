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
import eureka
import sys
from eureka.infrastructure import filesystem


def generate_restore_backup_script():
    """Generates an Apache HTTPD Configuration snippet for your Eureka

    In:
      - ``parser`` -- the optparse.OptParser object used
            to parse the configuration file
      - ``options`` -- options in the command lines
      - ``args`` -- arguments in the command lines
    """

    eureka_egg_dir = os.path.dirname(os.path.dirname(eureka.__file__))
    app_dir = os.path.dirname(os.path.dirname(sys.executable))
    data_dir = filesystem.get_fs_service().data_dir

    with open(os.path.join(eureka_egg_dir, "contrib", "demo", "restore_snapshot.sh.in")) as template_file:
        template = template_file.read()
        script = template.format(app_dir=app_dir,
                                 data_dir=data_dir,
                                 backup_file=os.path.join(app_dir, 'dumps', 'demo.archive.tgz'),
                                 name='eureka')
    return script

fs = filesystem.get_fs_service()
# configure the batch environment
print(generate_restore_backup_script())
