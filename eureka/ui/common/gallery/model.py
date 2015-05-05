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
import uuid

from nagare import component, editor
from nagare.i18n import _

from eureka.domain.models import GalleryImageData, GalleryImageTagData
from eureka.ui.common.confirmation import Confirmation
from eureka.ui.common.searchbar import SearchBar
from eureka.infrastructure import validators


# FIXME: should become an image pager, and only that!
class Gallery(object):

    """A gallery component used to select an image using a thumbnail view.

    It supports adding/removing images and also searching by tag using a
    ``SearchBar``.

    The selection callback can be either handled by implementing the
    ``image_selected`` method or by providing the ``selected_js_func`` parameter
    which is the name of the function receiving the selection.

    Its UI can be customized using the following CSS rules:
      - ``div.gallery`` -- its root element
      - ``ul.content`` -- the list containing the selectable thumbnails
      - ``img.framed-thumbnail`` -- the image thumbnail
      - ``img.delete`` -- the delete link icon
      - ``input.add`` -- the submit button to add an image

    See:
      - ``GalleryImage`` -- the abstract image representations wrapped by
                            this gallery
      - ``SearchBar`` -- the search bar used to implement search
    """

    def __init__(self, base_url, base_dir, selected_js_func=None):
        """Initializer.

        Parameters:
          - ``base_url`` -- the base url of the gallery thumbnails
          - ``base_dir`` -- the base directory of the gallery thumbnails
          - ``selected_js_func`` -- the eventual name of the javascript function
                                    too call when an item is selected. It is
                                    called with the thumbnail location.
                                    If not provided, ``image_selected`` must be
                                    implemented (defaults: None)
        """
        super(Gallery, self).__init__()

        self.base_url = base_url
        self.base_dir = base_dir
        self.selected_js_func = selected_js_func

        self.search_bar = component.Component(None)
        self.filter_text = None

    def _set_filter_text(self, text):
        self.filter_text = text

    def get_search_bar(self, r):
        """Returns the lazy-created ``SearchBar``."""
        # FIXME: should not be lazy: the icon should be in the CSS, then no need to reference the renderer
        if not self.search_bar():
            self.search_bar.becomes(SearchBar(_(u'Search an image'),
                                              self._set_filter_text))

        return self.search_bar

    def find_images(self, filter_text):
        """Method to be implemented by subclasses to find the gallery images.

        Parameters:
          - ``filter_text`` -- the filter text which can be ``None`` if no text
                               has been input in the search bar

        Returns: an iterable over the ``GalleryImage`` objects representing
                 the images in the gallery
        """
        raise NotImplementedError()

    def has_same_image(self, image):
        """Can be overwritten by subclasses to check for duplicates.

        It is called when adding an image to avoid adding duplicates in the
        gallery.
        """
        return False

    def add_image(self, image):
        """Method to be implemented by subclasses to add an image in the gallery.

        Parameters:
          - ``image`` -- the ``GalleryImage`` to add
        """
        raise NotImplementedError()

    def delete_image(self, image):
        """Method to be implemented by subclasses to delete an image from the gallery.

        Parameters:
          - ``image`` -- the ``GalleryImage`` to delete
        """
        raise NotImplementedError()

    def image_selected(self, image):
        """Method to be implemented by subclasses to handle image selection
        if not done in Javascript through the ``selected_js_func`` member.

        Parameters:
          - ``image`` -- the ``GalleryImage`` selected

        Raises:
          - ``NotImplementedError`` -- if neither this method is subclassed nor
                                       ``selected_js_func`` is provided
        """
        if not self.selected_js_func:
            raise NotImplementedError("Must be implemented by subclasses if"
                                      "selected_js_func is not used")

    def upload(self, comp):
        """Switch the edition to upload mode using a ``GalleryUploader``."""
        image = comp.call(GalleryUploader(self))
        if image:
            self.add_image(image)

    def confirm_delete(self, image, comp):
        """Confirms the deletion of the specified image."""
        confirm = Confirmation(_(u'This image will be removed from the gallery. You must confirm the removal.'),
                               _(u'Delete'), _(u'Cancel'))

        if comp.call(confirm):
            self.delete_image(image)


class GalleryImage(object):

    """The abstract image representation used in a ``Gallery``."""

    def __init__(self, filename, thumbnail_filename, creation_date, tags):
        """Initializer.

        Parameters:
          - ``filename`` -- the filename of the image in the gallery
          - ``thumbnail_filename`` -- the filename of its thumbnail
          - ``creation_date`` -- the creation date
          - ``tags`` -- the tags associated to this image, which is a list of
                        strings
        """
        super(GalleryImage, self).__init__()

        self.filename = filename
        self.thumbnail_filename = thumbnail_filename
        self.creation_date = creation_date
        self.tags = tags


class GalleryUploader(editor.Editor):

    """An ``Editor`` used to upload a new image in a ``Gallery``."""

    def __init__(self, gallery):
        """Initializer.

        Parameters:
          - ``gallery`` -- the gallery the editor must add the upload result to
        """
        super(GalleryUploader, self).__init__(None)
        self.gallery = gallery
        self.image = editor.Property().validate(self._validate_image)
        self.tags = editor.Property().validate(validators.word_list)

    def upload(self):
        """Validates, uploads and adds the image to the gallery."""
        if not super(GalleryUploader, self).commit((), ('image', 'tags')):
            return None

        # get the image information
        filename = self.image.value['filename']
        data = self.image.value['data']
        tags = self.tags.value

        # creates the image
        image = GalleryImageData(filename, data)
        image.tags = [GalleryImageTagData.get_by(name=tag) or GalleryImageTagData(name=tag) for tag in tags]

        # returns the image
        return GalleryImage(image.filename,
                            image.thumbnail_filename,
                            image.created_on,
                            image.tags)

    def _validate_image(self, f):
        file = validators.validate_file(f)
        if file is None:
            raise ValueError(_(u"Can't be empty"))

        filename = file['filename']
        data = file['filedata']

        extension = os.path.splitext(filename)[1].lower()
        prefix = uuid.uuid4().hex
        filename = prefix + extension

        # checks the image is not already in the gallery
        if GalleryImageData.exist(data):
            raise ValueError(_(u'Image already in gallery'))

        return dict(filename=filename, data=data)
