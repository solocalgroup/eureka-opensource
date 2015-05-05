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

from nagare import editor


# FIXME: rename this class: this is not necessarily a "bar"
class SearchBar(editor.Editor):

    """An ``Editor`` used to input text to search.

    When not focused, the search bar input text displays a hint to describe
    what would be searched by launching the search.

    Its UI can be customized using the following CSS rules:
      - ``form.search-bar`` -- its root element
      - ``input.query-field`` -- the query text field which has the
                                 the additional ``focused`` class when it has
                                 the focus
      - ``input.search-image`` -- the search image used to trigger the search
     """

    def __init__(self, hint, search_cb):
        """Initializer.

        Parameters:
          - ``hint`` -- the message to display when the text is not focused
          - ``search_cb`` -- the callback to notify when the search must be
                             launched, it is only called when the ``query``
                             property is validated. By default no validation is
                             performed upon this field.

        .. *Note:* the search bar accepts a callback instead of providing a
                   template method by convenience since it is the unique method
                   to implement.
        """
        super(SearchBar, self).__init__(None)

        self.hint = hint
        self.search_cb = search_cb
        self.query = editor.Property(u'')

    def search(self):
        """Called when the search is launched."""
        if super(SearchBar, self).commit((), ('query',)):
            self.search_cb(self.query.value)
