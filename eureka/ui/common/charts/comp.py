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

from reportlab.graphics import shapes, renderPM
from reportlab.graphics.charts import legends, piecharts, barcharts, linecharts
from reportlab.graphics.widgets import markers
from reportlab.lib import colors
import PIL.Image
import PIL.ImageDraw
import PIL.ImageChops
import threading
import math
import cStringIO as StringIO


class InvalidDataError(Exception):
    """To be raised when the provided data set is not valid to draw chart"""
    pass


class TextImage(object):

    @classmethod
    def get_png(cls, text, width, height):
        size = (width, height)
        img = PIL.Image.new('RGB', size, color='white')
        draw = PIL.ImageDraw.Draw(img)
        black = (0, 0, 0)
        white = (255, 255, 255)
        text_pos = (width / 3, height / 2)
        draw.text(xy=text_pos, text=text, fill=black)

        img_stream = StringIO.StringIO()
        img.save(img_stream, 'PNG')

        return img_stream.getvalue()


def hsl_to_rgb(h, s, l):
    """ Converts HSL colorspace (Hue/Saturation/Value) to RGB colorspace.
        Formula from http://www.easyrgb.com/math.php?MATH=M19#text19

        Input:
            h (float) : Hue (0...1, but can be above or below
                              (This is a rotation around the chromatic circle))
            s (float) : Saturation (0...1)    (0=toward grey, 1=pure color)
            l (float) : Lightness (0...1)     (0=black 0.5=pure color 1=white)

        Ouput:
            (r,g,b) (integers 0...255) : Corresponding RGB values

        Examples:
            >>> print hsl_to_rgb(0.7, 0.7, 0.6)
            (110, 82, 224)
            >>> r, g, b = hsl_to_rgb(0.7, 0.7, 0.6)
            >>> print g
            82
    """

    def hue_2_rgb(v1, v2, vH):
        while vH < 0.0:
            vH += 1.0

        while vH > 1.0:
            vH -= 1.0

        if 6 * vH < 1.0:
            return v1 + (v2 - v1) * 6.0 * vH

        if 2 * vH < 1.0:
            return v2

        if 3 * vH < 2.0:
            return v1 + (v2 - v1) * ((2.0 / 3.0) - vH) * 6.0

        return v1

    if not (0 <= s <= 1):
        raise ValueError("s (saturation) parameter must be between 0 and 1.")
    if not (0 <= l <= 1):
        raise ValueError("l (lightness) parameter must be between 0 and 1.")

    r, b, g = (l * 255,) * 3
    if s != 0.0:
        if l < 0.5:
            var_2 = l * (1.0 + s)
        else:
            var_2 = (l + s) - (s * l)
        var_1 = 2.0 * l - var_2
        r = 255 * hue_2_rgb(var_1, var_2, h + (1.0 / 3.0))
        g = 255 * hue_2_rgb(var_1, var_2, h)
        b = 255 * hue_2_rgb(var_1, var_2, h - (1.0 / 3.0))

    return colors.Color(int(round(r)), int(round(g)), int(round(b)))


def gradient(start_color, nb, end_color=colors.white):
    S = 0.7
    L = 0.65
    step = float(1) / float(nb)
    for i in xrange(nb):
        H = i * step
        yield hsl_to_rgb(H, S, L)


class Drawing(shapes.Drawing, shapes._DrawingEditorMixin):
    pass


