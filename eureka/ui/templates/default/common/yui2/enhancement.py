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


from eureka.ui.common.yui2 import TableEnhancement


@presentation.render_for(TableEnhancement)
def render_table_enhancement(self, h, *args):
    column_defs_code = ',\n'.join(
        ['            {key:"#%s", %s}' % (index, definition.render_options())
         for index, definition in enumerate(self.column_definitions)]
    )

    head_js = """
    function computeWidth(element) {
        var region = YAHOO.util.Dom.getRegion(element)
        return region.right - region.left;
    }

    function parseString(text) {
        return text.replace(/<[^>]+>/, '');  // remove markup
    }

    function parseNumber(text) {
        text = parseString(text);
        return parseFloat(text);
    }

    function parsePercentage(text) {
        text = parseString(text);
        return parseFloat(text.split("%")[0]);
    }

    // TODO: may not work: how do we take the locale into account?
    function parseDate(text) {
        text = parseString(text);
        return YAHOO.util.DataSourceBase.parseDate(text);
    }

    function sortBy(parseFunction) {
        return function(a, b, desc, field) {
            a = parseFunction(a.getData(field));
            b = parseFunction(b.getData(field));
            return YAHOO.util.Sort.compare(a, b, desc);
        };
    }

    function enhanceTable(tableID, columnDefs, widthCorrection) {
        widthCorrection = widthCorrection || -20;  // default 2*10px padding
        table = YAHOO.util.Dom.get(tableID);
        container = table.parentNode;

        // append column labels and widths to the columnDefs from the th elements
        th_elements = table.getElementsByTagName('th');
        th_length = th_elements.length;
        var widths = new Array(th_length);
        for (var i = 0; i < th_length; i++) {
            columnDefs[i]["label"] = th_elements[i].firstChild.data;
            columnDefs[i]["width"] = computeWidth(th_elements[i]) + widthCorrection;
        }

        // make a datasource from the source table
        dataSource = new YAHOO.util.DataSource(table);
        dataSource.responseType = YAHOO.util.DataSource.TYPE_HTMLTABLE;
        dataSource.responseSchema = { fields: columnDefs };

        // create the enhanced datatable that use the datasource
        dataTable = new YAHOO.widget.DataTable(container, columnDefs, dataSource, {});
    }
    """
    h << h.head.javascript('enhance_table', head_js)

    js = u"""
    YAHOO.util.Event.addListener(window, "load", function () {
        var columnDefs = [\n%s
        ];
        enhanceTable("%s", columnDefs, %d);
    });
    """ % (column_defs_code, self.table_id, self.width_correction)
    h << h.script(js, type='text/javascript')

    return h.root
