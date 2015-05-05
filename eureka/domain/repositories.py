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

from datetime import datetime, timedelta

from eureka.domain.models import (ArticleData, AuthorData, ChallengeData,
                                  CommentData, DomainData, EvalCommentData,
                                  HomeSettingsData, IdeaData,
                                  IdeaEvalContextData, IdeaWFContextData,
                                  ImprovementData, OrganizationData,
                                  OrganizationType, PointData, PollData,
                                  ReminderData, RoleData, RoleType, StateData,
                                  UserData, VoteCommentData, VoteIdeaData,
                                  WFCommentData)
from eureka.domain.services import get_workflow
from eureka.infrastructure.cache import cached
from eureka.infrastructure.users import get_default_users
from nagare.database import session
from sqlalchemy.orm import eagerload
from sqlalchemy.orm.query import aliased
from sqlalchemy.sql import func, union
from sqlalchemy.sql.expression import desc, or_

# Domain repositories as defined in http://domaindrivendesign.org/node/123
# No need to implement DAOs thanks to the ORM layer


class UserRepository(object):
    """
    Repository of users. Most of the time, we only want to query enabled users,
        so this is the default.
    But you can override the default by providing an 'enabled' keyword option.
    """
    # default users
    @property
    def innovator(self):
        return self.get_by_uid(get_default_users()['INNOVATOR'])

    @property
    def facilitator(self):
        return self.get_by_uid(get_default_users()['FACILITATOR'])

    @property
    def developer(self):
        return self.get_by_uid(get_default_users()['DEVELOPER'])

    @property
    def admin(self):
        return self.get_by_uid(get_default_users()['ADMIN'])

    @property
    def generic_user(self):
        return self.get_by_uid(get_default_users()['AUTHOR'])

    @property
    def protected_accounts(self):
        return (
            self.innovator, self.facilitator, self.developer,
            self.admin, self.generic_user
        )

    def create(self, **kw):
        return UserData(**kw)

    def get_by_uid(self, uid):
        return UserData.get_by_uid(uid)

    def get_by_email(self, email):
        if email is None:
            return None
        return UserData.get_by(email=email)

    def get_by_emails(self, emails):
        return self._query().filter(UserData.email.in_(emails))

    def _query(self):
        return UserData.query

    def get_all(self):
        return self._query()

    def _filter_by_enabled(self, query, enabled):
        return UserData._filter_by_enabled(query, enabled)

    def get_enabled(self):
        q = self._query()
        return self._filter_by_enabled(q, True)

    def get_active(self):
        return self.get_enabled().filter(
            UserData.last_connection_date != None
        )

    def get_by_uids(self, uids):
        return self._query().filter(
            UserData.uid.in_(uids))

    def get_by_role(self, role_type, enabled=True):
        return UserData.get_by_role(role_type, enabled)

    def get_facilitators(self, enabled=True):
        return UserData.get_facilitators(enabled)

    def get_developers(self, enabled=True):
        return self.get_by_role(RoleType.Developer, enabled)

    def get_users_with_pending_messages(self):
        return self._query().join(UserData.pending_email_messages)

    def get_by_profile_modification_date(self, before_date=None,
                                         after_date=None):
        q = self._query()
        if before_date:
            q = q.filter(UserData.profile_modification_date < before_date)
        if after_date:
            q = q.filter(UserData.profile_modification_date > after_date)
        return q

    @cached
    def get_by_organization(self, corporation=None, direction=None,
                            service=None, site=None, subsite=None,
                            enabled=True):
        def tr(label):
            return label.replace('*', '%')

        q = self._query()
        if corporation:
            corporation_alias = aliased(OrganizationData)
            q = q.join((corporation_alias, UserData.corporation)).filter(
                corporation_alias.label.like(tr(corporation)))
        if direction:
            direction_alias = aliased(OrganizationData)
            q = q.join((direction_alias, UserData.direction)).filter(
                direction_alias.label.like(tr(direction)))
        if service:
            service_alias = aliased(OrganizationData)
            q = q.join((service_alias, UserData.service)).filter(
                service_alias.label.like(tr(service)))
        if site:
            site_alias = aliased(OrganizationData)
            q = q.join((site_alias, UserData.site)).filter(
                site_alias.label.like(tr(site)))

        if subsite:
            subsite_alias = aliased(OrganizationData)
            q = q.join((subsite_alias, UserData.subsite)).filter(
                subsite_alias.label.like(tr(site)))

        return self._filter_by_enabled(q, enabled)

    def ensure_generic_user(self):
        """Create the default generic user if missing"""
        if not self.generic_user:
            self.create(**{'uid': u'auteur',
                           'email': u'auteur@pagesjaunes.fr',
                           'firstname': u'Auteur',
                           'lastname': u'Eureka',
                           'position': u'',
                           'password': u'auteureureka2014',
                           'enabled': True,
                           'fi': self.facilitator})

    def delete(self, uid):
        self.ensure_generic_user()
        user_to_delete = self.get_by_uid(uid)
        if not user_to_delete:
            return False

        # Idea submission
        for i in IdeaData.query.filter_by(submitted_by=user_to_delete).all():
            i.submitted_by = self.generic_user
        for i in IdeaData.query.filter_by(proxy_submitter=user_to_delete).all():
            i.proxy_submitter = self.generic_user

        # Idea authors
        for idea in user_to_delete.ideas_as_author:
            authors = list(idea.authors)
            if self.generic_user in authors:
                authors.remove(user_to_delete)
            else:
                idx = authors.index(user_to_delete)
                authors[idx] = self.generic_user
            idea.authors = authors
        user_to_delete.ideas_as_author = []

        # FI for other users
        for u in UserData.query.filter_by(fi=user_to_delete).all():
            u.fi = self.facilitator
        # user_to_delete.fi_for = []

        PointData.query.filter_by(user=user_to_delete).delete()

        # DI/FI ideas
        for wfcontext in IdeaWFContextData.query.filter_by(assignated_fi=user_to_delete).all():
            wfcontext.assignated_fi = self.facilitator
        for wfcontext in IdeaWFContextData.query.filter_by(assignated_di=user_to_delete).all():
            wfcontext.assignated_di = self.developer

        # Delete read ideas
        for read_idea in user_to_delete.read_ideas_association:
            session.delete(read_idea)
        user_to_delete.read_ideas_association = []

        # Votes for ideas
        for vote in VoteIdeaData.query.filter_by(user=user_to_delete).all():
            vote.user = self.generic_user

        # Votes for comments
        comments = set(e.comment for e in self.generic_user.votes_for_comments)
        for vote in user_to_delete.votes_for_comments:
            if vote.comment in comments:
                session.delete(vote)
            else:
                vote.user = self.generic_user
                comments.add(vote.comment)
        user_to_delete.votes_for_comments = []

        # Comments
        for e in CommentData.query.filter_by(created_by=user_to_delete).all():
            e.created_by = self.generic_user
        user_to_delete.comments = []

        # Votes for polls
        # Only one choice allowed per user and per poll, we need to check that
        choices = set(e.choice for e in self.generic_user.votes_for_polls)
        for vote in user_to_delete.votes_for_polls:
            if vote.choice in choices:
                session.delete(vote)
            else:
                vote.user = self.generic_user
                choices.add(vote.choice)
        user_to_delete.votes_for_polls = []

        # Tracked ideas
        ideas = list(set(self.generic_user.tracked_ideas) | set(user_to_delete.tracked_ideas))
        user_to_delete.tracked_ideas = []
        self.generic_user.tracked_ideas = ideas

        # DI for challenges
        self.generic_user.di_for_challenges = list(set(self.generic_user.di_for_challenges) | set(user_to_delete.di_for_challenges))
        user_to_delete.di_for_challenges = []

        for e in ChallengeData.query.filter_by(created_by=user_to_delete).all():
            e.created_by = self.generic_user

        # Domains
        self.developer.managed_domains = list(set(self.developer.managed_domains) | set(user_to_delete.managed_domains))
        user_to_delete.managed_domains = []

        # Comments in ideas' evaluation contexts
        for e in EvalCommentData.query.filter_by(created_by=user_to_delete):
            e.created_by = self.generic_user
        for e in EvalCommentData.query.filter_by(expert=user_to_delete):
            e.expert = self.generic_user

        # Workflow comments
        for e in WFCommentData.query.filter_by(created_by=user_to_delete):
            e.created_by = self.generic_user

        # Improvements
        for e in ImprovementData.query.filter_by(user=user_to_delete):
            e.user = self.generic_user

        # Delete photo
        user_to_delete._change_photo(None)

        # Home settings
        if user_to_delete._home_settings:
            # We need to manually delete the rows found in the ManyToMany tables used for domains and user filters
            # A better way would be to use cascade deletion
            user_to_delete._home_settings.domains = []
            user_to_delete._home_settings.users_filter = []
            session.delete(user_to_delete._home_settings)
            HomeSettingsData.query.filter_by(user=user_to_delete).delete()
            session.flush()

        session.delete(user_to_delete)


