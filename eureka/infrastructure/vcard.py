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

from base64 import b64encode
from textwrap import wrap

from eureka.infrastructure.tools import create_thumbnail


VCARD_CONTENT_TYPE = 'text/vcard'
VCARD_FILE_EXT = '.vcf'


def _encode_vcard_image(image, size=64):
    """Encode the image the vCard PHOTO format"""
    format = 'image/jpeg'
    image_data = create_thumbnail(image, size, size, format.split('/')[1])
    image_base64 = b64encode(image_data)
    properties = ('ENCODING=BASE64', 'TYPE=%s' % format)
    return image_base64, properties


def generate_vcard(user, uid=None, url=None):
    """Generate a vCard for a given user. uid is a global identifier for the vcard. If
    an URL is specified, it will be included into the vCard"""
    lines = []

    def add(key, value, *properties):
        properties = list(properties)
        try:
            value = value.encode('us-ascii')
        except:
            value = value.encode('utf-8')
            properties.append('ENCODING=8BIT')
            properties.append('CHARSET=UTF-8')
        options_str = (';' + ';'.join(properties)) if properties else ''
        full_line = key + options_str + ':' + value
        wrapped_lines = wrap(full_line, 76)
        for i in range(1, len(wrapped_lines)):
            wrapped_lines[i] = ' ' + wrapped_lines[i]
        lines.extend(wrapped_lines)

    add('BEGIN', 'VCARD')
    add('VERSION', '2.1')
    if uid:
        add('UID', uid)
    add('N', '%s;%s' % (user.lastname, user.firstname))
    add('FN', '%s %s' % (user.firstname, user.lastname))
    add('EMAIL', user.email)
    add('TITLE', user.position)
    org = ';'.join((user.corporation_label, user.direction_label))
    add('ORG', org)
    add('TEL', user.work_phone, 'WORK')
    add('TEL', user.mobile_phone, 'CELL')
    if url:
        add('URL', url)
    if user.photo:
        value, properties = _encode_vcard_image(user.photo, 65)
        add('PHOTO', value, *properties)
    add('END', 'VCARD')

    return '\n'.join(lines)
