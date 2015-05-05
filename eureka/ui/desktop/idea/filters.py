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

import datetime
from eureka.domain.models import IdeaData, IdeaWFContextData, StateData


class IdeaFilter(object):
    """ The base Idea query filter """

    def __init__(self, name, title):
        self.name = name
        self.title = title

    def apply(self, q):
        """ Subclass must implement this method """
        raise NotImplementedError()


class IdeaDateFilter(IdeaFilter):
    """ A filter that checks an idea matches a maximum age """

    def __init__(self, name, title, wf_field, max_age):
        super(IdeaDateFilter, self).__init__(name, title)
        self.wf_field = wf_field
        self.max_age = max_age

    def apply(self, q):
        field = getattr(IdeaWFContextData, self.wf_field)
        dt = datetime.datetime.now() - datetime.timedelta(days=self.max_age)
        return q.filter(field >= dt)


class IdeaStateFilter(IdeaFilter):
    """Filter ideas that have one of the allowed state"""

    def __init__(self, name, title, allowed_states):
        super(IdeaStateFilter, self).__init__(name, title)
        self.allowed_states = allowed_states

    def apply(self, q):
        return q.filter(StateData.label.in_(self.allowed_states))


class IdeaChallengeFilter(IdeaFilter):
    """A filter that checks an idea is from a given challenge (or outside of a challenge when challenge_id is None)"""
    def __init__(self, name, title, challenge_id=None):
        super(IdeaChallengeFilter, self).__init__(name, title)
        self.challenge_id = challenge_id

    def apply(self, q):
        return q.filter(IdeaData.challenge_id == self.challenge_id)


class IdeaDomainFilter(IdeaFilter):
    """A filter that checks an idea is in a given domain"""
    def __init__(self, name, title, domain_id):
        super(IdeaDomainFilter, self).__init__(name, title)
        self.domain_id = domain_id

    def apply(self, q):
        return q.filter(IdeaData.domain_id == self.domain_id)


class IdeaNoFilter(IdeaFilter):
    """ An idea filter that implements the null pattern (no filtering) """

    def __init__(self):
        super(IdeaNoFilter, self).__init__(u'no_filter', 'No Filter')

    def apply(self, q):
        return q
