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

import inspect
import functools

from nagare import local


def _cache(storage):
    """Get or create a cache dictionary in the provided storage object"""
    cache = getattr(storage, 'cache', None)
    if cache is None:
        cache = storage.cache = {}
    return cache


def _fingerprint(func, *args, **kwargs):
    """Compute the fingerprint of a call to the given function with the given
    positional and keyword arguments"""
    call_args = inspect.getcallargs(func, *args, **kwargs)
    return hash((func, frozenset(call_args.items())))


def cached(func=None, storage=None):
    """Decorator that caches the results of the function calls in the given storage
    object (local.request by default)"""
    if func is None:
        return lambda f: cached(f, storage)

    @functools.wraps(func)
    def decorated(*args, **kwargs):
        cache = _cache(storage or local.request)
        fingerprint = _fingerprint(func, *args, **kwargs)
        nothing = object()
        result = cache.get(fingerprint, nothing)
        if result is nothing:
            result = cache[fingerprint] = func(*args, **kwargs)
        return result

    return decorated