class Chart(object):
    lock = threading.Lock()
    DPI = 72 * 1.2

    def __init__(self, labels, data, width, height, **kw):
        self.width = width
        self.height = height
        self._labels = list(labels)
        self._data = list(data)
        self.kw = kw

    def _create_drawing(self):
        drawing = Drawing(self.width, self.height)
        drawing.hAlign = 'CENTRE'
        return drawing

    def __call__(self):
        with self.lock:
            d = self._create_drawing()
            self._render(d)
            return d

    def get_png(self, e=None):
        with self.lock:
            d = self._create_drawing()
            self._render(d)
            rect = shapes.Rect(0, 0, d.width, d.height)
            rect.fillColor = colors.HexColor(0xeeeeee)
            rect.strokeWidth = 0
            d.background = rect
            im = renderPM.drawToPIL(d, dpi=self.DPI)
            bg = PIL.Image.new("RGB", im.size, 0xffffff)
            diff = PIL.ImageChops.difference(im, bg)
            bbox = diff.getbbox()
            if bbox:
                # center bbox
                width = im.size[0]
                minx, miny, maxx, maxy = bbox
                width2 = width / 2
                if width2 - minx < maxx - width2:
                    minx = width - maxx  # width2 - (maxx - width2)
                else:
                    maxx = width - minx  # width2 + (width2 - minx)
                im = im.crop((minx, miny, maxx, maxy))
            imgdata = StringIO.StringIO()
            im.save(imgdata, 'PNG')
            return imgdata.getvalue()


class Pie(Chart):
    def __init__(self, labels, data, width, height, colors=None, with_legend=False, legend_width=None,
                 alternate_values=True, slice_format='%(label)s: %(value)d (%(percentage).1f%%)',
                 legend_format='%(label)s: %(value)d (%(percentage).1f%%)'):
        super(Pie, self).__init__(labels, data, width, height)
        if not any(data):
            raise InvalidDataError(
                "Invalid data for Pie (can't draw chart with: `{}`)".format(data)
            )
        self.colors = colors
        self.with_legend = with_legend
        self.legend_width = legend_width
        self.alternate_values = alternate_values
        self.slice_format = slice_format
        self.legend_format = legend_format

    def _percentage(self, value, total):
        if total == 0:
            return 0
        return value * 100 / float(total)

    def _create_colors(self, color_names):
        colors_by_name = colors.getAllNamedColors()
        return [colors_by_name[name] for name in color_names]

    def _create_gradient(self, colors_count):
        return list(gradient(colors.red, colors_count, colors.blue))

    def _create_labels(self, format, data, labels):
        total = sum(data)
        return [self._create_label(format, value, label, self._percentage(value, total))
                for value, label in zip(data, labels)]

    def _create_label(self, format, value, label, percentage):
        subst = dict(
            label=label,
            value=value,
            percentage=percentage
        )
        return format % subst

    def _create_legend(self, drawing, legend_labels, colors):
        if legend_labels is None:
            return None, None

        legend = legends.LineLegend()
        legend.alignment = 'right'
        legend.dxTextSpace = 5
        legend.columnMaximum = len(legend_labels)
        legend.colorNamePairs = zip(colors, legend_labels)
        legend.fontSize = 12
        legend.deltay = 10

        # compute max width of legend labels
        # legend_width = (max(len(l) for l in legend_labels)+3) * 8
        legend_width = int(legend._calculateMaxBoundaries(legend.colorNamePairs)[1]) + 28
        legend.x = drawing.width - legend_width

        # compute height of legend labels
        # legend_height = legend._calcHeight()
        legend_height = len(legend_labels) * legend.deltay
        legend.y = drawing.height - (drawing.height - legend_height) / 2

        return legend, legend_width

    def _alternate_values(self):
        # This algorithm alternate small and large value slices
        values = sorted(zip(self._data, self._labels), key=lambda (d, l): d)
        alternate = []
        for i in range(len(values)):
            idx = 0 if i % 2 else -1
            value = values.pop(idx)  # take either the first element or the last one
            alternate.append(value)
        # overwrite data & labels
        self._data, self._labels = zip(*alternate)

    def _render(self, drawing):
        if not self._data:
            return

        if self.alternate_values:
            self._alternate_values()

        item_colors = self._create_colors(self.colors) if self.colors else self._create_gradient(len(self._data))

        legend = None
        legend_width = 0
        if self.with_legend:
            legend_labels = self._create_labels(self.legend_format, self._data, self._labels)
            legend, legend_width = self._create_legend(drawing, legend_labels, item_colors)
            drawing.add(legend, 'legend')

        # override legend_width if provided
        if self.legend_width is not None:
            legend_width = self.legend_width

        slice_labels = self._create_labels(self.slice_format, self._data, self._labels)
        gap = 5
        pie = piecharts.Pie3d()
        pie.perspective = 45
        pie.depth_3d = 10
        pie.startAngle = 0
        pie.data = self._data
        pie.labels = slice_labels
        pie.width = drawing.width - legend_width - 5 * gap
        pie.height = int(float(pie.width) * 0.707)
        pie.checkLabelOverlap = True
        pie.x = 3 * gap
        pie.y = (drawing.height - pie.height) / 2  # drawing.height*0.15/2

        pie.slices.setProperties(dict(fontName='Helvetica',
                                      fontSize=10,
                                      labelRadius=0.9,
                                      strokeWidth=1,
                                      strokeColor=colors.white))

        for i, color in enumerate(item_colors):
            pie.slices[i].setProperties(dict(fillColor=color))

        drawing.add(pie)


