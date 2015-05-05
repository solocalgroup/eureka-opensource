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

from nagare import presentation
from nagare.i18n import _

from eureka.ui.desktop.admin import ArticlesAdmin, ArticlesTab, PreviewArticle


@presentation.render_for(ArticlesAdmin)
def render_articles_admin(self, h, comp, *args):
    with h.div(class_='articles-admin rounded'):
        h << self.content
    return h.root


@presentation.render_for(PreviewArticle)
def render_preview_article(self, h, comp, *args):
    with h.div(class_='article-preview'):
        with h.div(class_='preview-area', style='width: %spx' % self.preview_width):
            h << self.article
        with h.div(class_='buttons'):
            label = _(u'Back')
            h << h.a(label,
                     title=label,
                     class_='confirm-button').action(comp.answer)
    return h.root


@presentation.render_for(ArticlesTab)
def render_articles_tab(self, h, comp, *args):
    with h.div(class_='articles-tab'):
        with h.table(class_='datatable'):
            with h.thead:
                with h.tr:
                    h << h.th(_(u'Article title'), class_='title')
                    h << h.th(_(u'Published'), class_='publication-status')
                    h << h.th(_(u'Actions'), class_='actions')

            with h.tbody:
                for article in self.articles:
                    with h.tr(class_='published' if article.published else 'unpublished'):
                        with h.td(class_='title'):
                            with h.a(title=_(u'Edit article')).action(lambda id=article.id: self.edit_article(id)):
                                h << article.title

                        with h.td(class_='publication-status'):
                            if article.published:
                                h << h.a(_(u'Yes'),
                                         title=_(u'Unpublish'),
                                         class_='yes').action(lambda id=article.id: self.set_publish(id, False))
                            else:
                                h << h.a(_(u'No'),
                                         title=_(u'Publish'),
                                         class_='no').action(lambda id=article.id: self.set_publish(id, True))

                        with h.td(class_='actions'):
                            # preview
                            label = _(u'Preview the article')
                            h << h.a(label,
                                     title=label,
                                     class_='preview-article').action(lambda id=article.id: self.preview_article(id))

                            # delete
                            title = _(u'Confirm delete?')
                            message = _(u'The article will be deleted. Are you sure?')
                            js = 'return yuiConfirm(this.href, "%s", "%s", "%s", "%s")' % (title, message, _(u'Delete'), _(u'Cancel'))
                            label = _(u'Delete the article')
                            h << h.a(label,
                                     title=label,
                                     class_='delete-article',
                                     onclick=js).action(lambda id=article.id: self.delete_article(id))

        with h.div(class_='buttons'):
            h << h.a(_(u'Add an article'),
                     class_='confirm-button').action(lambda: self.create_article(self.type))

    return h.root