# FIXME: remove all _get_by_query calls (double check there's no problem with iterators/lists)
class IdeaRepository(object):
    """
    Repository of ideas. Provide ways to query the ideas according to some criteria.
    """

    def _query(self):
        return (IdeaData.query
                .join(IdeaData.wf_context)
                .join(IdeaWFContextData.state)
                .order_by(desc(IdeaWFContextData.publication_date)))

    def create(self, title, description, impact, submitted_by, domain,
               challenge=None, tags=None, submission_date=None, **kw):
        # FIXME: this code should be the default constructor of the IdeaData
        idea = IdeaData(**kw)
        idea.title = title
        idea.description = description
        idea.impact = impact
        idea.submitted_by = submitted_by
        idea.domain = domain
        idea.challenge = challenge
        idea.tags = tags or []
        idea.submission_date = submission_date or datetime.now()
        idea.authors = [submitted_by]  # at least

        # initialize a workflow context
        #  FIXME: this code should be the default constructor of the IdeaWFContextData
        initial_state = StateData.get_by(
            label=get_workflow().WFStates.INITIAL_STATE)
        idea.wf_context = IdeaWFContextData()
        idea.wf_context.state = initial_state

        # initialize an evaluation context
        # FIXME: should be initialized at the moment when the idea is submitted (i.e. enters in the workflow...)
        idea.eval_context = IdeaEvalContextData()
        idea.eval_context.title = title
        idea.eval_context.description = description
        idea.eval_context.impact = impact

        return idea

    def get_all(self):
        return self._query()

    def _get_by_query(self,
                      query):  # allow future extensibility (wrapping, default filters, ...)
        return query.all()

    def get_by_id(self, id):
        return IdeaData.get(id)

    def get_assigned_to_facilitator(self, user):
        return (IdeaData.query
                .join(IdeaData.wf_context)
                .filter(IdeaWFContextData.assignated_fi_uid == user.uid)
                .order_by(desc(IdeaData.submission_date)))

    def get_assigned_to_developer(self, user):
        return (IdeaData.query
                .join(IdeaData.wf_context)
                .filter(IdeaWFContextData.assignated_di_uid == user.uid)
                .order_by(desc(IdeaData.submission_date)))

    def get_tracked_by(self, user):
        return self._query().join(IdeaData.tracked_by).filter(
            UserData.uid == user.uid)

    def get_published_ideas(self):
        return self.get_by_states(get_workflow().get_published_states())

    def get_by_workflow_state(self):
        return self.get_by_states(get_workflow().get_workflow_states())

    def get_launched_ideas(self):
        return self.get_by_states(get_workflow().get_launched_ideas_states())

    def get_by_states(self, states):
        return self.filter_by_states(self._query(), states)

    def filter_by_states(self, q, states):
        return q.filter(StateData.label.in_(states))

    def get_by_reminder_before_date(self, date, type=None):
        q = self._query().join(IdeaData.reminders).filter(
            ReminderData.date < date)
        if type is not None:
            q = q.filter(ReminderData.type == type)
        return self._get_by_query(q)

    def get_by_ids(self, idea_ids):
        return self._query().filter(
            IdeaData.id.in_(idea_ids))

    def get_by_challenges(self, challenges_ids):
        q = self.get_published_ideas()
        return q.filter(
            IdeaData.challenge_id.in_(challenges_ids))

    def get_by_keyword(self, keyword):
        q = self.get_published_ideas()
        return q.filter(or_(IdeaData.title.like('%%%s%%' % keyword),
                            IdeaData.description.like('%%%s%%' % keyword)))

    def get_by_period(self, period):
        now = datetime.now()
        q = self.get_published_ideas()
        return q.filter(
            IdeaData.submission_date > (now - timedelta(period)).date())

    def get_by_users(self, users):
        q = self.get_published_ideas()
        return q.outerjoin(AuthorData).join(
            (UserData, AuthorData.user)).filter(
            UserData.uid.in_([u.uid for u in users]))

    def get_published_ideas_with_success_states(self):
        workflow = get_workflow()
        states = list(set(workflow.get_published_states()).intersection(
            workflow.get_success_states()))
        return self.get_by_states(states)

    def get_progressing_ideas_with_success_states(self):
        workflow = get_workflow()
        states = list(set(workflow.get_progressing_ideas_states()).intersection(
            workflow.get_success_states()))
        return self.get_by_states(states)

    def get_challenges_ideas_with_success_states(self):
        q = self.get_published_ideas_with_success_states()
        return q.filter(IdeaData.challenge_id != None)

    def get_by_domains(self, domains_ids):
        q = self.get_published_ideas()
        return q.filter(
            IdeaData.domain_id.in_(domains_ids))

    def get_by_domains_with_success_states(self, domains_ids):
        q = self.get_published_ideas_with_success_states()
        return q.filter(
            IdeaData.domain_id.in_(domains_ids))

    def get_tracked_by_with_success_states(self, user):
        return self.filter_by_states(self.get_tracked_by(user),
                                     get_workflow().get_success_states())

    def get_by_home_settings(self, home_settings=None):
        queries = []

        if not home_settings:
            home_settings = HomeSettingsData(user=None,
                                             show_progressing_ideas=True,
                                             show_challenge_ideas=True,
                                             show_tracked_ideas=False)
            session.expunge(
                home_settings)  # don't commit this temporary object

        # populate the queries list
        if home_settings.show_progressing_ideas:
            progressing_ideas = self.get_progressing_ideas_with_success_states().order_by(
                None)
            queries.append(progressing_ideas)

        if home_settings.show_tracked_ideas:
            tracked_ideas = self.get_tracked_by_with_success_states(
                home_settings.user).order_by(None)
            queries.append(tracked_ideas)

        if home_settings.show_challenges_ideas:
            challenges_ideas = self.get_challenges_ideas_with_success_states().order_by(
                None)
            queries.append(challenges_ideas)

        if home_settings.domains:
            domains_ids = [domain.id for domain in home_settings.domains]
            domains_ideas = self.get_by_domains_with_success_states(
                domains_ids).order_by(None)
            queries.append(domains_ideas)

        # Create a query for keyword
        if home_settings.keyword_filter:
            queries.append(
                self.get_by_keyword(home_settings.keyword_filter).order_by(
                    None))

        # Create a query for followed users
        # self.get_by_users().order_by(None)
        if home_settings.users_filter:
            queries.append(
                self.get_by_users(home_settings.users_filter).order_by(None))

        # assemble the queries with unions
        if not queries:
            q = self.get_by_ids([])  # query that returns nothing
        elif len(queries) == 1:
            q = queries[0]
        else:
            q = queries[0].union(*queries[1:])

        if home_settings.period_filter:
            now = datetime.now()
            q = q.filter(IdeaData.submission_date > (
                now - timedelta(home_settings.period_filter)).date())

        return q

    def sort_by_publication_date(self, q):
        return q.join(IdeaData.wf_context).order_by(
            desc(IdeaWFContextData.publication_date))

    def sort_by_last_wf_comment_date(self, q):
        last_comments_dates = (session.query(IdeaData.id.label('idea_id'),
                                             func.max(
                                                 WFCommentData.submission_date).label(
                                                 'last_comment_date'))
                               .join(IdeaData.wf_context)
                               .join(IdeaWFContextData.comments)
                               .group_by(IdeaData.id)
                               .subquery())

        q = (q.filter(IdeaData.id == last_comments_dates.c.idea_id)
             .order_by(desc(last_comments_dates.c.last_comment_date)))

        return q


