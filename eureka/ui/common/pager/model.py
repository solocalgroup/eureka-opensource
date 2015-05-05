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

class Pager(object):
    """A pager component.

    This is an abstract class that must be implemented
    It can be used to paginate a target object (a list or a table for instance)
    by presenting some data in pages and react to page selection by updating
    the target object.

    It is possible to also invert the control with the target object being
    strongly coupled with the pager and using its result to alter its finding
    methods for instance.

    Its UI can be customized using the following CSS rules:
      - ``ul.pager`` -- its root element
      - ``li.selected`` -- the selected page item
      - ``li.unselected`` -- the unselected page items
      - ``li.disabled`` -- the previous/next items when they can not be used
                           (respectively on the first and last page)

    See:
      - ``DbPager`` -- a pager that can be used in a ``DbTable`` to paginate
                       table data
    """

    def __init__(self, page_size, radius=2):
        """Initializer.

        Parameters:
          - ``page_size`` -- the maximum number of items to display by page
          - ``radius`` -- the minimum number of significant/unellipsized links
                          around the selected page link (defaults: 2)
        """
        super(Pager, self).__init__()

        self.page_size = page_size
        self.radius = radius
        self.start = 0

    def get_page_size(self):
        """Returns the maximum number of items to display by page."""
        return self.page_size

    def paginate(self, target):
        """Method to be implemented by subclasses to paginate a target object.

        Parameters:
          - ``target`` -- the target object to paginate, which can virtually be
                          anything (a list or a database query for instance)

        Raises:
          - ``NotImplementedError`` -- as this is an abstract method
        """
        raise NotImplementedError()

    def _find_items_count(self):
        """Method to be implemented by subclasses to find the total number of
        items of the target object.

        This will be used to know the number of pages to display.

        Raises:
          - ``NotImplementedError`` -- as this is an abstract method
        """
        raise NotImplementedError()

    def find_page_count(self):
        """Returns the number of pages to display."""
        return (self._find_items_count() - 1) // self.page_size + 1

    def get_current_page(self):
        """Returns the currently displayed page index."""
        return self.start / self.page_size

    def go_to_page(self, page_num):
        """Forces the pager to go to the specified page index.

        .. **Warning:** this method does not check if ``page_num`` is inside the
                        ``0..self.find_page_count() - 1`` interval to avoid
                        finding data again, which is potentially slow.

        Anyway, this should only be used by the pager itself.
        """
        self.start = page_num * self.page_size

    def _get_start_index(self, items_count=None):
        # updates the start index if items are removed
        if items_count is None:
            items_count = self._find_items_count()

        if self.start >= items_count:
            last_page_num = (items_count - 1) / self.page_size
            self.go_to_page(last_page_num)

        # returns it
        return self.start
