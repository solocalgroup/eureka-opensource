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

from nagare import security, editor, validator
from nagare.i18n import _

from eureka.domain.models import CommentData, AttachmentData
from eureka.infrastructure.urls import get_url_service
from eureka.infrastructure import event_management
from eureka.infrastructure.tools import is_integer, fix_filename
from eureka.infrastructure.security import get_current_user
from eureka.infrastructure.validators import non_empty_string
from eureka.ui.common.yui2 import flashmessage
from eureka.ui.desktop.attachment import validate_attachment
from eureka.domain.repositories import IdeaRepository
from eureka.domain import mail_notification


class Comment(object):
    def __init__(self, comment):
        super(Comment, self).__init__()
        self.id = comment if is_integer(comment) else comment.id
        self.reset()

    def reset(self):
        self.delete_reason = editor.Property('').validate(lambda v: validator.StringValidator(v).shorter_or_equal_than(150, _(u"Length must be shorter or equal than %(max)d characters")))
        self.show_delete_form = editor.Property(False)

    @property
    def comment(self):
        return CommentData.get(self.id)

    def has_vote(self):
        current_user = get_current_user()
        if current_user:
            return self.comment.find_vote_from_user(current_user) is not None
        else:
            return False

    def add_vote(self):
        self.comment.add_vote_for_user(get_current_user())

    def remove_vote(self):
        vote = self.comment.find_vote_from_user(get_current_user())
        self.comment.votes.remove(vote)

    @property
    def voters(self):
        return [vote.user for vote in self.comment.votes]

    def delete(self):
        if not self.delete_reason.error:
            comment = self.comment
            idea = comment.idea
            idea.remove_comment(comment, reason=self.delete_reason.value)
            event_management._emit_signal(self, "DELETE_COMMENT")
            return True

    def moderate(self):
        self.comment.moderated = True
        # FIXME: the moderation mail should be sent from a CommentData method, not from here
        self.send_moderation_mail(get_current_user())

    def cancel_moderation(self):
        self.comment.moderated = False

    def send_moderation_mail(self, from_user):
        mail_notification.send('mail-moderation.html',
                               to=None,
                               moderation_user=from_user.email,
                               moderation_user_firstname=from_user.firstname,
                               moderation_user_lastname=from_user.lastname,
                               idea=self.comment.idea,
                               comment=self.comment.content,
                               delivery_priority=mail_notification.DeliveryPriority.Low)

    def get_url(self):
        return get_url_service().expand_url(['idea', '%d#comment%d' % (self.comment.idea.id, self.comment.id)])

    def goto_user(self, user_uid):
        event_management._emit_signal(self, "VIEW_USER_PROFILE",
                                      user_uid=user_uid)


class CommentCreator(editor.Editor):
    def __init__(self, parent, idea):
        event_management._register_listener(parent, self)
        self.idea_id = idea if is_integer(idea) else idea.id
        self.reset()

    @property
    def idea(self):
        return IdeaRepository().get_by_id(self.idea_id)

    def reset(self):
        self.content = editor.Property(u'').validate(non_empty_string)
        self.attachment = editor.Property(None).validate(validate_attachment)

    def is_valid(self):
        return super(CommentCreator, self).is_validated(('content', 'attachment'))

    def create_attachment(self, uploaded_file):
        if not uploaded_file:
            return None

        return AttachmentData(filename=fix_filename(uploaded_file['filename']),
                              mimetype=uploaded_file['content_type'],
                              data=uploaded_file['filedata'])

    def create_comment(self):
        if not self.is_valid():
            return None

        # create the comment
        idea = self.idea
        content = self.content.value
        user = get_current_user()
        attachment = self.create_attachment(self.attachment.value)
        comment = idea.add_comment(user, content, attachment)

        # clear fields
        self.reset()

        flashmessage.set_flash(_(u'Comment added'))
        return comment

    def with_login(self, action):
        event_management._emit_signal(self, 'WITH_LOGIN', action)