class BarChart(Chart):
    def _render(self, drawing):
        if not self._labels:
            return

        bc = barcharts.HorizontalBarChart3D()

        labels_factor = 0.015 * max(list(len(l) for l in self._labels))
        width = drawing.width * (0.95 - labels_factor)
        height = drawing.height * 0.85

        bc.setProperties(dict(zDepth=5,
                              width=width,
                              height=height,
                              data=[self._data],
                              y=(drawing.height - height) / 2))

        bc.categoryAxis.categoryNames = self._labels
        bc.categoryAxis.labels.setProperties(dict(fontName='Helvetica',
                                                  fontSize=9,
                                                  textAnchor='end'))
        maximumTicks = 6
        nb_max = max(self._data) or 1
        bc.valueAxis.setProperties(dict(
            visibleGrid=True,
            maximumTicks=maximumTicks,
            valueMin=0,
            valueSteps=range(0, nb_max + 1,
                             int(math.ceil(float(nb_max) / maximumTicks)))))
        bc.valueAxis.labels.setProperties(dict(fontName='Helvetica',
                                               fontSize=9))
        colors_list = list(gradient(colors.red, len(self._data),
                                    colors.orange))
        for i in xrange(len(self._data)):
            bc.bars[i].fillColor = colors_list[i]
            bc.bars[i].strokeWidth = 0

        bc.x = drawing.width * labels_factor

        bc.barLabels.nudge = 10
        bc.barLabelFormat = '%d'
        bc.barLabels.dx = 0
        bc.barLabels.dy = 5
        bc.barLabels.boxAnchor = 'n'
        bc.barLabels.fontName = 'Helvetica'
        bc.barLabels.fontSize = 7

        drawing.add(bc)


class StackedBarChart(Chart):
    def _render(self, drawing):
        if not self._labels:
            return

        bc = barcharts.HorizontalBarChart3D()

        labels_factor = 0.015 * max(list(len(l) for l in self._labels))
        width = drawing.width * (0.95 - labels_factor)
        height = drawing.height * 0.85

        bc.categoryAxis.style = 'stacked'
        bc.categoryAxis.categoryNames = self._labels
        bc.categoryAxis.labels.boxAnchor = 'e'
        bc.categoryAxis.labels.setProperties(dict(fontName='Helvetica',
                                                  fontSize=9,
                                                  textAnchor='end'))
        bc.x = drawing.width * labels_factor
        bc.y = (drawing.height - height) / 2
        bc.height = height
        bc.width = width
        bc.data = self._data
        bc.barWidth = 2

        bc.valueAxis.valueMin = 0
        bc.valueAxis.visibleGrid = True
        bc.valueAxis.maximumTicks = 6
        bc.valueAxis.labels.setProperties(dict(fontName='Helvetica',
                                               fontSize=9))

        colors_list = list(gradient(colors.red, len(self._data),
                                    colors.orange))
        for i in xrange(len(self._data)):
            bc.bars[i].fillColor = colors_list[i]
            bc.bars[i].strokeWidth = 0

        drawing.add(bc)