class OrganizationRepository(object):
    """
    Repository of (business) organizations
    """

    def _get_by_query(self, query):
        return query.all()

    def _get_organization_type(self, type):
        return OrganizationType.get_by(label=type)

    def _get_by_type(self, type, parent=None):
        org_type = self._get_organization_type(type)
        q = OrganizationData.query \
            .filter_by(type=org_type)
        if parent:
            q = q.filter_by(parent=parent)
        return self._get_by_query(q)


class VoteIdeaRepository(object):
    """
    Repository of votes for ideas
    """

    def _get_by_query(self,
                      query):  # allow future extensibility (wrapping, default filters, ...)
        return query.all()

    @cached
    def get_by_users(self, users):
        user_uids = [user.uid for user in users]
        q = VoteIdeaData.query \
            .filter(VoteIdeaData.user_uid.in_(user_uids)) \
            .options(eagerload(VoteIdeaData.idea),
                     eagerload(VoteIdeaData.user))
        return self._get_by_query(q)

    def get_all(self):
        return VoteIdeaData.query.options(eagerload(VoteIdeaData.idea),
                                          eagerload(VoteIdeaData.user)).all()


class CommentRepository(object):
    """
    Repository of comments
    """

    def _query(self):
        q = CommentData.query
        return q.options(eagerload(CommentData.idea),
                         eagerload(CommentData.created_by))

    def get_by_id(self, id):
        return CommentData.get(id)

    def get_by_after_date(self, date):
        return self._query().filter(CommentData.submission_date > date)

    @cached
    def get_by_users(self, users):
        user_uids = [user.uid for user in users]
        return self._query().filter(CommentData.created_by_uid.in_(user_uids))

    def get_all(self):
        return self._query()

    def get_most_voted_comments(self, before_date=datetime.now()):
        q = (self._query()
             .add_column(func.sum(VoteCommentData.rate).label('score'))
             .join(CommentData.votes)
             .filter(CommentData.submission_date < before_date)
             .group_by(CommentData.id)
             .order_by(desc('score')))

        return q


