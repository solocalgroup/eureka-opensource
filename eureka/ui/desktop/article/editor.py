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

from nagare import editor, log
from nagare.i18n import _

from eureka.domain.models import ArticleType, ArticleTopicData
from eureka.infrastructure.urls import get_url_service
from eureka.domain.repositories import ArticleRepository
from eureka.infrastructure import validators, tools
from eureka.infrastructure.tools import is_string
from eureka.ui.common.confirmation import Confirmation


class ArticleEditor(editor.Editor):
    DEFAULT_TYPE = ArticleType.News

    def __init__(self, page, article_id, type=None, mobile_access=False):
        super(ArticleEditor, self).__init__(None)
        self.mobile_access = mobile_access
        article = ArticleRepository().get_by_id(article_id)

        self.page = page
        self.creation = article is None

        self.DEFAULT_TOPIC = ArticleTopicData.get_by(default=True).label
        # gets the initial values
        type = article.type if article else (type or self.DEFAULT_TYPE)
        topic = article.topic.label if article else self.DEFAULT_TOPIC
        title = article.title if article else u''
        content = article.content if article else u''
        mobile_content = article.mobile_content if article else u''
        tags = u', '.join(article.tags) if article else u''

        # creates the properties
        self.type = editor.Property(type)
        self.topic = editor.Property(topic)
        self.title = editor.Property(title).validate(validators.non_empty_string)
        self.thumbnail = editor.Property().validate(self._validate_thumbnail)
        self.thumbnail_filename = None
        self.content = editor.Property(content).validate(validators.string)
        self.mobile_content = editor.Property(mobile_content).validate(validators.string)
        self.tags = editor.Property(tags).validate(lambda t: validators.word_list(t, duplicates='remove'))

    def gallery_url(self, editor_id):
        return get_url_service().expand_url(['gallery-for', editor_id])

    @property
    def article_types(self):
        return [type for type in ArticleType]

    @property
    def article_topics(self):
        return [topic.label for topic in ArticleTopicData.query]

    def get_type(self):
        return self.type.value

    def get_topic(self):
        return self.topic.value

    def get_title(self):
        return self.title.value

    def get_thumbnail(self):
        return self.thumbnail.value

    def get_thumbnail_filename(self):
        return self.thumbnail_filename

    def get_content(self):
        return self.content.value

    def get_mobile_content(self):
        return self.mobile_content.value

    def get_tags(self):
        return self.tags.value

    def save(self, comp):
        properties = ('type', 'topic', 'title', 'content', 'mobile_content', 'tags')
        if super(ArticleEditor, self).commit((), properties):
            comp.answer(True)

    def confirm_cancel(self, comp):
        editor = Confirmation(_(u'All changes will be lost. You must confirm that you want to cancel edition'),
                              _(u'Forget changes'), _(u'Resume'))

        if comp.call(editor):
            self.page.cancel_edition()

    def _validate_thumbnail(self, f):
        if is_string(f):
            return None

        if f.done == -1:
            raise ValueError(_(u'Transfer was interrupted'))

        # finds out the filename (I.E. 4 returns the on-disk path)
        self.thumbnail_filename = f.filename.split('\\')[-1]

        try:
            return tools.create_thumbnail(f.file, 870, 271)
        except IOError as e:
            errno, strerror = e
            log.exception('thumbnail reception error: %s', strerror)
            raise IOError(errno, _(u'Reception error'))
