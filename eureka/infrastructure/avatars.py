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
import time
from datetime import datetime

from eureka.infrastructure.filesystem import get_fs_service
from eureka.infrastructure import tools


_ThumbnailsFormats = {
    '30x30': (30, 30),
    '40x40': (40, 40),
    '90x90': (90, 90),
    '100x100': (100, 100)
}


def photo_filename(user_uid, photo_date):
    if not user_uid or not photo_date:
        return 'default.png'

    ts_uid = int(time.mktime(photo_date.timetuple()))
    return user_uid + '-%s.png' % ts_uid


def _photo_path():
    return get_fs_service().expand_path(['profile-photo'])


def _thumbnail_path(format):
    return get_fs_service().expand_path(['profile-thumbnails', format])


def read_photo(uid, photo_date):
    try:
        filename = photo_filename(uid, photo_date)
        path = os.path.join(_photo_path(), filename)
        return tools.read_file(path)
    except IOError:
        return ''


def write_photo(uid, source):
    photo_date = datetime.now()  # we use a timestamp here to avoid browser/http server cache issues
    filename = photo_filename(uid, photo_date)
    path = os.path.join(_photo_path(), filename)

    # writes the profile photo
    tools.write_file(path,
                     tools.create_thumbnail(source, width=124, height=124))

    # writes the thumbnails
    for format, (width, height) in _ThumbnailsFormats.items():
        dir_path = _thumbnail_path(format)
        if not os.path.exists(dir_path):  # if the directory is missing, create it
            os.mkdir(dir_path)
        img_path = os.path.join(dir_path, filename)
        if not os.path.exists(img_path):
            tools.write_file(img_path,
                             tools.create_thumbnail(source, width=width, height=height))

    return photo_date


def remove_photo(uid, photo_date):
    filename = photo_filename(uid, photo_date)
    old_paths = [os.path.join(_photo_path(), filename)]
    old_paths.extend([os.path.join(_thumbnail_path(format), filename) for format in _ThumbnailsFormats.keys()])
    tools.remove_silently(*old_paths)
