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

from eureka.ui.common.choice import CheckboxChoice, RadioChoice


@presentation.render_for(CheckboxChoice)
def render_checkbox_choice(self, h, comp, *args):
    def append_choice(idx):
        value = self.items[int(idx)][1]
        self.property().append(value)

    id = self.id or h.generate_id('checkboxchoice')
    with h.div(id=id, class_='checkbox-choice'):
        for idx, (label, value) in enumerate(self.items):
            with h.div(id='%s-item%d' % (id, idx),
                       class_='checkboxchoice-item field'):

                checkbox_id = '%s-checkbox%d' % (id, idx)
                h << h.input(type='checkbox',
                             class_='radio',
                             id=checkbox_id,
                             value=str(idx)).selected(value in self.property()).action(append_choice)
                h << h.label(label,
                             for_=checkbox_id)

    return h.root


@presentation.render_for(RadioChoice)
def render_radio_choice(self, h, comp, *args):
    id = self.id or h.generate_id('radiochoice')
    with h.div(id=id, class_='radio-choice'):
        for idx, (label, value) in enumerate(self.items):
            with h.div(id='%s-item%d' % (id, idx),
                       class_='radiochoice-item field'):

                radio_id = '%s-radio%d' % (id, idx)
                h << h.input(type='radio',
                             class_='radio',
                             id=radio_id,
                             name=id).selected(self.property() == value).action(lambda value=value: self.property(value))
                h << h.label(label,
                             for_=radio_id)

    return h.root
