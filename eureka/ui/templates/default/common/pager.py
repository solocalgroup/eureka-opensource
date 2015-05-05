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

from nagare import presentation
from nagare.i18n import _

from eureka.ui.common.pager import Pager


@presentation.render_for(Pager)
def render(p, r, comp, *args):
    # finds out the currently selected page index and the total page count
    current = p.get_current_page()
    page_count = p.find_page_count()

    if page_count <= 1:
        return r.root

    # finds out the items that are not ellipsizable
    unellipsizable = set(xrange(current - p.radius, current + p.radius + 1))
    unellipsizable.add(0)
    unellipsizable.add(page_count - 1)

    with r.ul(class_='pager'):
        # renders the 'previous' link
        render_page_item(r, _(u'Previous'), current - 1,
                         'disabled' if current == 0 else 'unselected', p)

        last_was_ellipsized = False

        for i in xrange(page_count):
            if i in unellipsizable:
                type = 'selected' if i == current else 'unselected'
                render_page_item(r, unicode(1 + i), i, type, p)
            elif not last_was_ellipsized:
                render_page_item(r, u'\N{HORIZONTAL ELLIPSIS}', None, 'disabled', p)
                last_was_ellipsized = True

        # renders the 'next' link
        render_page_item(r, _(u'Next'), current + 1,
                         'disabled' if current >= page_count - 1
                         else 'unselected', p)

    return r.root


def render_page_item(r, text, page, type, pager):
    if type in ('disabled', 'selected'):
        r << r.li(text, class_=type)
    elif type == 'unselected':
        r << r.li(r.a(text).action(lambda page=page: pager.go_to_page(page)),
                  class_='unselected')
    else:
        raise ValueError('%s: unsupported type' % type)
