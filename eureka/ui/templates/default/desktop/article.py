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

import operator
import re
from lxml import etree as ET
from lxml.html.clean import clean_html

from nagare import presentation, component
from nagare.i18n import _, format_datetime

from eureka.domain.models import ArticleType
from eureka.ui.common.yui2 import RichTextEditor
from eureka.infrastructure.tools import limit_string, text_to_html_elements
from eureka.infrastructure import htmltruncate

from eureka.ui.desktop.article import (Article, ArticlePager, ArticleBox,
                                       ArticleBlock, ArticleBoxMenu,
                                       ArticleEditor)


def render_tags(article, h):
    elements = []
    for t in article.article.tags:
        elements.append(h.span(class_='tag-%s' % t))
    return elements


# translated strings
def get_article_type_translation(type):
    Translation = {
        ArticleType.News: _(u'News'),
        ArticleType.Ongoing: _(u'Ongoing projects'),
        ArticleType.Headline: _(u'Headlines'),
    }
    return Translation.get(type, '')


def html(h, text, limit=None, clean=False):

    if clean:
        text = clean_html(text)

    t = h.span(h.parse_htmlstring(text, fragment=True))

    if limit and len(text) > limit:
        if 'rowspan' in text.lower():
            # Don't know how to limit table with rowspan properly
            # colspan doesn't seem to be a problem
            return text_only(h, text, limit)

        try:
            text = ET.tostring(t, method='xml')
            text = htmltruncate.truncate(text, limit, '...')
            return h.parse_htmlstring(text, fragment=True)[0]
        except htmltruncate.UnbalancedError:
            return text_only(h, text, limit)
    else:
        return t


def text_only(h, text, limit=None):
    text = clean_html(text)
    node = h.span(h.parse_htmlstring(text, fragment=True))

    def f(node):

        return ((node.text or '') +
                ''.join(f(children) for children in node) +
                (node.tail or ''))

    text = re.sub('\s+', ' ', f(node), flags=re.UNICODE)

    if limit:
        if len(text) <= limit:
            return text
        else:
            return ' '.join(text[:limit + 1].split(' ')[0:-1]) + '...'

    return text


def render_title(h, *args):
    return h.h1(h.span(*args), class_="titlebox")


@presentation.render_for(Article, model='title')
def render_article_title(self, h, comp, *args):
    h << render_title(h,
                      self.article.title,
                      render_tags(self, h))
    return h.root


@presentation.render_for(Article, model='title_link')
def render_article_title_link(self, h, comp, *args):
    h << h.a(self.article.title,
             render_tags(self, h),
             class_='title',
             href=self.url)
    return h.root


@presentation.render_for(Article, model='content')
def render_article_content(self, h, comp, *args):
    with h.div(class_='content'):
        h << html(h, self.article.content)
    return h.root


@presentation.render_for(Article, model='date')
def render_article_date(self, h, comp, *args):
    if self.article.creation_date:
        with h.div(class_='date'):
            h << format_datetime(self.article.creation_date, format='short')
    return h.root


@presentation.render_for(Article, model='thumbnail')
def render_article_thumbnail(self, h, comp, *args):
    if self.thumbnail_url:
        with h.a(href=self.url, class_='thumbnail'):
            h << h.img(src=self.thumbnail_url,
                       alt=self.article.title,
                       title=self.article.title)
    return h.root


@presentation.render_for(Article)
@presentation.render_for(Article, model='headline')
def render_article(self, h, comp, *args):
    with h.div(class_='article %s topic-%s' % (self.article.type.lower(), self.article.topic.key)):
        h << comp.render(h, model='title')
        h << h.span(self.article.topic.label or '', class_='thematic')
        h << comp.render(h, model='date')
        h << comp.render(h, model='content')

    return h.root


@presentation.render_for(Article, model="list_item")
def render_article_list_item(self, h, comp, *args):
    limit = 500
    date = format_datetime(self.article.creation_date, format='short')

    if len(self.article.content) > limit:
        if self.display_full_description():
            content = html(h, self.article.content)
        else:
            content = html(h, self.article.content, limit)

        display_more = True
    else:
        content = html(h, self.article.content)
        display_more = False

    with h.li:
        with h.h1:
            h << h.a(self.article.title, href=self.url)
        h << h.span(self.article.topic.label or '', class_='thematic')
        h << h.span(date, class_='date')

        with h.div:
            h << content

        if display_more and not self.display_full_description():
            h << h.a(_(u'Read more'), class_='more').action(lambda: self.display_full_description(True))
        elif display_more and self.display_full_description():
            h << h.a(_(u'Read less'), class_='more').action(lambda: self.display_full_description(False))

    return h.root


@presentation.render_for(Article, model="slider")
def render_article_list_item(self, h, comp, *args):
    with h.div(class_='item'):
        if self.thumbnail_url:
            h << h.img(
                src=self.thumbnail_url,
                alt=self.article.title,
                title=self.article.title)

        with h.div(class_='summary'):
            h << h.h1(h.a(self.article.title, href=self.url))
            h << h.p(h.a(text_only(h, self.article.content, 250), href=self.url))

    return h.root


