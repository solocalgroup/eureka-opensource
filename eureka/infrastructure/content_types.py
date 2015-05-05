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

# This modules sends custom HTTP responses for specific content types
# For the mime types, see http://www.isi.edu/in-notes/iana/assignments

from webob import exc

from eureka.infrastructure.tools import fix_filename


def view_content_response(content_type, content):
    e = exc.HTTPOk()
    # set response data
    e.content_type = str(content_type)
    e.body = str(content)
    return e


def download_content_response(content_type, content, filename=None):
    e = view_content_response(content_type, content)

    # convert filename if necessary
    if isinstance(filename, unicode):
        filename = fix_filename(filename)

    filename = str(filename)

    # consider the response as an attachment (will be downloaded instead of being displayed in the browser)
    content_disposition = "attachment"

    # add filename info
    if filename is not None:
        content_disposition += ';filename="%s"' % filename
        e.filename = filename

    # add content disposition
    e.headers["Content-Disposition"] = content_disposition
    return e


def excel_response(content, filename=None):
    # /media-types/application/vnd.ms-excel
    return download_content_response('application/vnd.ms-excel', content, filename)
