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

from eureka.ui.common.htmlcharts import BarChart


@presentation.render_for(BarChart)
def render_chart(self, h, comp, *args):
    with h.div(class_='chart'):
        with h.h3:
            h << h.i(class_='icon-chart')
            h << self.title

        with h.ul:
            total = sum(value for label, value in self.items)
            for label, value in self.items:
                if total:
                    px = value * 40 / total
                else:
                    px = 0
                with h.li:
                    with h.div(class_='bar'):
                        h << h.div(class_='top',
                                   style='bottom:%dpx' % px)
                        h << h.div(class_='value',
                                   style='height:%dpx' % px)
                        h << h.div(class_='bottom')
                    if self.clickable:
                        h << h.span(h.a(value).action(lambda label=label: comp.answer(label)))
                    else:
                        h << h.span(value)
                    h << h.small(_(label))
    return h.root