@presentation.render_for(ArticlePager)
def render_article_pager(self, h, comp, *args):
    with h.ul(class_='actu-items'):
        for article in self.articles:
            h << component.Component(Article(article.id)).render(h.AsyncRenderer(), model="list_item")

    return h.root


@presentation.render_for(ArticlePager, model='count')
def render_article_count(self, h, comp, *args):
    return ''


@presentation.render_for(ArticleBox)
def render_article_box(self, h, comp, *args):
    SeeAllArticles = {
        ArticleType.News: _(u'See all news'),
        ArticleType.Ongoing: _(u'See all ongoing projects'),
        ArticleType.Headline: _(u'See all headlines'),
    }

    with h.div(class_='articles ' + self.type.lower()):
        h << h.h1(get_article_type_translation(self.type))
        h << component.Component(self.pager)
        h << h.a(SeeAllArticles[self.type], href=self.see_all_url, class_='more-articles')
    return h.root


@presentation.render_for(ArticleBox, model='full')
def render_article_box_full(self, h, comp, *args):
    h << self.article_block.render(h.AsyncRenderer())
    with h.section(class_='actu'):
        h << render_title(h, get_article_type_translation(self.type))

        h << self.menu.render(h.AsyncRenderer())

        with h.div(id='infinite-pager'):
            h << self.infinite_pager.render(h.AsyncRenderer())
    return h.root


@presentation.render_for(ArticleBoxMenu)
def render_article_menu(self, h, comp, *args):
    with h.div(class_='ordered'):
        h << _(u'Filter by :')
        h << self.menu

    return h.root


@presentation.render_for(ArticleEditor)
def render_article_editor(self, h, comp, *args):
    # renders the article editor
    with h.div(class_='article-editor'):
        h << h.h2(_(u'Edit the article'))
        with h.form:
            with h.div(class_='fields'):
                with h.div(class_='title field'):
                    field_id = h.generate_id('field')
                    h << h.label(_(u'Title:'), for_=field_id)
                    h << h.input(id=field_id,
                                 type='text',
                                 class_='text wide',
                                 value=self.title()).action(self.title).error(self.title.error)

                with h.div(class_='tags field'):
                    field_id = h.generate_id('field')
                    h << h.label(_(u'Tags:'), for_=field_id)
                    h << h.input(id=field_id,
                                 type='text',
                                 class_='text wide',
                                 value=self.tags()).action(self.tags).error(self.tags.error)

                with h.div(class_='type field'):
                    field_id = h.generate_id('field')
                    types = [(get_article_type_translation(type), type) for type in self.article_types]
                    types = sorted(types, key=operator.itemgetter(0))
                    type_options = [h.option(n, value=v).selected(self.type())
                                    for (n, v) in types]
                    h << h.label(_(u'Type:'), for_=field_id)
                    with h.select(type_options).action(self.type) as select:
                        if not self.creation:
                            select.set('disabled', 'true')

                with h.div(class_='topic field'):
                    field_id = h.generate_id('field')
                    topics = sorted(self.article_topics)
                    topic_options = [h.option(v, value=v).selected(self.topic())
                                     for v in topics]
                    h << h.label(_(u'Topic:'), for_=field_id)
                    h << h.select(topic_options).action(self.topic)

                with h.div(class_='thumbnail field'):
                    field_id = h.generate_id('field')
                    h << h.label(_(u'Thumbnail:'), '(870 x 271)', for_=field_id)
                    h << h.input(id=field_id,
                                 type='file',
                                 class_='file').action(self.thumbnail)

                with h.div(class_='desktop-content field'):
                    field_id = h.generate_id('field')
                    h << h.label(_(u'Desktop content:'), for_=field_id)
                    rte = RichTextEditor(property=self.content,
                                         height=300,
                                         id=field_id,
                                         gallery_url=self.gallery_url(field_id))
                    h << component.Component(rte)

                if self.mobile_access:
                    with h.div(class_='mobile-content field'):
                        field_id = h.generate_id('field')
                        h << h.label(_(u'Mobile content:'), for_=field_id)
                        rte = RichTextEditor(property=self.mobile_content,
                                             height=400,
                                             max_chars=200,
                                             id=field_id,
                                             gallery_url=self.gallery_url(field_id))
                        h << component.Component(rte)

            with h.div(class_='buttons'):
                h << h.input(type='submit', value=_(u'Save')).action(lambda: self.save(comp))
                h << h.input(type='submit', value=_(u'Cancel')).action(lambda: self.confirm_cancel(comp))

    return h.root


@presentation.render_for(ArticleBlock)
def render_article_block(self, h, comp, *args):
    if self.slider:
        h << self.slider

    return h.root
