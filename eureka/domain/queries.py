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

# FIXME: remove this module entirely - add corresponding repositories to organize the queries

from sqlalchemy.sql.expression import desc, column, literal, func, or_, and_, case

from nagare.database import session
from nagare import log

from eureka.domain.models import IdeaData, IdeaWFContextData, WFCommentData, CommentData, \
    PollData, PollChoiceData, VotePollData, RoleType, PointData
from eureka.domain.models import UserData, DomainData, RoleData
from eureka.domain.models import TagData
from eureka.domain.models import ReadIdeaData, StateData, StepData, AuthorData
from eureka.domain.models import OrganizationData, OrganizationType
from eureka.domain.services import get_workflow

from eureka.domain.services import get_search_engine
from eureka.infrastructure.cache import cached


# FIXME: remove lambdas in queries

# user related queries
def _query_active_users_by_email(email):
    q = session.query(UserData.email,
                      UserData.firstname + u" " + UserData.lastname)
    q = q.filter(UserData.enabled == True)
    q = q.filter(
        func.lower(UserData.email).like(u"%" + email.lower() + u"%"))
    return q


# used only with the autocomplete component
def search_users_fulltext(search_string, limit=None):
    # Filter enabled users
    q = session.query(UserData.email,
                      UserData.lastname + u" " + UserData.firstname) \
        .filter(UserData.enabled == True) \
        .order_by(UserData.lastname)

    search_string = search_string.strip()

    # Splitting words. We assert each word must be in the lastname or firstname
    name_clauses = []
    for s in search_string.split(' '):
        name_clauses.append(or_(UserData.lastname.like('%%%s%%' % s),
                                UserData.firstname.like('%%%s%%' % s)))

    q = q.filter(or_(UserData.email.like('%%%s%%' % search_string),
                     and_(*name_clauses)))

    return q.limit(limit) if limit else q


def search_dis_fulltext(search_string, limit=None):
    q = search_users_fulltext(search_string)
    q = q.join(UserData.roles).filter(RoleData.type == RoleType.Developer)
    if limit:
        q = q.limit(limit)
    return q


def get_active_users_by_email(email):
    return _query_active_users_by_email(email)


def get_active_dis_by_email(email):
    return _query_active_users_by_email(email).join(UserData.roles).filter(
        RoleData.type == RoleType.Developer)


def get_tags(tag_label):
    q = session.query(TagData.label, TagData.label)
    q = q.filter(
        func.lower(TagData.label).like(u"%" + tag_label.lower() + u"%"))
    return q


# poll related queries
def get_all_enabled_polls():
    return (PollData.query.filter(PollData.enabled == True)
            .order_by(desc(PollData.id)))


def get_poll(poll_id):
    return PollData.get(poll_id) if poll_id else None


def get_poll_responses(poll_id):
    return PollChoiceData.query.filter(
        PollChoiceData.question_id == poll_id
    ).order_by(PollChoiceData.id)


def get_poll_response(response_id):
    return PollChoiceData.get(response_id) if response_id else None


def get_votes_from_user(poll_id, user_uid):
    """
    Return the votes a user has given to a specific poll
    """
    return VotePollData.query \
        .join(VotePollData.response) \
        .filter(PollChoiceData.question_id == poll_id) \
        .filter(VotePollData.user_uid == user_uid)


def get_votes_count_per_response(poll_id):
    return session.query(PollChoiceData,
                         func.count(VotePollData.id).label('vote_count')) \
        .outerjoin(PollChoiceData.votes) \
        .filter(PollChoiceData.question_id == poll_id) \
        .group_by(PollChoiceData)


# search engine
def get_searched_ideas(pattern):
    """
    Returns an iterator on ideas containing a pattern
    """
    q = get_all_published_ideas_unordered().outerjoin(
        IdeaData.domain).outerjoin(IdeaData.tags)
    return get_search_results('idea', pattern, q,
                              IdeaData.id)