class MultipleVerticalBarChart(Chart):
    def _render(self, drawing):
        if not self._labels:
            return

        bc = barcharts.VerticalBarChart()
        gap = 5

        if self.kw.get('stacked', False):
            bc.categoryAxis.style = 'stacked'

        legend = None
        legend_height = 0
        if self.kw.get('legendlabels', False):
            legend_height = 40
            colors_list = []
            for i in xrange(len(self._data)):
                colors_list.append(bc.bars[i].fillColor)

            legend = legends.LineLegend()
            legend.alignment = 'right'
            legend.x = 4 * gap
            legend.y = drawing.height - bc.y - gap * 3
            legend.deltay = 5
            legend.dxTextSpace = 5
            legend.columnMaximum = 2
            legend.colorNamePairs = zip(colors_list, self.kw.get('legendlabels'))

        bc.categoryAxis.categoryNames = self._labels
        bc.categoryAxis.labels.boxAnchor = 'e'
        bc.categoryAxis.labels.setProperties(dict(fontName='Helvetica',
                                                  fontSize=9,
                                                  textAnchor='end'))
        bc.categoryAxis.labels.angle = 90

        max_label = max(list(len(l) for l in self._labels))

        bc.x = 4 * gap
        bc.y = max_label * 4
        bc.height = drawing.height - bc.y - gap - legend_height
        bc.width = drawing.width - bc.x - gap
        bc.data = self._data
        bc.barWidth = 2

        bc.valueAxis.valueMin = 0
        bc.valueAxis.visibleGrid = True
        bc.valueAxis.maximumTicks = 12
        bc.valueAxis.labels.setProperties(dict(fontName='Helvetica',
                                               fontSize=9))

        bc.barLabels.nudge = 10
        bc.barLabelFormat = '%d'
        bc.barLabels.dx = 15
        bc.barLabels.dy = -5
        bc.barLabels.boxAnchor = 'c'
        bc.barLabels.fontName = 'Helvetica'
        bc.barLabels.fontSize = 7

        drawing.add(bc)
        if legend:
            drawing.add(legend, 'legend')


class MultipleHorizontalBarChart(Chart):
    def _render(self, drawing):
        if not self._labels:
            return

        bc = barcharts.HorizontalBarChart()
        gap = 5

        if self.kw.get('stacked', False):
            bc.categoryAxis.style = 'stacked'

        legend = None
        legend_height = 0
        if self.kw.get('legendlabels', False):
            legend_height = 30
            colors_list = []
            for i in xrange(len(self._data)):
                colors_list.append(bc.bars[i].fillColor)

            legend = legends.LineLegend()
            legend.alignment = 'right'
            legend.x = 4 * gap
            legend.y = drawing.height - bc.y - gap
            legend.deltay = 60
            legend.dxTextSpace = 5
            legend.columnMaximum = 1
            legend.colorNamePairs = zip(colors_list,
                                        self.kw.get('legendlabels'))

        bc.categoryAxis.categoryNames = self._labels
        bc.categoryAxis.labels.boxAnchor = 'e'
        bc.categoryAxis.labels.setProperties(dict(fontName='Helvetica',
                                                  fontSize=9,
                                                  textAnchor='end'))
        bc.categoryAxis.labels.angle = 90

        max_label = max(list(len(l) for l in self._labels))

        bc.x = 4 * gap
        bc.y = max_label * 5.5
        bc.height = drawing.height - bc.y - gap - legend_height
        bc.width = drawing.width - bc.x - gap
        bc.data = self._data
        bc.barWidth = 5

        bc.valueAxis.valueMin = 0
        bc.valueAxis.visibleGrid = True
        bc.valueAxis.maximumTicks = 12
        bc.valueAxis.labels.setProperties(dict(fontName='Helvetica',
                                               fontSize=9))

        drawing.add(bc)
        if legend:
            drawing.add(legend, 'legend')


