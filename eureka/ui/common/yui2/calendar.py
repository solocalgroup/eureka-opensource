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

from datetime import datetime


# helpers to convert python objects to their javascript counterparts
def js_datetime(value):
    """Convert a python datetime to a javascript one"""
    if value is None:
        return 'null'

    return 'new Date(%d, %d, %d, %d, %d, %d)' % (value.year, value.month - 1, value.day, value.hour, value.minute, value.second)


class Calendar(object):
    """Calendar component that updates a target field (given by its id) when a date is selected"""
    def __init__(self, field_id, field_format='dd/MM/yyyy', title=None, close_button=False, close_on_select=True, on_select='', curdate=None, mindate=None, maxdate=None):
        self.field_id = field_id
        self.field_format = field_format  # in the babel format
        self.title = title
        self.close_button = close_button
        self.close_on_select = close_on_select
        self.on_select = on_select
        self.curdate = curdate or datetime.now()
        self.mindate = mindate
        self.maxdate = maxdate

    @property
    def var(self):
        return 'cal_' + self.field_id

    def show(self):
        return '%(var)s.show();' % dict(var=self.var)

    def hide(self):
        return '%(var)s.hide();' % dict(var=self.var)
