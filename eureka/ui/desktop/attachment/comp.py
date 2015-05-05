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

from eureka.domain.models import AttachmentData, attachments_max_size
from eureka.infrastructure.urls import get_url_service
from eureka.infrastructure.content_types import download_content_response
from eureka.infrastructure.validators import validate_file
from eureka.infrastructure.tools import is_integer


class Attachment(object):
    def __init__(self, attachment):
        self.id = attachment if is_integer(attachment) else attachment.id

    @property
    def attachment(self):
        return AttachmentData.get(self.id)

    @property
    def url(self):
        return get_url_service().expand_url(['attachments', self.attachment.filepath])

    def download(self):
        raise download_content_response(self.attachment.mimetype,
                                        self.attachment.data,
                                        self.attachment.filename)


def validate_attachment(attachment):
    return validate_file(attachment, attachments_max_size())
