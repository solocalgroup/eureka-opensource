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

from eureka.ui.common.searchbar import SearchBar
import json


@presentation.render_for(SearchBar)
def render(self, h, comp, *args):
    # escapes the hint text out
    js_hint = json.dumps(self.hint)
    onsubmit_js = """
    f = YAHOO.util.Dom.getElementsByClassName("query-field", "INPUT", this)[0];
    f.value = f.value.replace("%s", "");
    """ % js_hint

    with h.form(class_='search-bar', onsubmit=onsubmit_js):
        # updates the query value with the hint
        self.query(self.hint)

        # query field
        onfocus_js = """
        if (this.value == %s) {
            this.value="";
            YAHOO.util.Dom.addClass(this, "focused");
        }
        """ % js_hint
        onblur_js = """
        if (this.value == "") {
            this.value=%s;
            YAHOO.util.Dom.removeClass(this, "focused");
       }
       """ % js_hint

        h << h.input(type='text',
                     class_='text query-field',
                     value=self.query(),
                     onfocus=onfocus_js,
                     onblur=onblur_js).action(self.query)

        # search button
        label = _(u'Search')
        h << h.input(value=label,
                     title=label,
                     class_='confirm-button',
                     type='submit').action(self.search)

    return h.root
