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

from nagare import presentation, var
from nagare.i18n import _
from eureka.ui.common.yui2 import Autocomplete


@presentation.render_for(Autocomplete)
def render(self, h, comp, *args):
    # register a callback and get its url
    callback = h.register_callback(1, self.value, False, self.hello)
    url = h.add_sessionid_in_url(h.request.path, params=(callback,))

    js = r'''
YAHOO.example.BasicRemote = function() {
    var oDS = new YAHOO.util.XHRDataSource("%(url)s");
    oDS.responseType = YAHOO.util.XHRDataSource.TYPE_TEXT;

    oDS.responseSchema = {
        recordDelim: "\n",
        fieldDelim: "\t"
    };

    oDS.maxCacheEntries = 5;

    var oAC = new YAHOO.widget.AutoComplete("%(autocomplete_search)s",
                                            "%(autocomplete_container)s", oDS);
    oAC.queryDelay = %(query_delay)f;
    oAC.queryQuestionMark = false;
    oAC.delimChar = "%(delim_char)s";
    oAC.minQueryLength = %(min_query_length)d;
    oAC.maxResultsDisplayed = %(max_results_displayed)d;

    oAC.formatResult = function(oResultData, sQuery, sResultMatch) {
        lc = sQuery.toLowerCase();
        uc = sQuery.toUpperCase();

        return sResultMatch.split(lc).join('<strong>' +
               lc + '</strong>').split(uc).join('<strong>' +
               uc + '</strong>') + ' ('+ oResultData[1] +')';

    };

    oAC.generateRequest = function(sQuery) {
        return "=" + sQuery +"&_a" ;
    };

    oAC.doBeforeExpandContainer = function(elTextbox, elContainer, sQuery, aResults) {
        if (aResults.length >= this.maxResultsDisplayed){
            this.setHeader("%(too_many_results)s");
        }else{
            this.setHeader('');
        }
        return true;
    };

    return {
        oDS: oDS,
        oAC: oAC
    };
}();
    '''

    autocomplete_search = self.id or h.generate_id(prefix='autocomplete_search')
    autocomplete_container = h.generate_id(prefix='autocomplete_container')
    with h.div(class_=" ".join(("autocomplete", self.ac_class))):
        h << h.input(id=autocomplete_search, **self.input_params).action(self._action).error(self._error)
        h << h.div(id=autocomplete_container)

        mapping = {'url': url,
                   'autocomplete_search': autocomplete_search,
                   'autocomplete_container': autocomplete_container,
                   'query_delay': self.query_delay,
                   'delim_char': self.delim_char,
                   'min_query_length': self.min_query_length,
                   'max_results_displayed': self.max_results_displayed,
                   'too_many_results': _(u"Too many results, please precise your query")}

        h << h.script(js % mapping)

    return h.root