class ChallengeRepository(object):
    """
    Repository of challenges
    """

    def _query(self):
        return ChallengeData.query.order_by(
            desc(ChallengeData.starting_date))

    def get_all(self):
        return self._query()

    def create(self, *args, **kwargs):
        return ChallengeData(*args, **kwargs)

    def get_by_id(self, id):
        if id is None:
            return None
        return ChallengeData.get(id)

    def get_by_active_at_date(self, date=None):
        ref_date = date or datetime.now()
        return (self._query()
                .filter(ChallengeData.starting_date <= ref_date)
                .filter(ChallengeData.ending_date > ref_date))


class WFCommentRepository(object):
    def get_by_submission_after_date(self, after_date):
        query = (WFCommentData
                 .query
                 .join(WFCommentData.idea_wf)
                 .join(WFCommentData.from_state)
                 .join(WFCommentData.to_state)
                 .join(IdeaWFContextData.idea)
                 .filter(WFCommentData.submission_date > after_date))
        return query


class DomainRepository(object):
    def _query(self):
        return DomainData.query.order_by(DomainData.rank)

    def get_all(self):
        return self._query()

    def get_by_id(self, id):
        if id is None:
            return None
        return DomainData.get(id)

    def get_by_di(self, di):
        return self._query().join(DomainData.dis).filter(
            UserData.uid == di.uid)


class ArticleRepository(object):
    def _query(self):
        return ArticleData.query.order_by(
            ArticleData.rank)

    def get_all(self):
        return self._query()

    def get_by_id(self, id):
        if id is None:
            return None
        return ArticleData.get(id)

    def get_by_type(self, type):
        return self._query().filter_by(type=type)

    def with_mobile_content(self, query):
        return query.filter(func.length(ArticleData.mobile_content) > 0)

    def get_by_type_with_mobile_content(self, type):
        return self.with_mobile_content(self.get_by_type(type))

    def create(self, **kw):
        return ArticleData(**kw)


class PollRepository(object):
    """
    Repository of polls
    """

    def get_all(self):
        return PollData.query

    def get_by_id(self, id):
        if id is None:
            return None
        return PollData.get(id)

    def create(self, **kw):
        return PollData(**kw)
