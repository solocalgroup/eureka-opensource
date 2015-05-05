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

from nagare import presentation, ajax
from nagare.i18n import _
from eureka.ui.common.yui2 import ModalBox, Wait


# modal boxes


@presentation.render_for(ModalBox)
def render_modal_box(self, h, comp, *args):
    # we set display to none to avoid the "flash" appearance of the div before the dialog is rendered
    # display is set back to block at the proper time
    with h.div(id=self._id, class_='modal-box', style='display:none'):
        if self.title:
            with h.div(class_='hd'):
                h << self.title

        with h.div(class_='bd'):
            h << self.inner_comp

    # render the YUI Panel
    js = """
    YAHOO.util.Dom.setStyle(%(id)s, "display", "block");
    var %(var)s = new YAHOO.widget.Panel(%(id)s, {
        width: %(width)s + "px",
        fixedcenter: true,
        modal: true,
        close: %(closable)s,
        visible: %(visible)s,
        draggable: false,
        zIndex: 40
    });
    %(var)s.render(document.body);
    YAHOO.util.Dom.get(%(id)s).panel = %(var)s;  // remember the panel associated to the Dom element
    """ % dict(
        id=ajax.py2js(self._id),
        var=self._id + 'Panel',
        width=ajax.py2js(self.width),
        visible=ajax.py2js(self.visible),
        closable=ajax.py2js(self.closable),
    )

    h << h.script(js, type='text/javascript')

    # forward the answer if necessary
    self.inner_comp.on_answer(comp.answer)

    return h.root


@presentation.render_for(Wait)
def render_wait(self, h, comp, *args):
    # FIXME: remove substituted values from the 'head' code
    load_timeout = 2000
    message = _(u'Loading, please wait...').replace("'", r"\'")

    head_js = ur'''
    function async_loading_init() {
        loading_panel = new YAHOO.widget.Panel("loading-panel", {
            width: "280px",
            fixedcenter: true,
            close: false, draggable: false,
            zindex:40, modal: true, visible: false
        });

        loading_panel.setHeader('%(message)s')
        loading_panel.setBody('<div class="inner-body"/>')
        loading_panel.render(document.body);
        loading_panel.subscribe('show', function(event){YAHOO.util.Dom.setStyle(loading_panel.element, "zIndex", 40)});

        var handleEvents = {
            start: function(eventType, args) {
                this.timer = setTimeout('loading_panel.show()', %(load_timeout)d);
            },
            success: function(eventType, args) {
                clearTimeout(this.timer); loading_panel.hide();
            },
            failure: function(eventType, args) {
                clearTimeout(this.timer); loading_panel.hide();
            },
            upload: function(eventType, args) {
                clearTimeout(this.timer); loading_panel.hide();
            }
        };

        var YUC = YAHOO.util.Connect;
        YUC.startEvent.subscribe(handleEvents.start, handleEvents);
        YUC.successEvent.subscribe(handleEvents.success, handleEvents);
        YUC.failureEvent.subscribe(handleEvents.failure, handleEvents);
        YUC.uploadEvent.subscribe(handleEvents.upload, handleEvents);
        YUC.abortEvent.subscribe(handleEvents.failure, handleEvents);
    }
    ''' % {'load_timeout': load_timeout, 'message': message}

    h << h.head.javascript('async-loading-init', head_js)
    h << h.script('YAHOO.util.Event.onDOMReady(async_loading_init);', type='text/javascript')

    return h.root
