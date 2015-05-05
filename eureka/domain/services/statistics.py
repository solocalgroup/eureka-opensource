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

import collections
import itertools

from eureka.domain.models import Unpicklable
from eureka.infrastructure.cache import cached

# Domain services as defined in http://domaindrivendesign.org/node/125


class UsersStatistics(Unpicklable):
    def __init__(self, nb_connected, total_ideas, nb_authors, total_votes,
                 nb_voters, total_comments, nb_commentators):
        from eureka.domain.repositories import (
            CommentRepository, IdeaRepository,
            UserRepository, VoteIdeaRepository
        )
        self.nb_connected = nb_connected
        self.total_ideas = total_ideas
        self.nb_authors = nb_authors
        self.total_votes = total_votes
        self.nb_voters = nb_voters
        self.total_comments = total_comments
        self.nb_commentators = nb_commentators


# Used for challenge filtering, because None value can be a correct value
NO_FILTER = object()


class StatisticsService(Unpicklable):
    """
    Service that compute statistics
    """

    def __init__(self):
        self.user_repository = UserRepository()
        self.idea_repository = IdeaRepository()
        self.vote_idea_repository = VoteIdeaRepository()
        self.comment_repository = CommentRepository()

    @cached
    def _active_users(self):
        # Users enabled and who have logged in at least once
        return set(self.user_repository.get_active())

    @cached
    def _votes(self):
        return set(self.vote_idea_repository.get_all())

    @cached
    def _votes_by_challenge(self):
        votes_by_challenge = collections.defaultdict(set)
        for k, v in itertools.groupby(
            self._votes(),
                lambda v: v.idea.challenge):
            votes_by_challenge[k].update(set(v))

        return votes_by_challenge

    @cached
    def _comments(self):
        return set(self.comment_repository.get_all())

    @cached
    def _comments_by_challenge(self):
        comments_by_challenge = collections.defaultdict(set)
        for k, v in itertools.groupby(
                self._comments(), lambda c: c.idea.challenge):
            comments_by_challenge[k].update(set(v))
        return comments_by_challenge

    @cached
    def _ideas(self):
        return set(self.idea_repository.get_published_ideas())

    @cached
    def _ideas_by_challenge(self):
        ideas_by_challenge = collections.defaultdict(set)
        for i in self._ideas():
            ideas_by_challenge[i.challenge].add(i)
        return ideas_by_challenge

    def get_users_statistics_on_connections(self, users, after_date=None):
        intersection = users.intersection(self._active_users())
        if after_date:
            return len([u for u in intersection
                        if u.last_connection_date > after_date])
        else:
            return len(intersection)

    def get_users_statistics_on_ideas(self, users, after_date=None,
                                      challenge=NO_FILTER):
        ideas = (
            self._ideas_by_challenge()[challenge]
            if challenge is not NO_FILTER
            else self._ideas()
        )
        ideas = set(i for i in ideas if not set(i.authors).isdisjoint(users))
        if after_date:
            ideas = [
                idea for idea in ideas
                if idea.wf_context.publication_date
                and idea.wf_context.publication_date > after_date
            ]
        unique_authors = set(
            author for idea in ideas
            for author in idea.authors
            if author in users
        )

        return len(ideas), len(unique_authors)

    def get_users_statistics_on_votes(self, users, after_date=None,
                                      challenge=NO_FILTER):
        votes = (
            self._votes_by_challenge()[challenge]
            if challenge is not NO_FILTER
            else self._votes()
        )
        votes = set(v for v in votes if v.user in users)
        if after_date:
            votes = set(
                v for v in votes
                if v.timestamp and v.timestamp > after_date
            )
        unique_voters = set(vote.user for vote in votes)

        return len(votes), len(unique_voters)

    def get_users_statistics_on_comments(self, users, after_date=None,
                                         challenge=NO_FILTER):
        comments = (
            self._comments_by_challenge()[challenge]
            if challenge is not NO_FILTER
            else self._comments()
        )
        if after_date:
            comments = set(
                c for c in comments
                if c.submission_date and c.submission_date > after_date
            )
        comments = set(c for c in comments if c.created_by in users)
        unique_commentators = set(comment.created_by for comment in comments)
        return len(comments), len(unique_commentators)

    def get_users_statistics(self, users, after_date=None,
                             challenge=NO_FILTER):
        """
        Compute various statistics for a given group of users,
        returns an instance of UsersStatistics
        """
        users = set(users)
        # first connections
        nb_connected_users = self.get_users_statistics_on_connections(
            users, after_date
        )
        # ideas
        total_ideas, nb_authors = self.get_users_statistics_on_ideas(
            users, after_date, challenge
        )
        # votes
        total_votes, nb_voters = self.get_users_statistics_on_votes(
            users, after_date, challenge
        )
        # comments
        total_comments, nb_commentators = (
            self.get_users_statistics_on_comments(users, after_date, challenge)
        )

        return UsersStatistics(
            nb_connected=nb_connected_users,
            total_ideas=total_ideas,
            nb_authors=nb_authors,
            total_votes=total_votes,
            nb_voters=nb_voters,
            total_comments=total_comments,
            nb_commentators=nb_commentators,
        )

    def get_users_points_statistics(self, users):
        """Compute statistics on users points"""
        statistics = {}
        users_status_levels = [
            (user, user.status_level_label)
            for user in users if user
        ]
        for user, level in users_status_levels:
            statistics.setdefault(level, []).append(user)

        return statistics
