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

from cStringIO import StringIO

import xlwt

from eureka.infrastructure.tools import Enum
import string


class _Element(object):
    def __init__(self, children=None):
        if children is None:
            self.children = []
        elif hasattr(children, '__iter__'):
            self.children = list(children)
        else:
            self.children = [children]

    def __enter__(self):
        self.renderer._enter(self)
        return self

    def __exit__(self, exception, value, traceback):
        self.renderer._exit()
        return False

    def render(self, renderer):
        for child in self.children:
            child.render(renderer)


class _Sheet(_Element):
    def __init__(self, name, children=None):
        self.name = name
        super(_Sheet, self).__init__(children)

    def render(self, renderer):
        renderer.add_sheet(self.name)
        super(_Sheet, self).render(renderer)


class _Row(_Element):
    def __init__(self, children=None, height=None, style=None):
        super(_Row, self).__init__(children)
        self.height = height
        self.style = style

    def render(self, renderer):
        renderer.add_row(height=self.height, style=self.style)
        super(_Row, self).render(renderer)


class _Cell(_Element):
    def __init__(self, children=None, rowspan=1, colspan=1, width=None, style=None, format=None):
        super(_Cell, self).__init__(children)
        self.rowspan = rowspan
        self.colspan = colspan
        self.width = width
        self.style = style
        self.format = format

    def render(self, renderer):
        text = None
        if len(self.children) > 1:
            text = ''.join(map(unicode, self.children))
        elif len(self.children) == 1:
            text = self.children[0]
        renderer.add_cell(text, rowspan=self.rowspan, colspan=self.colspan, width=self.width, style=self.style, format=self.format)


class _Property(object):
    def __init__(self, element_factory):
        self.factory = element_factory

    def __get__(self, renderer, type=None):
        if type is None:
            raise AttributeError()
        self.renderer = renderer
        return self

    def __call__(self, *args, **kwargs):
        element = self.factory(*args, **kwargs)
        element.renderer = self.renderer
        return element

    def __enter__(self):
        element = self.factory()
        self.renderer._enter(element)

    def __exit__(self, exception, value, traceback):
        self.renderer._exit()
        return False

    def __repr__(self):
        return 'ExcelProperty(%r)' % self.factory


