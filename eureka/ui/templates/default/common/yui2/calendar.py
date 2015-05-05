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
import json

from nagare import presentation
from nagare.i18n import _, get_day_names, get_month_names
from eureka.ui.common.yui2 import Calendar, js_datetime


@presentation.render_for(Calendar)
def render(self, h, comp, *args):
    # id used for this calendar component
    container_id = h.generate_id('calendar-')

    # container for the date picker table
    h << h.div(id=container_id, class_='calendar')

    # javascript code
    # hack for an IE javascript bug: declare a global variable in the head
    h << h.head.javascript('%s-var' % self.var,
                           "var %s = null;" % self.var)

    days_order = (6, 0, 1, 2, 3, 4, 5)
    weekdays_1char = [get_day_names('narrow')[i].title() for i in days_order]
    weekdays_short = [get_day_names('abbreviated')[i][:2].title() for i in days_order]
    weekdays_medium = [get_day_names('abbreviated')[i].title() for i in days_order]
    weekdays_long = [get_day_names('wide')[i].title() for i in days_order]
    months_order = range(1, 13)
    months_short = [get_month_names('abbreviated')[i].title() for i in months_order]
    months_long = [get_month_names('wide')[i].title() for i in months_order]

    js = u"""
    // WARNING: we should never try to parse a date string because it's format depend on the locale!
    // calendar
    %(var)s = new YAHOO.widget.Calendar("%(container_id)s", {
        title:%(title)s,
        mindate:%(mindate)s,
        maxdate:%(maxdate)s,
        start_weekday:1,
        locale_weekdays:"short",
        close:%(close_button)s }
    );

    // the "selected" config property does not accept Date objects, so we call the "select" function instead
    %(var)s.select(%(curdate)s);

    // date labels for the calendar display
    %(var)s.cfg.setProperty("WEEKDAYS_1CHAR", %(weekdays_1char)s);
    %(var)s.cfg.setProperty("WEEKDAYS_SHORT", %(weekdays_short)s);
    %(var)s.cfg.setProperty("WEEKDAYS_MEDIUM",%(weekdays_medium)s);
    %(var)s.cfg.setProperty("WEEKDAYS_LONG",  %(weekdays_long)s);
    %(var)s.cfg.setProperty("MONTHS_SHORT",   %(months_short)s);
    %(var)s.cfg.setProperty("MONTHS_LONG",    %(months_long)s);

    // on select handler
    function on_%(var)s_select(type,args,obj) {
        var dateElements = args[0][0];
        var date = new Date(dateElements[0], dateElements[1]-1, dateElements[2]);
        var format = %(field_format)s;
        var field = document.getElementById(%(field_id)s);
        field.value = formatDate(date, format);
        if (%(close_on_select)s) {
            %(var)s.hide();
        }
        %(on_select)s;
    }

    // register the handler and renders the calendar
    %(var)s.selectEvent.subscribe(on_%(var)s_select, %(var)s, true);
    %(var)s.render();
    """ % dict(var=self.var,
               container_id=container_id,
               field_id=json.dumps(self.field_id),
               field_format=json.dumps(self.field_format),
               title=json.dumps(self.title),
               close_button=json.dumps(self.close_button),
               close_on_select=json.dumps(self.close_on_select),
               on_select=self.on_select,
               curdate=js_datetime(self.curdate),
               mindate=js_datetime(self.mindate),
               maxdate=js_datetime(self.maxdate),
               weekdays_1char=json.dumps(weekdays_1char),
               weekdays_short=json.dumps(weekdays_short),
               weekdays_medium=json.dumps(weekdays_medium),
               weekdays_long=json.dumps(weekdays_long),
               months_short=json.dumps(months_short),
               months_long=json.dumps(months_long))

    h << h.script(js, type='text/javascript')

    return h.root


@presentation.render_for(Calendar, model='date_picker')
def render_date_picker(self, h, comp, *args):
    h << h.a(title=_(u'Show the calendar'),
             class_='date-picker',
             onclick=self.show())

    return h.root
