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

from nagare import presentation, component
from nagare.namespaces import xhtml
from nagare.i18n import _

from eureka.infrastructure.urls import get_url_service
from eureka.ui.common.yui2 import flashmessage
from eureka.ui.common.yui2 import Wait
from eureka.ui.common.yui2 import Confirm
from eureka.ui.desktop import APP_TITLE

from eureka.ui.desktop.shell.comp import Shell


YUI_PREFIX = 'yui-2.8.0r4/'


@presentation.render_for(Shell)
def render_shell(self, h, comp, *args):
    comp.render(h, model='head')
    h << comp.render(h, model='body')
    return h.root


@presentation.render_for(Shell, model='head')
def render_shell_head(self, h, comp, *args):
    html_conf = self.configuration['html']

    # title
    h.head << h.head.title(APP_TITLE)

    # rss feed
    h.head << h.head.link(href=get_url_service().expand_url(['rss', 'ideas.rss']), rel='', type='application/rss+xml', title=_('Ideas'))

    # favicon
    h.head << h.head.link(rel="icon", type="image/png",
                          href=h.head.static_url + "favicon.png")
    h.head << h.head.link(rel="shortcut icon", type="image/x-icon",
                          href=h.head.static_url + "favicon.ico")

    # prevent indexing by robots
    h.head << h.head.meta(name='robots', content='noindex,nofollow')

    # additional meta information
    h.head << h.head.meta({'http-equiv': 'Content-Type',
                           'content': 'text/html; charset=UTF-8'})
    h.head << h.head.meta({'http-equiv': 'Content-Script-Type',
                           'content': 'text/javascript'})

    css_files = [YUI_PREFIX + 'assets/skins/sam/skin.css',
                 'css/base.css',
                 'css/design.css',
                 'css/layout.css',
                 'css/fonts.css']
    for css_file in css_files:
        h.head.css_url(css_file, media='all')

    js_files = ['js/vendor/html5shiv.js',
                'js/vendor/nwmatcher-1.2.5-min.js',
                'js/vendor/selectivizr-min.js']
    ie_js = """[if (gte IE 6)&(lte IE 8)]>
    <script src="%s"></script>
    <script src="%s"></script>
    <script src="%s"></script>
    <![endif]""" % tuple(
        xhtml.absolute_url(u, h.head.static_url) for u in js_files)
    h.head << h.head.comment(ie_js)

    # Javascript
    if html_conf['use_combined_js']:
        js_files = ('js/desktop-combined.js',)
    else:
        js_files = (
            YUI_PREFIX + 'utilities/utilities.js',
            YUI_PREFIX + 'element/element-min.js',
            YUI_PREFIX + 'datasource/datasource-min.js',
            YUI_PREFIX + 'datatable/datatable-min.js',
            YUI_PREFIX + 'autocomplete/autocomplete-min.js',
            YUI_PREFIX + 'container/container-min.js',
            YUI_PREFIX + 'menu/menu-min.js',
            YUI_PREFIX + 'button/button-min.js',
            YUI_PREFIX + 'editor/editor-min.js',
            YUI_PREFIX + 'calendar/calendar-min.js',
            'js/notification.js',
            'js/rte.js',
            'js/desktop.js',
            'yui-3.4.1/yui/yui-min.js',
        )

    for js_file in js_files:
        h.head.javascript_url(js_file)

    return h.root


@presentation.render_for(Shell, model='body')
def render_shell_body(self, h, comp, *args):
    with h.body(id='shell', class_='yui-skin-sam'):  # specific class for YUI
        # flash notifier
        h << component.Component(flashmessage.FlashNotifier())

        # transient flash message
        if flashmessage.has_flash():
            h << component.Component(flashmessage.get_flash())

        h << component.Component(Wait())

        # hidden dialogs
        h << component.Component(Confirm())

        # content
        h << self.content

    return h.root


@presentation.render_for(Shell, model='not_found_error')
def render_error_page(self, h, comp, *args):
    with h.html():
        with h.div(id='error-page'):
            with h.p:
                h << _(u"An error happened, please accept our apologies.") << " "
                h << _(u"Click") << " " << h.a(_(u"here"), href="/") << " " << _(
                    u"to go back to the %s home page") % APP_TITLE

    return h.root
