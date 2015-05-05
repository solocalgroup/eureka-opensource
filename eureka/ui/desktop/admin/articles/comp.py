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
import shutil
import uuid
from cStringIO import StringIO
from datetime import datetime

from nagare import component
from nagare.i18n import _

from eureka.domain.models import ArticleType, ArticleTopicData
from eureka.domain.repositories import ArticleRepository
from eureka.infrastructure.filesystem import get_fs_service
from eureka.infrastructure import tools
from eureka.ui.common.tab import TabContainer
from eureka.ui.desktop.article import ArticleEditor, Article


class ArticlesAdmin(object):
    def __init__(self, configuration):
        super(ArticlesAdmin, self).__init__()
        translation = {
            ArticleType.News: _(u'News'),
            ArticleType.Ongoing: _(u'Ongoing projects'),
            ArticleType.Headline: _(u'Headlines'),
        }
        items = [(translation[type], ArticlesTab(self, type)) for type in
                 ArticleType]
        self.tab_container = TabContainer(items)
        self.content = component.Component(self.tab_container)
        self.mobile_access = configuration['mobile_version']['enabled']

    def cancel_edition(self):
        self.content.becomes(self.tab_container)

    def preview_article(self, id):
        self.content.call(PreviewArticle(id))

    def edit_article(self, id=None, type=None):
        # handles None being passed as a id for convenience
        id = -1 if id is None else id

        # creates the editor
        editor = ArticleEditor(self, id, type=type, mobile_access=self.mobile_access)

        # starts edition
        if self.content.call(editor):
            # gets the article type
            article_type = editor.get_type()
            article_topic = ArticleTopicData.get_by(label=editor.get_topic())

            # write the thumbnail down
            thumbnails_dir = get_fs_service().expand_path(
                ['articles-thumbnails'])
            thumbnail = editor.get_thumbnail()
            thumbnail_filename = None
            thumbnail_path = None

            if thumbnail:
                thumbnail_extension = os.path.splitext(
                    editor.get_thumbnail_filename())[1].lower()
                os.path.splitext(editor.get_thumbnail_filename())[1].lower()
                os.path.splitext(editor.get_thumbnail_filename())[1].lower()
                thumbnail_filename = uuid.uuid4().hex + thumbnail_extension  # random filename
                thumbnail_path = os.path.join(thumbnails_dir,
                                              thumbnail_filename)

                with open(thumbnail_path, 'wb') as target:
                    shutil.copyfileobj(StringIO(thumbnail), target)

            # creates the article if it does not exist yet
            article_repository = ArticleRepository()
            article = article_repository.get_by_id(id)

            # FIXME: we should save the article in the ArticleEditor, not here
            if article:
                if article.thumbnail_filename:
                    if thumbnail:
                        # removes the old thumbnail if a new thumbnail has been uploaded
                        tools.remove_silently(os.path.join(thumbnails_dir,
                                                           article.thumbnail_filename))
                    else:
                        # otherwise, keep the old thumbnail
                        thumbnail_filename = article.thumbnail_filename

                article.type = article_type
                article.topic = article_topic
                article.title = editor.get_title()
                article.thumbnail_filename = thumbnail_filename
                article.content = editor.get_content()
                article.mobile_content = editor.get_mobile_content()
                article.tags = editor.get_tags()
            else:
                # FIXME: this algorithm is not scalable. Ranks should be reversed in that case
                for n in article_repository.get_by_type(article_type):
                    n.rank += 1

                article_repository.create(type=article_type,
                                          topic=article_topic,
                                          title=editor.get_title(),
                                          creation_date=datetime.now(),
                                          thumbnail_filename=thumbnail_filename,
                                          content=editor.get_content(),
                                          mobile_content=editor.get_mobile_content(),
                                          tags=editor.get_tags(),
                                          rank=1, published=False)


class PreviewArticle(object):
    def __init__(self, id):
        self.article = component.Component(Article(id))
        self.preview_width = 240 if self.article().article.type == ArticleType.Headline else 640


class ArticlesTab(object):
    def __init__(self, parent, type):
        self.parent = parent
        self.type = type
        self.article_repository = ArticleRepository()

    @property
    def articles(self):
        return self.article_repository.get_by_type(self.type)

    def edit_article(self, id):
        self.parent.edit_article(id=id)

    def preview_article(self, id):
        self.parent.preview_article(id=id)

    def create_article(self, type):
        self.parent.edit_article(type=type)

    def has_single_published_article(self, type):
        return type == ArticleType.Headline

    def set_publish(self, id, published):
        article = self.article_repository.get_by_id(id)
        type = article.type
        if self.has_single_published_article(type):  # unpublish other articles
            for a in self.article_repository.get_by_type(type):
                a.published = False
        article.published = published

    def delete_article(self, id):
        self.article_repository.get_by_id(id).delete()
