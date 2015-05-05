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

from lxml import etree

from nagare import component, i18n

from eureka.pkg import resource_stream
from eureka.infrastructure.urls import get_url_service
from eureka.infrastructure import event_management, registry
from eureka.ui.common.videoplayer import VideoPlayer
from eureka.ui.desktop.idea.comp import SubmitIdeaBox
from webob.exc import HTTPInternalServerError, HTTPNotFound


class XMLContentBlock(object):
    def __init__(self, parent):
        event_management._register_listener(parent, self)

    @property
    def xml_file(self):
        language = i18n.get_locale().language
        return resource_stream(os.path.join('data', 'staticcontent', language, self.filename))

    def inner_xml(self, element):
        return (element.text or '') + ''.join(map(etree.tostring, element))


class HTMLContent(object):

    def __init__(self, filename, base_path=None):
        if not base_path:
            base_path = os.path.join('static', 'html')
        self.filepath = os.path.join(base_path, filename)

    @property
    def content(self):
        with resource_stream(self.filepath) as content:
            return content.read()


class Welcome(XMLContentBlock):
    filename = 'welcome.xml'

    def __init__(self, parent):
        super(Welcome, self).__init__(parent)

        self.submit_idea_box = component.Component(SubmitIdeaBox(self))

        misc_conf = registry.get_configuration('misc')
        video_url = misc_conf['tutorial_video_url']
        video_splash_url = misc_conf['tutorial_splash_url']
        player = VideoPlayer(video_url, video_splash_url, width=640, height=360, autoplay=(video_splash_url is not None))
        self.video_player = component.Component(player)


class OnlineShop(XMLContentBlock):
    filename = 'online_shop.xml'

    def view_details(self):
        event_management._emit_signal(self, "VIEW_SHOP")


class FAQ(XMLContentBlock):
    filename = 'faq.xml'

    def __init__(self, parent):
        super(FAQ, self).__init__(parent)
        self.opened_section = None

    def open_section(self, section_name):
        self.opened_section = section_name

    @property
    def improvements_url(self):
        return get_url_service().expand_url(['improvements'])


class TermsOfUse(XMLContentBlock):
    filename = 'terms_of_use.xml'


class InternalServerError(HTTPInternalServerError):

    def __init__(self):
        body = HTMLContent(filename='500.html').content
        super(InternalServerError, self).__init__(body=body)


class NotFoundError(HTTPNotFound):

    def __init__(self):
        body = HTMLContent(filename='404.html').content
        super(NotFoundError, self).__init__(body=body)
