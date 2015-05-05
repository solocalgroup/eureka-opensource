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

from datetime import datetime

from webob.exc import HTTPOk, HTTPNotFound

from nagare import presentation
from nagare.namespaces import xml

from eureka.infrastructure.urls import get_url_service
from eureka.infrastructure import rss
from eureka.domain.repositories import ChallengeRepository, UserRepository
from eureka.domain.models import ArticleType
from eureka.infrastructure.tools import redirect_to
from .comp import Portal
from eureka.ui.desktop.gallery import Gallery


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise HTTPNotFound()


@presentation.init_for(Portal, "(len(url) == 3) and (url[0] == 'password_reset')")
def init_portal_password_reset(self, url, comp, http_method, request):
    uid = url[1]
    token = url[2]
    self.confirm_reset_password(uid, token)


@presentation.init_for(Portal, "(len(url) == 2) and (url[0] == 'idea')")
def init_portal_idea(self, url, *args):
    self.show_idea(to_int(url[1]))


@presentation.init_for(Portal, "len(url) == 2 and url[0] == 'rss' and url[1] == 'ideas.rss'")
def init_portal_idea(self, url, comp, *args):
    r_feed = comp.render(rss.RssRenderer(), model='published_ideas')
    r_feed = r_feed.write_xmlstring()
    e = HTTPOk(headerlist=[('Content-Type', '')])
    e.body = '<?xml version="1.0" encoding="UTF-8"?>\n' + r_feed

    e.content_type = 'application/xml'

    raise e


@presentation.init_for(Portal, "(len(url) == 1) and (url[0] == 'home')")
def init_portal_home(self, url, *args):
    self.show_home()


@presentation.init_for(Portal, "(len(url) == 1) and (url[0] == 'improvements')")
def init_portal_improvements(self, url, *args):
    self.show_suggestions()


@presentation.init_for(Portal, "(len(url) == 1) and (url[0] == 'improvements_submit')")
def init_portal_improvements_submit(self, url, *args):
    self.show_submit_suggestion()


@presentation.init_for(Portal, "(len(url) == 1) and (url[0] == 'contact_us')")
def init_portal_contact_us(self, url, *args):
    self.show_contact()


@presentation.init_for(Portal, "(len(url) == 1) and (url[0] == 'help')")
def init_portal_help(self, url, *args):
    self.show_help()


@presentation.init_for(Portal, "(len(url) == 1) and (url[0] == 'shop')")
def init_portal_shop(self, url, *args):
    self.show_shop()


@presentation.init_for(Portal, "(len(url) == 1) and (url[0] == 'terms_of_use')")
def init_portal_terms_of_use(self, url, *args):
    self.show_terms_of_use()


@presentation.init_for(Portal, "(len(url) == 1) and (url[0] == 'welcome')")
def init_portal_welcome(self, url, *args):
    self.show_welcome()


@presentation.init_for(Portal, "len(url) == 1 and url[0] == 'news'")
def init_portal_news(self, url, *args):
    self.show_articles_by_type(ArticleType.News)


@presentation.init_for(Portal, "len(url) == 1 and url[0] == 'ongoing'")
def init_portal_ongoing(self, url, *args):
    self.show_articles_by_type(ArticleType.Ongoing)


@presentation.init_for(Portal, "(len(url) == 2) and (url[0] == 'article')")
def init_portal_article(self, url, *args):
    self.show_article(to_int(url[1]))


@presentation.init_for(Portal, "(len(url) == 1) and (url[0] == 'launched-ideas')")
def init_portal_show_launched_ideas(self, url, *args):
    self.show_launched_ideas()


@presentation.init_for(Portal, "(len(url) == 2) and (url[0] == 'challenge')")
def init_portal_challenge(self, url, *args):
    self.show_challenge(to_int(url[1]))


@presentation.init_for(Portal, "(len(url) == 1) and (url[0] == 'challenges')")
def init_portal_challenges(self, url, *args):
    self.show_challenge_ideas()


@presentation.init_for(Portal, "(len(url) == 2) and (url[0] == 'challenge_ideas')")
def init_portal_challenge_ideas(self, url, *args):
    self.show_challenge_ideas(to_int(url[1]))


@presentation.init_for(Portal, "(len(url) == 2) and (url[0] == 'profile')")
def init_portal_profile(self, url, *args):
    uid = url[1]
    if not UserRepository().get_by_uid(uid):
        raise HTTPNotFound()

    self.show_user_profile(uid)


@presentation.init_for(Portal, "(len(url) == 1) and (url[0] == 'administration')")
def init_portal_administration(self, url, comp, http_method, request):
    self.show_administration_menu()


@presentation.init_for(Portal, "(len(url) == 1) and (url[0] == 'dsig_basket')")
def init_portal_dsig_basket(self, url, *args):
    self.show_dsig_ideas_basket()


@presentation.init_for(Portal, "(len(url) == 1) and (url[0] == 'show_user_ideas_basket')")
def init_portal_show_user_ideas_basket(self, url, *args):
    self.show_user_ideas_basket()


@presentation.init_for(Portal, "(len(url) == 1) and (url[0] == 'ideas')")
def init_portal_ideas(self, url, *args):
    self.show_ideas()


@presentation.init_for(Portal, "(len(url) == 1) and (url[0] == 'show_most_viewed_ideas')")
def init_portal_show_most_viewed_ideas(self, url, *args):
    self.show_most_viewed_ideas()


@presentation.init_for(Portal, "(len(url) == 1) and (url[0] == 'fi_basket')")
def init_portal_fi_basket(self, url, *args):
    self.show_fi_ideas_basket()


@presentation.init_for(Portal, "(len(url) == 1) and (url[0] == 'di_basket')")
def init_portal_di_basket(self, url, *args):
    self.show_di_ideas_basket()


@presentation.init_for(Portal, "len(url) <= 2 and url[0] == 'submit'")
def init_portal_submit(self, url, *args):
    challenge_id = None

    if len(url) == 2:
        challenge_id = to_int(url[1])
        # make sure the challenge exists and is active; otherwise, redirect to the "normal" submission
        challenge = ChallengeRepository().get_by_id(challenge_id)
        now = datetime.now()
        if not challenge or not challenge.is_active(now):
            raise redirect_to('/submit', permanent=True, base_url=get_url_service().base_url)

    self.show_submit_idea(challenge_id)


@presentation.init_for(Portal, "len(url) == 2 and url[0] == 'gallery-for'")
def init_portal_gallery_for(self, url, comp, * args):
    comp.becomes(Gallery(url[1]))  # special gallery


@presentation.init_for(Portal, "url == ('xml', 'published_ideas')")
def init_portal_xml_published_ideas(self, url, comp, http_method, request):
    root = comp.render(xml.Renderer(), model='xml_published_ideas')
    # Now we need to fix the avatar urls because we can't pass the request object to the component
    # render function (or did I missed something ?)
    for node in root.xpath('//avatar'):
        node.text = request.application_url + node.text
    raise HTTPOk(content_type='application/xml', body=root.write_xmlstring(
        xml_declaration=True, encoding='UTF-8'))
