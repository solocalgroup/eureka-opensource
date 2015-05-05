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


class ColumnDefinition(object):
    _PARSE_FUNCTIONS = dict(
        string='parseString',
        number='parseNumber',
        date='parseDate',
        percentage='parsePercentage'
    )

    def __init__(self, type='string', sortable=True):
        self.type = type
        self.sortable = sortable

    def render_options(self):
        options = {'sortable': 'true' if self.sortable else 'false'}
        if self.type in self._PARSE_FUNCTIONS:
            options['sortOptions'] = '{sortFunction:sortBy(%s)}' % self._PARSE_FUNCTIONS[self.type]
        return ', '.join('%s:%s' % item for item in options.items())


class TableEnhancement(object):
    DEFAULT_WIDTH_CORRECTION = -20  # default 2*10px padding

    def __init__(self, table_id, column_definitions, width_correction=DEFAULT_WIDTH_CORRECTION):
        self.table_id = table_id
        self.column_definitions = column_definitions
        self.width_correction = width_correction