def get_search_results(type, pattern, query, id_field, max_results=200,
                       default_search_field='text'):
    ordered_ids = get_search_engine().search(type, pattern, rows=max_results,
                                             default_field=default_search_field)[
        0] if pattern else []

    # log the result of the search
    logger = log.get_logger('.' + __name__)
    logger.debug(
        'Search results of type %s for "%s" on search field "%s": %s'
        % (type, pattern, default_search_field, ordered_ids))

    query = query.filter(id_field.in_(ordered_ids))
    if ordered_ids:
        rank_mapping = [(id, rank) for rank, id in enumerate(ordered_ids)]
        query = query.order_by(case(value=id_field, whens=rank_mapping))

    return query


# ideas
def get_ideas_count_by_domain():
    return session.query(
        DomainData.id,
        DomainData.label,
        func.count(IdeaData.id)
    ).outerjoin(IdeaData).group_by(DomainData.id)


def get_ideas_count_by_di():
    WFStates = get_workflow().WFStates
    sub_query = (IdeaWFContextData.query.outerjoin(IdeaWFContextData.state)
                 .filter(StateData.label == WFStates.DI_APPRAISAL_STATE)
                 .subquery())

    return session.query(
        UserData,
        func.count(sub_query.c.id)
    ).filter(UserData.enabled == True) \
        .outerjoin((sub_query, sub_query.c.assignated_di_uid == UserData.uid)) \
        .join(RoleData) \
        .filter(RoleData.type == RoleType.Developer).group_by(UserData.uid)


# add last state change date?
def get_ideas_count_in_fi_baskets():
    fi_basket_states = get_workflow().get_fi_basket_states()
    query = session.query(UserData,
                          StateData,
                          func.count(IdeaWFContextData.id).label('count')) \
        .join(IdeaWFContextData.assignated_fi) \
        .join(IdeaWFContextData.state) \
        .filter(StateData.label.in_(fi_basket_states)) \
        .group_by(UserData.uid, StateData.id)
    return query


def get_ideas_count_by_step():
    q = session.query(
        StateData.label.label('state'),
        StepData.label.label('step'),
        func.count(IdeaWFContextData.id).label('count')
    ).outerjoin(StateData.state_for) \
        .outerjoin(StateData.step) \
        .group_by(StateData.label) \
        .order_by(StepData.rank, StateData.id)
    return q


def get_user_ideas_count(uid):
    return (lambda uid=uid:
            session.query(
                StateData.label.label('state'),
                func.count(IdeaWFContextData.id).label('count')
            ).outerjoin(StateData.state_for)
            .outerjoin(IdeaWFContextData.idea)
            .outerjoin(AuthorData)
            .join((UserData, AuthorData.user))
            .filter(UserData.uid == uid)
            .group_by(StateData.label))


def get_fi_ideas_count(uid):
    return (lambda uid=uid:
            session.query(
                StateData.label.label('state'),
                func.count(IdeaWFContextData.id).label('count')
            ).outerjoin(StateData.state_for)
            .filter(IdeaWFContextData.assignated_fi == UserData.query.filter(
                UserData.uid == uid).first())
            .filter(StateData.label.in_(get_workflow().get_fi_basket_states())).group_by(
                StateData.label))


def get_di_ideas_count(uid):
    return (lambda uid=uid:
            session.query(
                StateData.label.label('state'),
                func.count(IdeaWFContextData.id).label('count')
            ).outerjoin(StateData.state_for)
            .filter(IdeaWFContextData.assignated_di == UserData.query.filter(
                UserData.uid == uid).first())
            .filter(StateData.label.in_(get_workflow().get_di_basket_states()))
            .group_by(StateData.label))


def get_all_published_ideas():
    """
    Returns an iterator on published ideas
    """
    return get_all_published_ideas_unordered().order_by(
        desc(IdeaWFContextData.publication_date))


