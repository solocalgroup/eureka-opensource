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
from nagare.namespaces import xhtml
from nagare.i18n import _

from eureka.ui.desktop.portal import (HomePage, HomeBlock, EditoLink,
                                      ImprovementsLink, Empty,
                                      OngoingArticlesBox, IdeaCounter,
                                      IdeasByDomain)


@presentation.render_for(HomePage)
def render_home_page(self, h, comp, *args):
    with h.section(class_='home'):
        h << self.article_block.render(h.AsyncRenderer())
        h << self.column

    return h.root


@presentation.render_for(HomeBlock)
def render_home_block(self, h, comp, *args):
    css_class = 'home-block' + (' rounded' if self.rounded else '')
    with h.div(id=self.id, class_=css_class):
        h << self.content
    return h.root


@presentation.render_for(Empty)
def render_empty(self, h, comp, *args):
    h << self.message
    return h.root


@presentation.render_for(OngoingArticlesBox)
def render_ongoing_articles_box(self, h, comp, *args):
    h << self.articles
    label = _("See all launched ideas")
    h << h.a(label, title=label, class_='launched-ideas', href=self.launched_ideas_url).action(self.view_launched_ideas)
    return h.root


@presentation.render_for(EditoLink)
def render_edito_link(self, h, comp, *args):
    with h.a(href="welcome"):
        with h.span(class_='important'):
            h << _(u"Discover Eurêka")
    return h.root


@presentation.render_for(ImprovementsLink)
def render_improvements_link(self, h, comp, *args):
    with h.a(href="improvements"):
        h << h.span(_(u"Your suggestions"), class_='important')
        h << h.br
        h << _(u"Consult the list of suggestions")
    return h.root


@presentation.render_for(IdeaCounter)
def render_idea_counter(self, h, comp, *args):
    count = self.find_ideas_count()

    # renders the digits
    digits_r = xhtml.Renderer()

    with digits_r.span:
        digits_r << (digits_r.span(i, class_='digit') for i in str(count).zfill(4))

    digits_html = digits_r.root.write_htmlstring()

    #  renders the whole counter
    with h.div(class_='counter'):
        # TRANSLATORS: we do not use %d because we inject the nb of ideas in
        #              HTML form
        h << h.parse_htmlstring(_(u'Already %s ideas') % digits_html)

    h << h.a(_(u'View the ideas'), href=self.ideas_url)

    return h.root


@presentation.render_for(IdeasByDomain)
def render_ideas_by_domain(self, h, comp, *args):
    h << h.h1(_(u'Ideas by domain'))

    with h.ul:
        for (id, label, count) in self.find_count_by_domain():
            with h.li:
                h << h.a(_(label), ' (%d)' % count).action(lambda id=id, label=label: comp.answer((id, label)))

    return h.root
