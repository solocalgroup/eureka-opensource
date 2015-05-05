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

import operator

from nagare import presentation
from nagare.i18n import _

from eureka.ui.common.gallery import Gallery, GalleryUploader


@presentation.render_for(Gallery, model='upload_image')
def render_gallery_upload_image(self, h, comp, *args):
    with h.form(class_='upload-image'):
        h << h.input(type='submit',
                     value=_(u'Add an image'),
                     class_='add-image-btn').action(lambda: self.upload(comp))
    return h.root


@presentation.render_for(Gallery, model='search_image')
def render_gallery_search_bar(self, h, comp, *args):
    # FIXME: refactor this
    h << self.get_search_bar(h)
    return h.root


@presentation.render_for(Gallery)
def render_gallery(self, h, comp, *args):
    with h.div(class_='gallery'):
        with h.div(class_='menu-bar'):
            h << comp.render(h, model='search_image')
            h << comp.render(h, model='upload_image')

        images = self.find_images(self.filter_text)
        images.sort(key=operator.attrgetter('creation_date'), reverse=True)

        if images:
            with h.ul(class_='content'):
                for image in images:
                    tag_names = u', '.join(image.tags)

                    with h.li:
                        # thumbnail / link
                        link = (h.a(h.img(src=self.base_url + '/' + image.thumbnail_filename,
                                          alt=tag_names, title=tag_names,
                                          class_='framed-thumbnail'))
                                 .action(lambda img=image: self.image_selected(img)))

                        if self.selected_js_func:
                            link.set('onclick', '%s("%s");' % (self.selected_js_func, self.base_url + '/' + image.filename))

                        h << link
                        h << h.br()

                        # delete button
                        label = _(u'Delete')
                        h << h.a(label,
                                 title=label,
                                 class_='delete-image').action(lambda img=image: self.confirm_delete(img, comp))
        else:
            h << h.p(
                _(u'No image found.') if self.filter_text
                else _(u'No image in the gallery yet.'))

    return h.root


@presentation.render_for(GalleryUploader)
def render_gallery_uploader(self, h, comp, *args):
    def commit():
        image = self.upload()
        if image:
            comp.answer(image)

    with h.form(id='gallery-upload'):
        with h.div(class_='fields'):
            with h.div(class_='image-field field'):
                h << h.label(_(u'Image:'))
                h << h.input(type='file',
                             class_='file',
                             accept='image/*').action(self.image).error(self.image.error)

            with h.div(class_='tags-field field'):
                h << h.label(_(u'Tags:'))
                h << h.input(type='text',
                             class_='text').action(self.tags).error(self.tags.error)

        with h.div(class_='buttons'):
            h << h.input(type='submit', value=_(u'Upload')).action(commit)
            h << h.input(type='submit', value=_(u'Cancel')).action(lambda: comp.answer(None))

    return h.root