def get_all_ideas_unordered():
    """
    Returns an iterator on all ideas
    """
    q = (session.query(
        IdeaData.id.label('id'),
        IdeaWFContextData.publication_date.label('publication_date'),
        IdeaWFContextData.recommendation_date.label('recommendation_date'),
        StateData.label.label('state'),
        DomainData.id.label('domain_id'),
        IdeaData.total_readers.label('total_readers'),
        IdeaData.total_comments.label('total_comments'),
        IdeaData.total_votes.label('total_votes'),
        IdeaData.title.label('title'),
        IdeaData.description.label('description'),
        IdeaData.submission_date.label('submission_date'),
        IdeaData.challenge_id.label('challenge_id')))

    q = (q.join(IdeaData.wf_context)
         .join(IdeaData.domain)
         .join(IdeaWFContextData.state)
         .group_by(IdeaData.id))

    return q


def get_all_published_ideas_unordered(states=[]):
    """
    Returns an iterator on published ideas
    """
    if states:
        return get_all_ideas_unordered().filter(
            StateData.label.in_(states))
    else:
        return get_all_ideas_unordered().filter(
            StateData.label.in_(get_workflow().get_published_states()))


def get_di_ideas(uid):
    """
    Returns an iterator on developer affected ideas
    """
    return (lambda uid=uid:
            IdeaData.query.outerjoin(IdeaData.wf_context)
            .filter(IdeaWFContextData.assignated_di == UserData.query.filter(
                UserData.uid == uid).first())
            .order_by(desc(IdeaData.submission_date)))


def get_di_process_ideas(uid):
    """
    Returns an iterator on idea for developer current process
    """
    return (lambda uid=uid:
            IdeaData.query.outerjoin(IdeaData.wf_context)
            .outerjoin(IdeaWFContextData.state)
            .filter(and_(
                StateData.label == get_workflow().WFStates.DI_APPRAISAL_STATE,
                IdeaWFContextData.assignated_di == UserData.query.filter(
                    UserData.uid == uid).first()))
            .order_by(desc(IdeaData.submission_date)))


def get_di_ideas_with_state(uid, state):
    """
    Returns an iterator on developer affected ideas
    """
    return (lambda uid=uid:
            IdeaData.query.outerjoin(IdeaData.wf_context)
            .outerjoin(IdeaWFContextData.state)
            .filter(and_(
                StateData.label == state,
                IdeaWFContextData.assignated_di == UserData.query.filter(
                    UserData.uid == uid).first()))
            .order_by(desc(IdeaData.submission_date)))


def get_dsig_ideas(uid):
    """
    Returns an iterator on dsig ideas
    """
    return (lambda uid=uid: IdeaData.query.outerjoin(
        IdeaData.wf_context).order_by(desc(IdeaData.submission_date)))


def get_dsig_ideas_with_state(uid, state):
    """
    Returns an iterator on dsig ideas
    """
    return (lambda uid=uid:
            IdeaData.query.outerjoin(IdeaData.wf_context)
            .outerjoin(IdeaWFContextData.state)
            .filter(StateData.label == state)
            .order_by(desc(IdeaData.submission_date)))


def get_fi_ideas(uid):
    """
    Returns an iterator on facilitator affected ideas
    """
    return (lambda uid=uid:
            IdeaData.query.outerjoin(IdeaData.wf_context)
            .outerjoin(IdeaWFContextData.state)
            .filter(
                IdeaWFContextData.assignated_fi == UserData.query.filter(
                    UserData.uid == uid).first())
            .order_by(desc(IdeaData.submission_date)))


def get_fi_process_ideas(uid):
    """
    Returns an iterator on idea for facilitator current process
    """
    return (lambda uid=uid:
            IdeaData.query.join(IdeaData.wf_context)
            .outerjoin(IdeaWFContextData.state)
            .filter(and_(
                StateData.label == get_workflow().WFStates.FI_NORMALIZE_STATE,
                IdeaWFContextData.assignated_fi == UserData.query.filter(
                    UserData.uid == uid).first()))
            .order_by(desc(IdeaData.submission_date)))


