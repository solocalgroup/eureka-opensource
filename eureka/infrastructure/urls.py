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

import threading
import urlparse


class URLService(object):

    def __init__(self, base_url):
        self.base_url = base_url
        self.relative_base_url = self._make_url_relative(base_url)

    def expand_url(self, urls, relative=True):
        if relative:
            urls = [self.relative_base_url] + urls
        else:
            urls = [self.base_url] + urls

        return '/'.join(str(u) for u in urls)

    def _make_url_relative(self, url):
        _, _, path, query, fragments = urlparse.urlsplit(url)
        return urlparse.urlunsplit((None, None, path, query, fragments))


__local = threading.local()


def set_url_service(url_service):
    __local.url_service = url_service


def get_url_service():
    return __local.url_service
