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

from nagare import editor
from nagare.i18n import _

from eureka.domain.repositories import UserRepository
from eureka.infrastructure.workflow.voucher import PointCategory
from eureka.infrastructure import validators
from eureka.ui.common.yui2 import flashmessage


# FIXME: maybe we should pass through the voucher rules to add points
class PointsAdmin(editor.Editor):
    """User interface to assign points to some users"""
    def __init__(self):
        super(PointsAdmin, self).__init__(None)
        self._ActionList = (
            (PointCategory.GIFT_BOUGHT, _(u"Gift purchase"), -1),
            (PointCategory.OTHER_EXPENSE, _(u"Other expense"), -1),
            (PointCategory.BONUS_POINTS, _(u"Bonus points"), +1),
            (PointCategory.PENALTY_POINTS, _(u"Penalty points"), -1),
        )
        self.category = editor.Property(PointCategory.GIFT_BOUGHT)
        self.users_emails = editor.Property(u'').validate(validators.user_email_list)
        self.points = editor.Property(u'').validate(validators.positive_integer)
        self.reason = editor.Property(u'').validate(validators.non_empty_string)
        self.user_repository = UserRepository()

    def _find_sign(self, category):
        for id, _, sign in self._ActionList:
            if id == category:
                return sign

    def is_validated(self):
        return super(PointsAdmin, self).is_validated(('category', 'points', 'users_emails', 'reason'))

    def check_users_have_enough_points(self):
        emails = self.users_with_not_enough_points()
        if emails:
            msg = _(u'The following users do not have enough available points: %s') % ', '.join(emails)
            self.users_emails.error = msg

    def users_with_not_enough_points(self):
        if self._find_sign(self.category.value) > 0:
            return []

        emails = []
        for email in self.users_emails.value:
            user = self.user_repository.get_by_email(email)
            if user.available_points < self.points.value:
                emails.append(email)
        return emails

    def commit(self):
        if not self.is_validated():
            return False

        category = self.category.value
        sign = self._find_sign(category)
        nb_points = self.points.value * sign
        reason = self.reason.value
        for email in self.users_emails.value:
            user = self.user_repository.get_by_email(email)
            user.add_points(category, nb_points, reason=reason)

        flashmessage.set_flash(_(u'Modifications done'))
        return True