def get_fi_ideas_with_state(uid, state):
    """
    Returns an iterator on facilitator affected ideas
    """
    return (lambda uid=uid:
            IdeaData.query.join(IdeaData.wf_context)
            .outerjoin(IdeaWFContextData.state)
            .filter(and_(
                StateData.label == state,
                IdeaWFContextData.assignated_fi == UserData.query.filter(
                    UserData.uid == uid).first()))
            .order_by(desc(IdeaData.submission_date)))


def get_all_user_ideas(uid):
    return get_all_ideas_unordered().outerjoin(AuthorData).join(
        (UserData, AuthorData.user)).filter(UserData.uid == uid)


def get_published_user_ideas(uid):
    return get_all_published_ideas_unordered().outerjoin(AuthorData).join(
        (UserData, AuthorData.user)).filter(UserData.uid == uid)


def get_all_user_ideas_with_state(uid, state):
    """
    Returns an iterator on all ideas of a user with a specific state
    """
    return (lambda uid=uid:
            IdeaData.query.outerjoin(IdeaData.wf_context)
            .outerjoin(IdeaWFContextData.state)
            .filter(StateData.label == state)
            .outerjoin(AuthorData)
            .join((UserData, AuthorData.user))
            .filter(UserData.uid == uid)
            .order_by(desc(IdeaData.submission_date)))


def get_published_tag_ideas(tag_label):
    """
    Returns an iterator on ideas of a certain Tag
    """
    return (lambda tag_label=tag_label:
            get_all_published_ideas_unordered().filter(
                IdeaData.tags.contains(TagData.query.filter(
                    TagData.label == tag_label).first())))


def get_published_challenge_ideas(challenge_id=None):
    """
    Returns an iterator on published ideas linked to a challenge
    """

    def create():
        q = get_all_published_ideas_unordered()

        if challenge_id:
            return q.filter(IdeaData.challenge_id == challenge_id)
        else:
            return q.filter(IdeaData.challenge != None)

    return create


def get_published_tags(limit):

    def query(limit=limit):
        q = session.query(
            TagData.label,
            func.count(IdeaData.id).label('ideas_count'))
        q = q.outerjoin(TagData.ideas)
        q = q.outerjoin(IdeaData.wf_context)
        q = q.outerjoin(IdeaWFContextData.state)
        q = q.filter(
            StateData.label.in_(get_workflow().get_published_states()))
        q = q.order_by(desc('ideas_count'))
        q = q.group_by(TagData.label)
        q = q.limit(limit)
        return q

    return query


def get_idea_published_tag(idea_id):
    tag_ids = [elt[0] for elt in
               session.query(TagData.id).outerjoin(TagData.ideas).filter(
                   IdeaData.id == idea_id)]

    result = (session.query(
        TagData.label,
        func.sum(StateData.label.in_(get_workflow().get_published_states())).label(
            'ideas_count')
    ).outerjoin(TagData.ideas))

    result = (result.outerjoin(IdeaData.wf_context)
              .outerjoin(IdeaWFContextData.state)
              .filter(TagData.id.in_(tag_ids))
              .group_by(TagData.label))

    return result


@cached
def get_org_type(name):
    return OrganizationType.get_by(label=name)


@cached
def get_org_label(org_id, org_type):
    # FIXME: why the orga id and orga type? orga id is already unique?!
    #        well, let's use both for the moment like it was before...
    return (session.query(OrganizationData.label)
            .filter_by(id=org_id, type=get_org_type(org_type))
            .scalar()) or u''


def get_corporation_label(corporation_id):
    return get_org_label(corporation_id, u'corporation')


def get_site_label(site_id):
    return get_org_label(site_id, u'site')


def get_direction_label(direction_id):
    return get_org_label(direction_id, u'direction')


def get_service_label(service_id):
    return get_org_label(service_id, u'service')


