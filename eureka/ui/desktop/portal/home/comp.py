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

from sqlalchemy import func

from nagare import component
from nagare.database import session
from nagare.i18n import _L

from eureka.domain.models import ArticleData, ArticleType, DomainData
from eureka.domain.models import IdeaData, IdeaWFContextData, StateData
from eureka.domain.services import get_workflow
from eureka.infrastructure.urls import get_url_service
from eureka.domain import queries
from eureka.domain.repositories import IdeaRepository
from eureka.infrastructure import event_management
from eureka.ui.desktop.idea import IdeasActivityPager
from eureka.ui.desktop.poll import Poll
from eureka.ui.desktop.article import Article, ArticleBox, ArticleBlock


class HomePage(object):
    def __init__(self, parent):
        self.parent = parent
        event_management._register_listener(self.parent, self)

        create_block = lambda id, c, rounded = True: component.Component(HomeBlock(id, c, rounded))

        self.column = create_block('ideas-activity', IdeasActivityPager(parent))
        self.edito_link = create_block('edito-link', EditoLink(), rounded=False)
        headline_comp = component.Component(Article(self.headline_article), model='headline') if self.headline_article else Empty()
        self.headline = create_block('headline', headline_comp)
        self.article_box = create_block('news', ArticleBox(ArticleType.News, 5))
        self.article_block = component.Component(ArticleBlock())
        self.idea_counter = create_block('idea-counter', IdeaCounter(self))

        self.ideas_by_domain = create_block('ideas-by-domain', component.Component(IdeasByDomain()).on_answer(lambda v: self.show_domain(*v)))
        poll = self.find_current_poll()
        self.poll = create_block('poll', Poll(poll.id)) if poll else None
        self.ongoing = create_block('ongoing', OngoingArticlesBox(parent, 6))
        self.improvements_link = create_block('improvements-link', ImprovementsLink(), rounded=False)

    def show_domain(self, id, label):
        event_management._emit_signal(self, 'VIEW_DOMAIN_IDEAS', domain_id=id, domain_label=label)

    @property
    def headline_article(self):
        # FIXME: use the ArticleRepository
        return ArticleData.query.filter_by(type=ArticleType.Headline, published=True).first()

    def find_current_poll(self):
        return queries.get_all_enabled_polls().first()


class HomeBlock(object):
    # FIXME: we need this wrapper block for rounded corners ATM, otherwise
    #        the blocks should not be wrapped but inherited from this one
    def __init__(self, id, content, rounded=True):
        super(HomeBlock, self).__init__()
        self.id = id
        self.rounded = rounded
        if isinstance(content, component.Component):
            self.content = content
        else:
            self.content = component.Component(content)


class Empty(object):
    def __init__(self, message=_L(u'No content yet')):
        self.message = message


class OngoingArticlesBox(object):
    def __init__(self, parent, max_items=None):
        event_management._register_listener(parent, self)
        self.articles = component.Component(ArticleBox(ArticleType.Ongoing, max_items))

    def view_launched_ideas(self):
        event_management._emit_signal(self, "VIEW_LAUNCHED_IDEAS")

    @property
    def launched_ideas_url(self):
        return get_url_service().expand_url(['launched-ideas'])


class EditoLink(object):
    pass


class ImprovementsLink(object):
    pass


class IdeasByDomain(object):
    def find_count_by_domain(self):
        return (session.query(DomainData.id, DomainData.label, func.count(IdeaData.id))
                       .join(DomainData.ideas)
                       .join(IdeaData.wf_context)
                       .join(IdeaWFContextData.state)
                       .filter(StateData.label.in_(get_workflow().get_published_states()))
                       .group_by(DomainData.id)
                       .having(func.count(IdeaData.id) > 0)
                       .order_by(DomainData.rank, DomainData.label))


class IdeaCounter(object):

    def __init__(self, parent):
        event_management._register_listener(parent, self)

    def find_ideas_count(self):
        return IdeaRepository().get_by_workflow_state().count()

    @property
    def ideas_url(self):
        return get_url_service().expand_url(['ideas'])

    @property
    def submit_idea_url(self):
        return get_url_service().expand_url(['submit'])

    def with_login(self, action):
        event_management._emit_signal(self, "WITH_LOGIN", action)
