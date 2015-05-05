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

from eureka.infrastructure.security import Rules
from .comp import Suggestion  # @UnusedImport - needed for peak-rules
from .pager import SuggestionsPager  # @UnusedImport - needed for peak-rules


@peak.rules.when(Rules.has_permission, "perm == 'view_masked_suggestions' and isinstance(subject, SuggestionsPager)")
def has_permission_view_masked_suggestions_pager(self, user, perm, subject):
    if not user:
        return False

    return user.entity.is_dsig()


@peak.rules.when(Rules.has_permission, "perm == 'edit' and isinstance(subject, Suggestion)")
def has_permission_edit_suggestion(self, user, perm, subject):
    if not user:
        return False

    return user.entity.is_dsig()
