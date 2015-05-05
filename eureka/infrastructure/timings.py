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

import time
import functools

from nagare import log


class timeit(object):
    """Measures execution time of a function and annotate it with its elapsed time. """
    def __init__(self, name=None):
        self.name = name

    @property
    def log(self):
        return log.get_logger('.' + __name__)

    def log_elapsed_time(self, f, elapsed):
        hours, remainder = divmod(elapsed, 3600)
        mins, remainder = divmod(remainder, 60)
        secs, remainder = divmod(remainder, 1)
        msecs = remainder * 1000

        values = (hours, mins, secs, msecs)
        labels = ('hrs', 'mins', 'secs', 'msecs')
        values_labels = zip(values, labels)
        execution_time = ', '.join(['%d %s' % item for item in values_labels])

        func_name = self.name or f.func_name
        self.log.debug("%s executed in %s" % (func_name, execution_time))

    def __call__(self, f):
        def wrapper(*args, **kwargs):
            t1 = time.time()
            try:
                return f(*args, **kwargs)
            finally:
                t2 = time.time()
                self.log_elapsed_time(f, t2 - t1)

        functools.update_wrapper(wrapper, f)
        return wrapper
