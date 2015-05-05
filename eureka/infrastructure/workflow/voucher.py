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

from datetime import datetime
from collections import defaultdict
import math

from nagare.i18n import _

from eureka.infrastructure.tools import Enum
from argparse import Namespace


# FIXME: these constants should be declared in the domain.models module instead

class PointEvent(Enum):
    FIRST_CONNECTION = u"FIRST_CONNECTION"
    FIRST_CONNECTION_OF_THE_DAY = u"FIRST_CONNECTION_OF_THE_DAY"
    VOTE = u"VOTE"
    ADD_COMMENT = u"ADD_COMMENT"
    REMOVE_COMMENT = u"REMOVE_COMMENT"
    PUBLISH_IDEA = u"PUBLISH_IDEA"
    PUBLISH_CHALLENGE_FIRST_IDEA = u"PUBLISH_CHALLENGE_FIRST_IDEA"
    APPROVAL = u"APPROVAL"
    START_IMPLEMENTATION = u"START_IMPLEMENTATION"
    CHANGE_AVATAR = u"CHANGE_AVATAR"
    SUBMIT_IDEA = u"SUBMIT_IDEA"
    SELECT_IDEA = u"SELECT_IDEA"
    SEND_PROJECT_IDEA = u"SEND_PROJECT_IDEA"
    SEND_PROTOTYPE_IDEA = u"SEND_PROTOTYPE_IDEA"
    EXTEND_IDEA = u"EXTEND_IDEA"


class PointCategory(Enum):
    FIRST_CONNECTION = u'FIRST_CONNECTION'
    FIRST_CONNECTION_OF_THE_DAY = u'FIRST_CONNECTION_OF_THE_DAY'
    VOTE = u'VOTE'
    ADD_COMMENT = u'ADD_COMMENT'
    REMOVE_COMMENT = u'REMOVE_COMMENT'
    SUBMIT_IDEA = u'SUBMIT_IDEA'
    PUBLISH_IDEA = u'PUBLISH_IDEA'
    PUBLISH_CHALLENGE_FIRST_IDEA = u'PUBLISH_CHALLENGE_FIRST_IDEA'
    APPROVAL = u'APPROVAL'
    SELECTED_IDEA = u'SELECTED_IDEA'
    PROJECT_IDEA = u'PROJECT_IDEA'
    PROTOTYPE_IDEA = u'PROTOTYPE_IDEA'
    EXTENDED_IDEA = u'EXTENDED_IDEA'
    CHANGED_AVATAR = u'CHANGED_AVATAR'
    CHALLENGE_BONUS = u'CHALLENGE_BONUS'
    POINT_SCALE_CHANGE = u'POINT_SCALE_CHANGE'
    BONUS_POINTS = u'BONUS_POINTS'
    PENALTY_POINTS = u'PENALTY_POINTS'
    GIFT_BOUGHT = u'GIFT_BOUGHT'
    OTHER_EXPENSE = u'OTHER_EXPENSE'


PointCategoryLabels = {
    PointCategory.FIRST_CONNECTION: _("FIRST_CONNECTION"),
    PointCategory.FIRST_CONNECTION_OF_THE_DAY: _("FIRST_CONNECTION_OF_THE_DAY"),
    PointCategory.VOTE: _("VOTE"),
    PointCategory.ADD_COMMENT: _("ADD_COMMENT"),
    PointCategory.REMOVE_COMMENT: _("REMOVE_COMMENT"),
    PointCategory.SUBMIT_IDEA: _("SUBMIT_IDEA"),
    PointCategory.PUBLISH_IDEA: _("PUBLISH_IDEA"),
    PointCategory.PUBLISH_CHALLENGE_FIRST_IDEA: _("PUBLISH_CHALLENGE_FIRST_IDEA"),
    PointCategory.APPROVAL: _("APPROVAL"),
    PointCategory.SELECTED_IDEA: _("SELECTED_IDEA"),
    PointCategory.PROJECT_IDEA: _("PROJECT_IDEA"),
    PointCategory.PROTOTYPE_IDEA: _("PROTOTYPE_IDEA"),
    PointCategory.EXTENDED_IDEA: _("EXTENDED_IDEA"),
    PointCategory.CHANGED_AVATAR: _("CHANGED_AVATAR"),
    PointCategory.CHALLENGE_BONUS: _("CHALLENGE_BONUS"),
    PointCategory.POINT_SCALE_CHANGE: _("POINT_SCALE_CHANGE"),
    PointCategory.BONUS_POINTS: _("BONUS_POINTS"),
    PointCategory.PENALTY_POINTS: _("PENALTY_POINTS"),
    PointCategory.GIFT_BOUGHT: _("GIFT_BOUGHT"),
    PointCategory.OTHER_EXPENSE: _("OTHER_EXPENSE"),
}


