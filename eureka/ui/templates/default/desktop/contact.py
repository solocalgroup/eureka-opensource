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

from eureka.ui.desktop.contact import Contact


@presentation.render_for(Contact)
def render_contact(self, h, comp, *args):
    with h.div(class_="contact rounded"):
        with h.h1(class_="tab big active"):
            with h.span:
                h << _(u'Contact form')

        with h.h2:
            h << _(u'A problem? A question? The IPS team is listening you and will answer your questions as soon as possible')

        with h.form:
            with h.div(class_='fields'):
                if not self.user:
                    with h.div(class_='sender-field field'):
                        h << h.label(_(u'Your email address'))
                        h << h.input(type='text',
                                     class_='text wide',
                                     value=self.sender_email()).action(self.sender_email).error(self.sender_email.error)

                with h.div(class_='subject-field field'):
                    h << h.label(_(u'Subject'))
                    h << h.input(type='text',
                                 class_='text wide',
                                 value=self.subject()).action(self.subject).error(self.subject.error)

                with h.div(class_='message-field field'):
                    h << h.label(_(u'Message'))
                    h << h.textarea(self.message(),
                                    rows=5,
                                    class_='wide').action(self.message).error(self.message.error)

            with h.div(class_='buttons'):
                h << h.input(type="submit",
                             value=_(u'Submit')).action(self.commit)

    return h.root
