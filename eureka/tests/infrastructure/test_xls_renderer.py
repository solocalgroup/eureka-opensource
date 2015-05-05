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

import unittest

from eureka.infrastructure.xls_renderer import XLSRenderer


class XLSRendererMock(XLSRenderer):
    def __init__(self, rows, cols):
        super(XLSRendererMock, self).__init__()
        self.write_operation_index = 1
        self.matrix = []
        for _ in range(rows):
            row = [' ' for _ in range(cols)]
            self.matrix.append(row)

    def add_cell(self, text=None, rowspan=1, colspan=1, **kwargs):
        for row in range(self._row_index, self._row_index + rowspan):
            for col in range(self._col_index, self._col_index + colspan):
                self.matrix[row][col] = str(self.write_operation_index)
        self.write_operation_index += 1
        # call base implementation to trigger the original behavior
        super(XLSRendererMock, self).add_cell(text, rowspan=rowspan, colspan=colspan, **kwargs)

    def render_matrix(self):
        self.get_content()  # triggers the rendering
        return [''.join(row) for row in self.matrix]


class TestXLSRenderer(unittest.TestCase):
    def setUp(self):
        self.renderer = XLSRendererMock(3, 5)
        self.blank = ' ' * 5

    def check_matrix(self, rows, r):
        self.assertEquals(rows, r.render_matrix())

    def test_initial_conditions(self):
        r = self.renderer
        r.add_sheet('Test')  # xlwt library does not want to generate a XLS without a default sheet
        self.check_matrix([self.blank] * 3, r)

    def test_current_row(self):
        r = self.renderer
        self.assertEquals(None, r.current_row)
        r.add_sheet('Test')
        self.assertEquals(None, r.current_row)
        r.add_row()
        self.assertEquals(0, r.current_row)
        r.add_row()
        self.assertEquals(1, r.current_row)

    def test_current_col(self):
        r = self.renderer
        self.assertEquals(0, r.current_col)
        r.add_sheet('Test')
        self.assertEquals(0, r.current_col)
        r.add_row()
        self.assertEquals(0, r.current_col)
        r.add_cell()
        self.assertEquals(1, r.current_col)
        r.add_cell()
        self.assertEquals(2, r.current_col)
        r.add_row()
        self.assertEquals(0, r.current_col)
        r.add_cell()
        self.assertEquals(1, r.current_col)
        r.add_sheet('Test2')
        self.assertEquals(0, r.current_col)

    def test_cell_id(self):
        r = self.renderer
        self.assertEquals('A1', r.cell_id(0, 0))
        self.assertEquals('A2', r.cell_id(1, 0))
        self.assertEquals('Z1', r.cell_id(0, 25))
#        self.assertEquals('AA2', r.cell_id(1, 26))
#        self.assertEquals('BA3', r.cell_id(2, 52))
#        self.assertEquals('ZZ1', r.cell_id(0, 25 + 26*26))
#        self.assertEquals('AAA1', r.cell_id(0, 26 + 26*26))

    def test_single_cell(self):
        r = self.renderer
        r.add_sheet('Test')
        r.add_row()
        r.add_cell('1')
        self.check_matrix(['1    '] + [self.blank] * 2, r)

    def test_range_of_cells(self):
        r = self.renderer
        r.add_sheet('Test')
        r.add_row()
        r.add_cell('1', rowspan=2, colspan=3)
        self.check_matrix(['111  '] * 2 + [self.blank], r)

    def test_single_cell_with_property(self):
        r = self.renderer
        with r.sheet('First sheet'):
            with r.row:
                r << r.cell('Test')
        self.check_matrix(['1    ', self.blank, self.blank], r)

    def test_range_of_cells_with_property(self):
        r = self.renderer
        with r.sheet('First sheet'):
            with r.row:
                r << r.cell('Test', rowspan=2, colspan=4)
        self.check_matrix(['1111 '] * 2 + [self.blank], r)

    def test_single_and_range_of_cells(self):
        r = self.renderer
        with r.sheet('First sheet'):
            with r.row:  # row 1
                r << r.cell('Test')  # col 1
                r << r.cell('Test', rowspan=2, colspan=3)  # col 2-4
        self.check_matrix(['1222 ', ' 222 ', self.blank], r)

    def test_write_pass_over_written_cells(self):
        r = self.renderer
        with r.sheet('First sheet'):
            with r.row:  # row 1
                r << r.cell('Test')  # col 1
                r << r.cell('Test', rowspan=2, colspan=3)  # col 2-4
                r << r.cell('Test')  # col 5
            with r.row:  # row 2
                r << r.cell('Test')  # col 1
                r << r.cell('Test')  # col 5!
        self.check_matrix(['12223', '42225', self.blank], r)

    def test_children_as_constructor_args(self):
        r = self.renderer
        r << r.sheet('Test', [r.row([r.cell('a'), r.cell('b')]), r.row(r.cell('c'))])
        self.check_matrix(['12   ', '3    ', self.blank], r)

    def test_unicode_compatibility(self):
        r = self.renderer
        with r.sheet(u'Mémé'):
            with r.row:
                r << r.cell(u'Mémé')
        self.check_matrix(['1    ', self.blank, self.blank], r)


if __name__ == '__main__':
    unittest.main()