def get_dsig_basket_state_ideas():
    q = session.query(IdeaData.id) \
        .join(IdeaWFContextData) \
        .join(StateData) \
        .filter(StateData.label == get_workflow().WFStates.DSIG_BASKET_STATE)
    return q


def get_idea_events(event_filter=None):
    # get a mixture of Comments & comments sorted by submission_date
    q1 = session.query(WFCommentData.submission_date.label('date'),
                       UserData.uid.label('user_uid'),
                       StateData.label.label('event'),
                       IdeaData.id.label('idea_id'))
    q1 = q1.join(WFCommentData.to_state,
                 WFCommentData.created_by,
                 WFCommentData.idea_wf,
                 IdeaWFContextData.idea)

    q2 = session.query(CommentData.submission_date.label('date'),
                       UserData.uid.label('user_uid'),
                       literal(u'COMMENT').label('event'),
                       IdeaData.id.label('idea_id'))
    q2 = q2.join(CommentData.created_by, CommentData.idea,
                 IdeaData.wf_context, IdeaWFContextData.state)
    # mask comments for ideas that are not in a published state
    q2 = q2.filter(StateData.label.in_(get_workflow().get_published_states()))

    q = q1.union(q2)

    # mask ideas that are currently in the dsig_basket_state
    q = q.filter(~IdeaData.id.in_(get_dsig_basket_state_ideas()))

    if event_filter:
        q = q.filter(column('event').in_(event_filter))
    q = q.order_by(desc('date'))
    return q


def get_status_by_entity():
    result = {}

    # FIXME: use user.status_level instead of duplicating the levels scale
    q_users = (session.query(
        UserData.uid,
        UserData.corporation_id.label('corporation_id'),
        UserData.direction_id.label('direction_id'),
        func.sum(func.coalesce(PointData.nb_points, 0)).label('points')
    ).filter(or_(PointData.label == None, PointData.label != u'GIFT_BOUGHT')))

    q_users = (
        q_users.filter(UserData.enabled == True)
        .group_by(UserData.corporation_id, UserData.direction_id, UserData.uid)
        .outerjoin(UserData.points)
        .subquery())

    q = (session.query(q_users.c.corporation_id, q_users.c.direction_id,
                       func.count(q_users.c.uid).label('user_count'))
         .group_by(q_users.c.corporation_id, q_users.c.direction_id)
         .order_by(q_users.c.corporation_id, q_users.c.direction_id))

    q0 = q.filter(q_users.c.points == 0)

    for elt in q0:
        t = result.get((elt[0], elt[1]), {})
        t.update(status_level0=elt[2])
        result[(elt[0], elt[1])] = t

    q1 = q.filter(q_users.c.points > 0).filter(q_users.c.points <= 100)

    for elt in q1:
        t = result.get((elt[0], elt[1]), {})
        t.update(status_level1=elt[2])
        result[(elt[0], elt[1])] = t

    q2 = q.filter(q_users.c.points > 100).filter(q_users.c.points <= 200)

    for elt in q2:
        t = result.get((elt[0], elt[1]), {})
        t.update(status_level2=elt[2])
        result[(elt[0], elt[1])] = t

    q3 = q.filter(q_users.c.points > 200).filter(q_users.c.points <= 2000)

    for elt in q3:
        t = result.get((elt[0], elt[1]), {})
        t.update(status_level3=elt[2])
        result[(elt[0], elt[1])] = t

    q4 = q.filter(q_users.c.points > 2000).filter(q_users.c.points <= 10000)

    for elt in q4:
        t = result.get((elt[0], elt[1]), {})
        t.update(status_level4=elt[2])
        result[(elt[0], elt[1])] = t

    q5 = q.filter(q_users.c.points > 10000)

    for elt in q5:
        t = result.get((elt[0], elt[1]), {})
        t.update(status_level5=elt[2])
        result[(elt[0], elt[1])] = t

    return result
