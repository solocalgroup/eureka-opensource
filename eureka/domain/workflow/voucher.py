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

import peak.rules
from eureka.infrastructure.workflow.voucher import (
    _comment_points_by_date,
    _nb_comments_points_credited_today,
    _points_per_author,
    _remove_comment_event_should_remove_some_points,
    add_points, PointCategory,
    PointEvent, PointEventValues
)
from nagare import log


@peak.rules.when(add_points,
                 "point_event == PointEvent.FIRST_CONNECTION")
def add_points_first_connection(user, point_event, timestamp=None,
                                subject_id=None, **kwargs):
    user.add_points(
        PointCategory.FIRST_CONNECTION,
        nb_points=PointEventValues[point_event],
        timestamp=timestamp,
        subject_id=subject_id,
    )


@peak.rules.when(add_points,
                 "point_event == PointEvent.FIRST_CONNECTION_OF_THE_DAY")
def add_points_first_connection_of_the_day(user, point_event, timestamp=None,
                                           subject_id=None, **kwargs):
    user.add_points(
        PointCategory.FIRST_CONNECTION_OF_THE_DAY,
        nb_points=PointEventValues[point_event],
        timestamp=timestamp,
        subject_id=subject_id,
    )


@peak.rules.when(add_points, "point_event == PointEvent.VOTE")
def add_points_vote(user, point_event, timestamp=None, **kwargs):
    if user.nb_votes_this_day < 3:
        user.add_points(
            PointCategory.VOTE,
            nb_points=PointEventValues[point_event],
            timestamp=timestamp,
        )

    user.nb_votes_this_day += 1


@peak.rules.when(add_points, "point_event == PointEvent.ADD_COMMENT")
def add_points_add_comment(user, point_event, timestamp=None,
                           comment_id=None, **kwargs):
    # Feature: limit to 15 points per day and per user for comments
    # Since we have ADD_COMMENT and REMOVE_COMMENT events that change the bonus points
    # acquired for comments this day we must make sure that if a user has exceeded
    # today's limit and he removes some comments, we must not remove points for the
    # comments that did not credited some points to the user. In fact, we must count
    # the number N of comments that did not credit points (including the previous days),
    # and the N first REMOVE_COMMENT events should not remove points. So we should remember
    # the ADD_COMMENT events that credited 0 points, that why we call the user.add_points
    # with 0 points credit.

    # Max 2 points per day, 1 point per comment
    credited_today = _nb_comments_points_credited_today(user, timestamp)
    if credited_today < 2:
        points_credited = _comment_points_by_date(timestamp)
    else:
        points_credited = 0

    # Log it for further debugging
    log.info(
        "Comment added by %s (credited_today=%s, points_credited=%s)" % (
            user, credited_today, points_credited))

    user.add_points(
        PointCategory.ADD_COMMENT,
        nb_points=points_credited,
        timestamp=timestamp,
        subject_id=comment_id
    )


@peak.rules.when(add_points,
                 "point_event == PointEvent.REMOVE_COMMENT")
def add_points_remove_comment(user, point_event, timestamp=None,
                              comment_date=None, comment_id=None, **kwargs):
    from eureka.domain.models import PointData

    # TODO: implement the limit to 15 points per day per user
    # Feature: limit to 15 points per day and per user for comments
    #   (see comments for the ADD_COMMENT event handling)
    assert comment_date is not None

    # Try to find the added points when the comment was created
    pd = PointData.get_by(
        label=PointCategory.ADD_COMMENT,
        subject_id=comment_id
    )
    if pd is not None:
        points_removed = -pd.nb_points

    # Keep the old mechanism
    elif _remove_comment_event_should_remove_some_points(user, timestamp):
        points_removed = -_comment_points_by_date(comment_date)
    else:
        points_removed = 0

    reason = kwargs.get('reason', '')
    user.add_points(
        PointCategory.REMOVE_COMMENT,
        nb_points=points_removed,
        reason=reason,
        timestamp=timestamp,
        subject_id=comment_id
    )


@peak.rules.when(add_points,
                 "point_event == PointEvent.PUBLISH_IDEA")
def add_points_publish_idea(user, point_event, timestamp=None, **kwargs):
    idea = kwargs['idea']
    user.add_points(
        PointCategory.PUBLISH_IDEA,
        nb_points=_points_per_author(PointEventValues[point_event], idea),
        timestamp=timestamp
    )


@peak.rules.when(add_points,
                 "point_event == PointEvent.PUBLISH_CHALLENGE_FIRST_IDEA")
def add_points_publish_challenge_first_idea(user, point_event,
                                            timestamp=None, **kwargs):
    idea = kwargs['idea']
    user.add_points(
        PointCategory.PUBLISH_CHALLENGE_FIRST_IDEA,
        nb_points=_points_per_author(PointEventValues[point_event], idea),
        timestamp=timestamp)


@peak.rules.when(add_points, "point_event == PointEvent.APPROVAL")
def add_points_approval(user, point_event, timestamp=None, **kwargs):
    idea = kwargs['idea']
    user.add_points(
        PointCategory.APPROVAL,
        nb_points=_points_per_author(PointEventValues[point_event], idea),
        timestamp=timestamp
    )


@peak.rules.when(add_points, "point_event == PointEvent.SELECT_IDEA")
def add_points_select_idea(user, point_event, timestamp=None, **kwargs):
    idea = kwargs['idea']
    user.add_points(
        PointCategory.SELECTED_IDEA,
        nb_points=_points_per_author(PointEventValues[point_event], idea),
        timestamp=timestamp
    )


@peak.rules.when(add_points,
                 "point_event == PointEvent.SEND_PROJECT_IDEA")
def add_points_send_project_idea(user, point_event, timestamp=None, **kwargs):
    idea = kwargs['idea']
    user.add_points(
        PointCategory.PROJECT_IDEA,
        nb_points=_points_per_author(PointEventValues[point_event], idea),
        timestamp=timestamp
    )


@peak.rules.when(add_points,
                 "point_event == PointEvent.SEND_PROTOTYPE_IDEA")
def add_points_send_prototype_idea(user, point_event,
                                   timestamp=None, **kwargs):
    idea = kwargs['idea']
    user.add_points(
        PointCategory.PROTOTYPE_IDEA,
        nb_points=_points_per_author(PointEventValues[point_event], idea),
        timestamp=timestamp
    )


@peak.rules.when(add_points, "point_event == PointEvent.EXTEND_IDEA")
def add_points_extend_idea(user, point_event, timestamp=None, **kwargs):
    idea = kwargs['idea']
    user.add_points(
        PointCategory.EXTENDED_IDEA,
        nb_points=_points_per_author(PointEventValues[point_event], idea),
        timestamp=timestamp
    )


@peak.rules.when(add_points, "point_event == PointEvent.CHANGE_AVATAR")
def add_points_change_avatar(user, point_event, timestamp=None, **kwargs):
    if user.photo_date is None:
        user.add_points(
            PointCategory.CHANGED_AVATAR,
            nb_points=PointEventValues[point_event],
            timestamp=timestamp
        )