spec = {
    'first_connection': 'integer(default=1, min=0)',
    'first_connection_of_the_day': 'integer(default=1, min=0)',
    'vote': 'integer(default=1, min=0)',
    'add_comment': 'integer(default=1, min=0)',
    'publish_idea': 'integer(default=10, min=0)',
    'publish_challenge_first_idea': 'integer(default=50, min=0)',
    'approval': 'integer(default=20, min=0)',
    'change_avatar': 'integer(default=5, min=0)',
    'select_idea': 'integer(default=100, min=0)',
    'send_project_idea': 'integer(default=200, min=0)',
    'send_prototype_idea': 'integer(default=300, min=0)',
    'extend_idea': 'integer(default=500, min=0)',
}


PointEventValues = dict()


def configure(config):
    """Sets up the number of points awarded for possible event"""
    PointEventValues.update({k.upper(): v for k, v in config.iteritems()})


def get_acquired_point_categories():
    return (
        PointCategory.CHALLENGE_BONUS,
        PointCategory.EXTENDED_IDEA,
        PointCategory.PROTOTYPE_IDEA,
        PointCategory.PROJECT_IDEA,
        PointCategory.SELECTED_IDEA,
        PointCategory.POINT_SCALE_CHANGE,
        PointCategory.CHANGED_AVATAR,
        PointCategory.PUBLISH_CHALLENGE_FIRST_IDEA,
        PointCategory.APPROVAL,
        PointCategory.SUBMIT_IDEA,
        PointCategory.PUBLISH_IDEA,
        PointCategory.ADD_COMMENT,
        PointCategory.REMOVE_COMMENT,
        PointCategory.FIRST_CONNECTION,
        PointCategory.VOTE,
        PointCategory.FIRST_CONNECTION_OF_THE_DAY,
        PointCategory.BONUS_POINTS,
        PointCategory.PENALTY_POINTS,
    )


def get_sorted_spent_point_categories():
    return (
        PointCategory.GIFT_BOUGHT,
        PointCategory.OTHER_EXPENSE,
    )


def get_manual_point_categories():
    """Points that can be handled manually in the points admin"""
    return (
        PointCategory.GIFT_BOUGHT,
        PointCategory.OTHER_EXPENSE,
        PointCategory.BONUS_POINTS,
        PointCategory.PENALTY_POINTS
    )


def _nb_comments_points_credited_today(user, timestamp):
    timestamp = timestamp or datetime.now()
    from_ = datetime(timestamp.year, timestamp.month, timestamp.day, 0, 0, 0)
    to_ = datetime(timestamp.year, timestamp.month, timestamp.day, 23, 59, 59)
    points = user.get_points(PointCategory.ADD_COMMENT, from_date=from_, to_date=to_)  # up to now
# points.extend(user.get_points(PointCategory.REMOVE_COMMENT, from_date=timestamp.date(), to_date=timestamp))  # up to now
    return sum(point.nb_points for point in points)


def _remove_comment_event_should_remove_some_points(user, timestamp):
    # we should start to remove points when the number of ADD_COMMENT events that credited 0 points is equal to the
    # number of REMOVE_COMMENT events that removed 0 points (to cancel ADD_COMMENT no-credit events)
    timestamp = timestamp or datetime.now()
    credited_0 = len([point for point in user.get_points(PointCategory.ADD_COMMENT, to_date=timestamp) if point.nb_points == 0])
    debited_0 = len([point for point in user.get_points(PointCategory.REMOVE_COMMENT, to_date=timestamp) if point.nb_points == 0])
    return credited_0 == debited_0


def _comment_points_by_date(d):
    d = d or datetime.now()
    if d <= datetime(2010, 10, 11, 23, 59, 59):
        # Before oct 11th, 2010 each comment = 5 pts
        return 5
    elif d <= datetime(2011, 3, 28, 23, 59, 59):
        # Before march 28th, 2011 each comment = 2 pts
        return 2
    else:
        # Now each comment = 1pt by default (configurable)
        return PointEventValues[PointEvent.ADD_COMMENT]


def _points_per_author(total_points, idea):
    """Share the total points between the authors of the idea, return the number of points to give to each author"""
    return int(math.ceil(float(total_points) / len(idea.authors)))


def add_points(user, point_event, timestamp=None, **kwargs):
    """In:
      - `user` -- a user data to give point
      - `point_event` -- name of event
      - `timestamp` -- the eventual custom timestamp of the point, defaults
                       to `datetime.now()` otherwise
    """
    pass
