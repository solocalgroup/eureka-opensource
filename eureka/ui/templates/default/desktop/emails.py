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
from nagare.i18n import format_datetime

from eureka.ui.desktop.emails import AggregatedEmail


EMAIL_CSS = """
div.title {
    font-size: 1.2em;
    font-weight: bold;
}

div.date {
    margin: 2px 0;
    font-size: 0.9em;
    color: #666;
}
"""


@presentation.render_for(AggregatedEmail)
def render_aggregated_email(self, h, comp, *args):
    # head
    h.head << h.head.title(self.title)
    # h.head << h.head.meta({'http-equiv': 'Content-Type', 'content': 'text/html; charset=UTF-8'})

    # body
    with h.body:
        h << h.style(EMAIL_CSS, type='text/css')

        for idx, message in enumerate(self.user.pending_email_messages):
            if idx > 0:
                h << h.hr

            with h.div(class_='title'):
                h << message.subject

            with h.div(class_='date'):
                h << format_datetime(message.creation_date)

            content = h.parse_htmlstring(message.content)
            h << content.xpath('/html/body/*')

    return h.root
