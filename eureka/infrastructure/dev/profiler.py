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

import cProfile
import pstats
import operator
import os
import threading
import time

from sqlalchemy.interfaces import ConnectionProxy

from nagare import database, log


class _SqlProfilingConnectionProxy(ConnectionProxy):

    def __init__(self):
        super(_SqlProfilingConnectionProxy, self).__init__()

        self.data = threading.local()
        self.reset()

    def reset(self):
        self.data.timings = {}

    def dump_cumulated(self, count=None):
        sorted_timings = sorted(self.data.timings.iteritems(),
                                key=operator.itemgetter(1), reverse=True)
        filtered_timings = sorted_timings[:count or len(sorted_timings)]

        log.debug('%d/%d slowest queries (%dms/%dms):',
                  len(filtered_timings),
                  len(sorted_timings),
                  sum(ms for (__, ms) in filtered_timings),
                  sum(ms for (__, ms) in sorted_timings))

        for (sql, ms) in filtered_timings:
            log.debug('  + %dms: %s', ms, sql[:100].replace('\n', '') + '...')

    def cursor_execute(self, execute, cursor, stmt, params, ctx, executemany):
        txt_params = tuple([(('"%s"' % p) if isinstance(p, basestring) else p) for p in params])
        desc = str(stmt) % tuple(txt_params)

        return self._timed(desc, execute, cursor, stmt, params, ctx)

    def _timed(self, desc, func, *args, **kw):
        start = time.time()
        result = func(*args, **kw)
        end = time.time()

        if hasattr(self.data, 'timings'):
            timings = self.data.timings
            timings[desc] = timings.get(desc, 0) + 1000 * (end - start)

        return result


profiling_conn_proxy = _SqlProfilingConnectionProxy()


def sql_profiled(func):

    def _(*args, **kw):
        profiling_conn_proxy.reset()
        result = func(*args, **kw)
        profiling_conn_proxy.dump_cumulated()

        return result

    return _


def cpu_profiled(func):

    def _(*args, **kw):
        # this is required for func to be visible, otherwise Python does
        # not export the value as it seems unused
        func

        return print_code_profile('func(*args, **kw)',
                                  globals(), locals(), with_result=True,
                                  root_func=func)
    return _


def print_code_profile(code, global_values=None, local_values=None,
                       with_result=False, strip_dirs=False, root_func=None):
    # adds result handling
    if with_result:
        code = 'result = ' + code

    # profiles the code execution
    profile = cProfile.Profile()
    profile.runctx(code, global_values, local_values)

    # dumps basic stats
    stats = pstats.Stats(profile)
    stats = stats.strip_dirs() if strip_dirs else stats
    stats.sort_stats('cumulative').print_stats(30)

    # dumps the profile
    _dump_profile(root_func, stats.stats)

    # eventually dumps the profile to a file
    # stats.dump_stats('/tmp/eureka.profile')

    return local_values['result'] if with_result else None


def _dump_profile(root_func, stats):

    class ProfileNode(object):
        def __init__(self, func, cc, tt, ct):
            self.func = func
            self.cc = cc
            self.tt = tt
            self.ct = ct
            self.caller = None
            self.callees = set()

    def create_tree(depth):
        # creates the root node
        root = None

        for (callee, (cc, __, tt, ct, callers)) in stats.iteritems():
            if root_func:
                if callee[0] == root_func.func_code.co_filename and callee[2] == root_func.func_name:
                    root = ProfileNode(callee, cc, tt, ct)
                    break
            elif not callers:  # 'app.py' in callee[0] and callee[2] == '__call__':
                root = ProfileNode(callee, cc, tt, ct)
                break

        # creates tree
        stack = [(root, depth)]

        while stack:
            (current, depth) = stack.pop()

            for (callee, (__, __, __, __, callers)) in stats.iteritems():
                caller = callers.get(current.func)

                if caller:
                    (_cc, __, _tt, _ct) = caller

                    node = ProfileNode(callee, _cc, _tt, _ct)
                    current.callees.add(node)
                    node.caller = current

                    if depth > 0:
                        stack.append((node, depth - 1))

        return root

    # dumps the result
    def pretty_filename(path):
        fn = os.path.basename(path)

        if fn in ('model.py', 'view.py'):
            fn = u'/'.join(path.split(os.sep)[-2:])

        return fn

    def dump_tree(root):
        stack = [(root, 0)]

        while stack:
            (node, indent) = stack.pop()

            (path, __, func_name) = node.func
            name = '%s#%s' % (pretty_filename(path), func_name)

            if indent:
                header = '   %s+ %s' % ('|  ' * (indent - 1), name)
            else:
                header = name

            if node.caller and node.ct > node.caller.ct:
                ct_percent = '???%'
            else:
                ct_percent = '%3d%%' % ((100.0 * (node.ct / node.caller.ct)) if node.caller else 100)

            print ('| %-95s | %9d (%s) | %14d (%3d%%) | %16d |'
                   % (header[:95], 1000 * node.ct, ct_percent,
                      1000 * node.tt, 100.0 * (node.tt / node.ct), node.cc))

            # the sort should be in reversed order but the stack insertion should be reversed too, so do not reverse at all!
            for subnode in sorted(node.callees, key=operator.attrgetter('ct')):
                if 1000 * subnode.ct >= 1 and subnode.ct >= node.ct * 5 / 100:  # filter < 1ms or < 5%
                    stack.append((subnode, indent + 1))

    root = create_tree(6)

    print '+-%s-+-%s-+-%s-+-%s-+' % ('-' * 95, '-' * 16, '-' * 21, '-' * 16)
    print '| %95s | %16s | %21s | %16s |' % ('Name', 'Time (ms)', 'Own Time (ms)', 'Invocation Count')
    print '+-%s-+-%s-+-%s-+-%s-+' % ('-' * 95, '-' * 16, '-' * 21, '-' * 16)
    dump_tree(root)
    print '+-%s-+-%s-+-%s-+-%s-+' % ('-' * 95, '-' * 16, '-' * 21, '-' * 16)


# hooks up the connection proxy in the nagare database module
original_set_metadata = database.set_metadata


def _custom_set_metadata(md, uri, debug, engine_settings):
    engine_settings.setdefault('proxy', profiling_conn_proxy)
    original_set_metadata(md, uri, debug, engine_settings)


database.set_metadata = _custom_set_metadata