class HorizontalLineChart(Chart):
    def _render(self, drawing):
        if not self._labels:
            return

        gap = 5
        lc = linecharts.HorizontalLineChart()
        lc.data = self._data
        lc.lines.symbol = markers.makeMarker('FilledCircle')
        lc.categoryAxis.categoryNames = self._labels
        lc.lineLabelFormat = '%2.0f'

        legend = None
        legend_height = 0
        if self.kw.get('legendlabels', False):
            legend_height = 40
            colors_list = []
            for i in xrange(len(self._data)):
                colors_list.append(lc.lines[i].strokeColor)

            legend = legends.LineLegend()
            legend.alignment = 'right'
            legend.x = 4 * gap
            legend.y = drawing.height - lc.y - gap
            legend.deltay = 60
            legend.dxTextSpace = 5
            legend.columnMaximum = 1
            legend.colorNamePairs = zip(colors_list,
                                        self.kw.get('legendlabels'))

        lc.x = 20
        lc.y = 20
        lc.height = self.height - lc.y - legend_height
        lc.width = self.width - 1.5 * lc.x

        drawing.add(lc)
        if legend:
            drawing.add(legend, 'legend')


class DoubleHorizontalLineChart(Chart):
    def _render(self, drawing):
        if not self._labels:
            return

        gap = 5
        lc1 = linecharts.HorizontalLineChart()
        lc1.data = [self._data[0]]
        lc1.lines.symbol = markers.makeMarker('FilledCircle')
        lc1.categoryAxis.categoryNames = self._labels
        lc1.lineLabelFormat = '%2.0f'

        legend = None
        legend_height = 0
        if self.kw.get('legendlabels', False):
            legend_height = 40
            colors_list = []
            for i in xrange(len(self._data)):
                colors_list.append(lc1.lines[i].strokeColor)

            legend = legends.LineLegend()
            legend.alignment = 'right'
            legend.x = 4 * gap
            legend.y = drawing.height - lc1.y - gap
            legend.deltay = 60
            legend.dxTextSpace = 5
            legend.columnMaximum = 1
            legend.colorNamePairs = zip(colors_list,
                                        self.kw.get('legendlabels'))

        lc1.x = 20
        lc1.y = 20
        lc1.height = self.height - lc1.y - legend_height
        lc1.width = self.width - 1.5 * lc1.x
        lc1.lineLabels.dx = -7
        lc1.lineLabels.fillColor = colors.red

        lc2 = linecharts.HorizontalLineChart()
        lc2.data = [self._data[1]]
        lc2.lines.symbol = markers.makeMarker('FilledCircle')
        lc2.categoryAxis.categoryNames = self._labels
        lc2.lineLabelFormat = '%2.0f'
        lc2.lineLabels.dx = 7
        lc2.lineLabels.fillColor = colors.green
        lc2.valueAxis.strokeColor = colors.green
        # lc2.valueAxis
        lc2.categoryAxis.visible = False

        lc2.x = 20
        lc2.y = 20
        lc2.height = self.height - lc2.y - legend_height
        lc2.width = self.width - 1.5 * lc1.x
        lc2.valueAxis.joinAxisMode = 'right'
        lc2.lines[0].strokeColor = colors.green

        drawing.add(lc1)
        drawing.add(lc2)
        if legend:
            drawing.add(legend, 'legend')


class ColorChooser(Chart):
    def _render(self, drawing):
        gap = 5

        legend = legends.Legend()
        legend.alignment = 'right'
        legend.x = gap
        legend.y = self.height - 3 * gap
        legend.deltay = 5
        legend.dxTextSpace = 5
        legend.fontSize = 14
        legend.columnMaximum = len(colors.getAllNamedColors().keys())
        legend.colorNamePairs = zip(colors.getAllNamedColors().values(),
                                    colors.getAllNamedColors().keys())

        drawing.add(legend, 'legend')
