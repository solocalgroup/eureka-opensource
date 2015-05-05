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

from nagare import var


class Autocomplete(object):
    def __init__(self, query, ac_class=u"", max_cache_entries=10,
                 delim_char=u"", min_query_length=2, max_results_displayed=10,
                 query_delay=0.5, query_question_mark=False, action=None,
                 error=None, id=None, **kwds):
        self._query = query
        self.input_params = kwds
        self._action = action
        self._error = error
        self.value = var.Var(u'')
        self.ac_class = ac_class
        self.max_cache_entries = max_cache_entries
        self.query_delay = query_delay
        self.delim_char = delim_char
        self.min_query_length = min_query_length
        self.max_results_displayed = max_results_displayed
        self.id = id

    def action(self, value):
        self.value(value)
        self._action(self.value())

    def hello(self, h):
        elements = self._query(unicode(self.value()))
        return u"\n".join([u"\t".join((elt[0], elt[1])) for elt in elements])