class XLSRenderer(object):
    """
    Implements an Excel Renderer.

    Usage example:
    >>> from eureka.infrastructure.xls_renderer import XLSRenderer
    >>> r = XLSRenderer()
    >>> with r.sheet('My sheet'):  #doctest: +ELLIPSIS
    ...     with r.row(style=r.Background.Yellow+r.Style.Bold):
    ...         r << r.cell('first line')
    ...         r << r.cell('text that spans 3 columns', colspan=3)
    ...     with r.row:
    ...         r << r.cell('second line', style=r.Border.All)
    ...         r << r.cell('example')
    ...         r << r.cell('another example')
    ...
    <eureka.infrastructure.xls_renderer.XLSRenderer object at 0x...>
    >>> xls_content = r.get_content()
    """
    # See xlwt.Style for constants
    # Sizes: multiply the value that appears in excel/openoffice (number of pt) by 20 to obtain the value to set
    class Style(Enum):
        VerticalAlignTop = 'alignment: vertical top;'
        VerticalAlignCenter = 'alignment: vertical center;'
        Wrap = 'alignment: wrap yes;'
        Bold = 'font: bold yes;'
        Centered = 'alignment: horizontal center;'
        _FontHeight = 'font: height %s;'
        Text = _FontHeight % 200  # size 10
        _HeadingBase = Bold + Centered
        Heading1 = (_FontHeight % 400) + _HeadingBase  # size 20
        Heading2 = (_FontHeight % 320) + _HeadingBase  # size 16
        Heading3 = (_FontHeight % 240) + _HeadingBase  # size 12
        ColumnHeading = Text + _HeadingBase

    class Format(Enum):
        Date = 'dd/mm/yyyy'  # FIXME: locale specific format?
        Percentage = '0.00 %'

    class Background(Enum):
        _BackgroundFormat = 'pattern: pattern solid, fore-color %s;'

        Black = _BackgroundFormat % 'black'
        White = _BackgroundFormat % 'white'

        Red = _BackgroundFormat % 'red'
        Green = _BackgroundFormat % 'green'
        Blue = _BackgroundFormat % 'blue'

        Yellow = _BackgroundFormat % 'yellow'
        Magenta = _BackgroundFormat % 'pink'
        Cyan = _BackgroundFormat % 'turquoise'

        Orange = _BackgroundFormat % 'orange'
        LightBlue = _BackgroundFormat % 'light_blue'
        LightGreen = _BackgroundFormat % 'light_green'
        LightOrange = _BackgroundFormat % 'light_orange'
        LightYellow = _BackgroundFormat % 'light_yellow'
        Tan = _BackgroundFormat % 'tan'

        PaleBlue = _BackgroundFormat % 'pale_blue'
        Rose = _BackgroundFormat % 'rose'

        Grey25 = _BackgroundFormat % 'grey25'
        Grey40 = _BackgroundFormat % 'grey40'
        Grey50 = _BackgroundFormat % 'grey50'
        Grey80 = _BackgroundFormat % 'grey80'

        LightTurquoise = _BackgroundFormat % 'light_turquoise'

    class Border(Enum):
        _ThinFormat = 'border: %s thin;'
        _MediumFormat = 'border: %s medium;'

        # thin
        Top = _ThinFormat % 'top'
        Left = _ThinFormat % 'left'
        Right = _ThinFormat % 'right'
        Bottom = _ThinFormat % 'bottom'
        All = Top + Left + Right + Bottom

        # medium
        TopMedium = _MediumFormat % 'top'
        LeftMedium = _MediumFormat % 'left'
        RightMedium = _MediumFormat % 'right'
        BottomMedium = _MediumFormat % 'bottom'
        AllMedium = TopMedium + LeftMedium + RightMedium + BottomMedium

    sheet = _Property(_Sheet)
    row = _Property(_Row)
    cell = _Property(_Cell)
    formula = xlwt.Formula  # alias

    def __init__(self, encoding='utf-8'):
        self._workbook = xlwt.Workbook(encoding=encoding)
        self._worksheet = None
        self._row_index = -1
        self._col_index = 0
        self._styles_lut = {}  # we remember the styles created previously for reuse since their number is limited

    @property
    def current_row(self):
        return self._row_index if self._row_index > -1 else None

    @property
    def current_col(self):
        return self._col_index

    def _col_name(self, col):
        # repeatedly divide col value by 26 to obtain the digits
        if col >= 26:
            raise NotImplementedError()

        return string.ascii_uppercase[col]

    def cell_id(self, row, col):
        return '%s%d' % (self._col_name(col), row + 1)  # excel starts counting at 1

    def cell_range_id(self, row1, col1, row2, col2):
        return self.cell_id(row1, col1) + ':' + self.cell_id(row2, col2)

    @property
    def current_cell_id(self):
        return self.cell_id(self.current_row, self.current_col)

    def __lshift__(self, child):
        child.render(self)
        return self  # so that we can cascade << calls

    def add_sheet(self, name):
        self._worksheet = self._workbook.add_sheet(name)
        self._marked_cells = set()
        self._row_index = -1
        self._col_index = 0

    def add_row(self, height=None, style=None):
        self._row_index += 1
        self._col_index = 0
        self._move_to_next_unmarked_cell()
        row = self._worksheet.row(self._row_index)
        if height:
            row.height = height * 20
            row.height_mismatch = True
        if style:
            style = self._create_style(style)
            row.set_style(style)

    def add_cell(self, text=None, rowspan=1, colspan=1, width=None, style=None, format=None):
        style = self._create_style(style, format)
        if colspan > 1 or rowspan > 1:
            self._worksheet.write_merge(self._row_index,
                                        self._row_index + rowspan - 1,
                                        self._col_index,
                                        self._col_index + colspan - 1,
                                        text,
                                        style)
        else:
            self._worksheet.write(self._row_index,
                                  self._col_index,
                                  text,
                                  style)

        if width:
            self._worksheet.col(self._col_index).width = width * 20

        # mark the written cells
        self._mark_cells(self._row_index, rowspan, self._col_index, colspan)
        # move to the next unmarked cell
        self._move_to_next_unmarked_cell()

    def save(self, stream_or_filename):
        """
        Write the workbook content to a stream/file
        """
        self._workbook.save(stream_or_filename)

    def get_content(self):
        """
        Get the workbook content
        """
        stream = StringIO()
        self.save(stream)
        content = stream.getvalue()
        stream.close()
        return content

    def _create_style(self, style=None, format=None):
        if style is None and format is None:
            return xlwt.Style.default_style

        if style is None:
            style = []
        elif not hasattr(style, '__iter__'):
            style = [style]
        style_str = ''.join(style)
        return self._styles_lut.setdefault((style_str, format), xlwt.easyxf(style_str, num_format_str=format))

    def _mark_cells(self, row, rowspan, col, colspan):
        for r in range(row, row + rowspan):
            for c in range(col, col + colspan):
                self._marked_cells.add((r, c))

    def _move_to_next_unmarked_cell(self):
        while (self._row_index, self._col_index) in self._marked_cells:
            self._col_index += 1

    def _enter(self, element):
        self << element

    def _exit(self):
        pass
