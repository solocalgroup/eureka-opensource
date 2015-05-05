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

import os

from eureka.infrastructure.filesystem import get_fs_service
from eureka.infrastructure.tools import redirect_to, serve_static_content
from eureka.infrastructure.urls import get_url_service
from nagare import log, presentation, serializer, top
from nagare.namespaces import xhtml5
from webob.exc import HTTPNotFound
from .comp import Shell
from eureka.ui.desktop.staticcontent.comp import NotFoundError

# FIXME: should we use the "register_static" facility of the WSGI application instead?
# The files in these directories are served directly by the application
STATIC_DATA_DIRS = (
    'board',
    'gallery',
    'articles-thumbnails',
    'profile-photo',
    'profile-thumbnails',
    'attachments'
)


@presentation.init_for(Shell)
def init_shell(self, url, comp, *args):
    try:
        self.content.init(url, *args)  # forward everything to the content component
    except HTTPNotFound:
        raise NotFoundError()


@presentation.init_for(Shell, "(len(url) == 1) and (url[0] == 'connect_secure')")
def init_shell_autoconnection(self, url, comp, http_method, request):
    # The single sign-on is handled by the security manager itself. So, we let the user pass here
    # FIXME: redirect to / ?
    pass


@presentation.init_for(Shell, "len(url) > 1 and url[0] in STATIC_DATA_DIRS")
def init_shell_static_content(self, url, *args):
    logger = log.get_logger('.' + __name__)
    logger.debug('Serving static content: %s' % '/'.join(url))

    path = get_fs_service().expand_path(url)
    serve_static_content(path)


@presentation.init_for(Shell, "len(url) > 1 and url[0] == 'news-gallery'")  # obsolete URL (need to fix the articles images urls)
def init_shell_news_gallery(self, url, *args):
    raise redirect_to(get_url_service().expand_url(['gallery', url[1]]), permanent=True, base_url=get_url_service().base_url)
