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

from sqlalchemy.sql.expression import or_

import eureka.ui.common.gallery as gallery
from eureka.domain.models import GalleryImageData, GalleryImageTagData
from eureka.infrastructure.urls import get_url_service
from eureka.infrastructure.filesystem import get_fs_service
from eureka.ui.common.yui2 import RichTextEditorInsertImageCallback


class Gallery(gallery.model.Gallery):
    def __init__(self, editor_id):
        gallery_url = get_url_service().expand_url(['gallery'])
        gallery_dir = get_fs_service().expand_path(['gallery'])

        self.rte_insert_image = RichTextEditorInsertImageCallback(editor_id)
        super(Gallery, self).__init__(gallery_url, gallery_dir, self.rte_insert_image.callback_name)

    def has_same_image(self, data):
        return GalleryImageData.exist(data)

    def add_image(self, image):
        pass

    def delete_image(self, image):
        GalleryImageData.get_by(filename=image.filename).delete()

    def find_images(self, text_filter):
        q = GalleryImageData.query

        if text_filter:
            q = q.join('tags')
            q = q.filter(or_(*(GalleryImageTagData.name.like('%' + t + '%')
                               for t in text_filter.split())))

        return [gallery.model.GalleryImage(i.filename,
                                           i.thumbnail_filename,
                                           i.created_on,
                                           [tag.name for tag in i.tags]) for i in q]
