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

from eureka.ui.desktop.pager import Pager, FilterMenu, PagerMenu, InfinitePager
from eureka.ui.desktop.pager.comp import Filter

from nagare import component, var
from nagare.i18n import _L

from eureka.domain.models import ArticleData, ArticleTopicData
from eureka.infrastructure.urls import get_url_service
from eureka.infrastructure.tools import is_integer
from eureka.ui.common.slider import Slider


class Article(object):
    def __init__(self, article):
        self.id = article if is_integer(article) else article.id
        self.display_full_description = var.Var(False)

    @property
    def article(self):
        return ArticleData.get(self.id)

    @property
    def url(self):
        return get_url_service().expand_url(['article', self.id])

    @property
    def thumbnail_url(self):
        if not self.article.thumbnail_filename:
            return None

        return get_url_service().expand_url(['articles-thumbnails', self.article.thumbnail_filename])


class ArticlePager(Pager):
    def __init__(self, query, max_items=10):
        super(ArticlePager, self).__init__(query, max_items)
        self.topic = None
        self.max_items = max_items

    @property
    def articles(self):
        return ArticleData.get_articles(True, None, self.topic, self.max_items, self.start).all()

    def change_topic(self, topic):
        self.topic = topic


class ArticleBoxMenu(object):
    def __init__(self, pager):
        filters = [Filter(t.label, t.label) for t in ArticleTopicData.query]

        self.filter_menu = FilterMenu(filters, 'Topic', pager)
        self.menu = component.Component(PagerMenu(_L(u'Topic'), self.filter_menu, pager, pager().change_topic))


class ArticleBox(object):
    def __init__(self, type, max_items=10):
        self.type = type
        self.pager = component.Component(ArticlePager(self.get_articles))
        self.infinite_pager = component.Component(InfinitePager(self.pager))
        self.article_block = component.Component(ArticleBlock())
        self.menu = component.Component(ArticleBoxMenu(self.pager))

    def get_articles(self):
        return ArticleData.get_articles(True, self.type)

    @property
    def see_all_url(self):
        return self.type.lower()


class ArticleBlock(object):

    def __init__(self):
        articles = [Article(a) for a in
                    ArticleData.get_articles(True, max_items=10)]
        self.slider = None
        if articles:
            self.slider = component.Component(Slider(articles))
