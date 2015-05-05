/**
 * Copyright Solocal Group (2015)
 *
 * eureka@solocal.com
 *
 * This software is a computer program whose purpose is to provide a full
 * featured participative innovation solution within your organization.
 *
 * This software is governed by the CeCILL license under French law and
 * abiding by the rules of distribution of free software.  You can  use,
 * modify and/ or redistribute the software under the terms of the CeCILL
 * license as circulated by CEA, CNRS and INRIA at the following URL
 * "http://www.cecill.info".
 *
 * As a counterpart to the access to the source code and  rights to copy,
 * modify and redistribute granted by the license, users are provided only
 * with a limited warranty  and the software's author,  the holder of the
 * economic rights,  and the successive licensors  have only  limited
 * liability.
 *
 * In this respect, the user's attention is drawn to the risks associated
 * with loading,  using,  modifying and/or developing or reproducing the
 * software by the user in light of its specific status of free software,
 * that may mean  that it is complicated to manipulate,  and  that  also
 * therefore means  that it is reserved for developers  and  experienced
 * professionals having in-depth computer knowledge. Users are therefore
 * encouraged to load and test the software's suitability as regards their
 * requirements in conditions enabling the security of their systems and/or
 * data to be ensured and,  more generally, to use and operate it in the
 * same conditions as regards security.
 *
 * The fact that you are presently reading this means that you have had
 * knowledge of the CeCILL license and that you accept its terms.
 */

/**
 * JS code specific to the desktop version of Eurêka
 */

/* -- Expand/collapse toggle -- */
function isCollapsible(element) {
    return YAHOO.util.Dom.hasClass(element, 'expand') || YAHOO.util.Dom.hasClass(element, 'collapse');
}

function toggleCollapseExpand(element) {
    // find the nearest collapsible/expandable element
    var collapsible = null;
    if (isCollapsible(element))
        collapsible = element;
    else
        collapsible = YAHOO.util.Dom.getAncestorBy(element, isCollapsible);

    // toggle collapse/expand
    if (YAHOO.util.Dom.hasClass(collapsible, 'expand'))
        YAHOO.util.Dom.replaceClass(collapsible, 'expand', 'collapse');
    else
        YAHOO.util.Dom.replaceClass(collapsible, 'collapse', 'expand');
}

/* Format a date according to a format string in the babel format */
function formatDate(date, format) {
    var day = date.getDate();
    var month = date.getMonth() + 1;
    var year = date.getFullYear();
    var day2 = (day < 10 ? '0' : '') + day;
    var month2 = (month < 10 ? '0' : '') + month;
    var year2 = ("" + year).substring(2,4);
    return format.replace('dd', day2)
                 .replace('d', day)
                 .replace('MM', month2)
                 .replace('M', month)
                 .replace('yyyy', year)
                 .replace('yy', year2);
}

var slider_timer = null;

function initAutoPlay() {
    function autoPlay(el) {
        var link = YAHOO.util.Dom.getElementsByClassName('current', 'li', el)[0];

        /* find next link */
        var next = YAHOO.util.Dom.getNextSibling(link);

        if (next !== null){
            link = YAHOO.util.Dom.getFirstChild(next);
        }
        else {
            /* no more links use first link */
            link = el.getElementsByTagName('li')[0];
            link = YAHOO.util.Dom.getFirstChild(link);
        }

        if (typeof link.onclick == "function") {
            link.onclick.apply(link);
        }
    }

    if (slider_timer) {
        clearTimeout(slider_timer);
    }

    slider_timer = setTimeout(function() {
        var el = YAHOO.util.Dom.getElementsByClassName('slider')[0];
        autoPlay(el);
    }, 20000);
}

/* Scroll to the first field in error in the page */
function scrollToFirstErrorField() {
    YAHOO.util.Event.onDOMReady(function(){
        console.log('Here I am');
        setTimeout(function() {
            var el = YAHOO.util.Dom.getElementsByClassName('nagare-error-field')[0];
            if (el) {
                el.scrollIntoView(true);
            }
        }, 0);
    });
}

function manage_menu_click(action){
    YUI().use('node', function (Y) {
        var menu_node = Y.one('#menu_popin');
        var html_node = Y.one('html');
        menu_node.ancestor().ancestor().on('click', function(event){html_node.detach('click');event.stopPropagation();});
        var sub = html_node.on('click', function(){html_node.detach('click');action();})
    });
}
