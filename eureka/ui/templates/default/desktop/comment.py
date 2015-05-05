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

from nagare import presentation, component, security
from nagare.i18n import _, format_datetime

from eureka.domain.models import attachments_max_size
from eureka.domain.repositories import UserRepository
from eureka.infrastructure.tools import text_to_html_elements
from eureka.ui.common.yui2 import ModalBox
from eureka.ui.common.yui2 import FlashMessage
from eureka.ui.desktop.attachment import Attachment
from eureka.ui.desktop.user import User, UserPager

from eureka.ui.desktop.comment import Comment, CommentCreator, CommentPager


class AsyncWrapper(object):
    def __init__(self, comp):
        self.inner_comp = comp


@presentation.render_for(AsyncWrapper)
def render_aysnc_wrapper(self, h, comp, *args):
    async = h.AsyncRenderer()
    h << self.inner_comp.render(async)
    return h.root


@presentation.render_for(Comment)
def render_comment(self, h, comp, *args):
    voters = self.voters
    voters_uids = [voter.uid for voter in voters]

    pager = UserPager(self, lambda uids=voters_uids: UserRepository().get_by_uids(uids))
    relevant_comment_users_dialog = component.Component(ModalBox(AsyncWrapper(component.Component(pager, model='minimal')),
                                                                 title=_(u'Users finding this comment relevant'),
                                                                 visible=False))

    with h.li:
        h << h.a(name='comment%s' % self.id)  # so we can navigate to comments
        sync = h.SyncRenderer()
        h << relevant_comment_users_dialog.render(sync)
        with h.div(class_='user'):
            # creator avatar
            h << component.Component(User(self, self.comment.created_by)).render(sync, model='avatar100')
        if voters:
            with h.div(class_='alert'):
                nb_voters = len(voters_uids)
                if nb_voters > 1:
                    message = _(u"%s people find this comment relevant") % nb_voters
                else:
                    message = _(u"One people find this comment relevant")

                h << h.a(message,
                         title=message,
                         href='javascript:' + relevant_comment_users_dialog().show_js(),
                         class_='votes')
        with h.div(class_='author'):
            # author
            h << _(u"From") << " "
            h << comp.render(sync, model='author') << " "

            # date
            if self.comment.submission_date:  # deal with missing dates in the database
                h << _(u'on') << " "
                with h.span(class_='date'):
                    h << format_datetime(self.comment.submission_date)
                h << " "
        h << h.p(text_to_html_elements(h, self.comment.content))

        # attachment
        if self.comment.attachment:
            with h.p:
                h << component.Component(Attachment(self.comment.attachment)).render(h)

        with h.div(class_='links'):
            h << comp.render(h, model='actions')

        # delete form
        h << comp.render(h, model='delete_form')

    return h.root


@presentation.render_for(Comment, model='author')
def render_comment_author(self, h, comp, *args):
    user = self.comment.created_by
    h << h.a(user.fullname,
             class_='author',
             href='profile/' + user.uid).action(lambda user_uid=user.uid: self.goto_user(user_uid))
    return h.root


@presentation.render_for(Comment, model='actions')
def render_comment_actions(self, h, comp, *args):

    # delete
    if security.has_permissions('delete_comment', self) and not self.show_delete_form():
        h << h.a(h.i(class_='icon-close'),
                 class_="delete",
                 title=_(u'Delete this comment')).action(lambda: self.show_delete_form(True))

    # moderation
    if not self.comment.moderated and security.has_permissions('moderate_comment', self):
        h << h.a(h.i(class_='icon-remark'),
                 class_="moderate",
                 title=_(u'Moderate this comment')).action(self.moderate)

    if self.comment.moderated and security.has_permissions('unmoderate_comment', self):
        h << h.a(h.i(class_='icon-remark'),
                 class_="unmoderate",
                 title=_(u'Cancel moderation')).action(self.cancel_moderation)

    # vote
    if security.has_permissions('vote_comment', self):
        if self.has_vote():
            label = _(u"I don't find this comment relevant anymore")
            h << h.a(h.i(class_='icon-thumb-down'),
                     title=label).action(self.remove_vote)
        else:
            label = _(u"I find this comment relevant")
            h << h.a(h.i(class_='icon-thumb-up'),
                     title=label).action(self.add_vote)

    return h.root


@presentation.render_for(Comment, model='delete_form')
def render_comment_delete_form(self, h, comp, *args):
    if self.show_delete_form():
        def delete_action():
            if self.delete():
                comp.answer(self.id)

        def cancel_action():
            self.reset()
            self.show_delete_form(False)

        with h.form:
            h << h.div(_(u"Fill this form to delete the comment (max. 150 characters)"),
                       class_='legend')
            h << h.strong(_(u'Reason:')) << " "
            h << h.input(type='text', value=self.delete_reason(), maxlength=150, size=56).action(self.delete_reason).error(self.delete_reason.error) << ' '
            h << h.input(type='submit', value=_(u'Delete')).action(delete_action) << ' '
            h << h.input(type='submit', value=_(u'Cancel')).action(cancel_action)

    return h.root


# ---------------------------------------

@presentation.render_for(CommentCreator)
def render_commentcreator(self, h, comp, *args):
    def commit():
        if self.create_comment():
            comp.answer()

    with h.div(class_="commentForm"):
        # h << h.div(h.span(h.a(_(u'I comment!'))), class_="tab active")
        with h.form(enctype='multipart/form-data'):  # so that the browser send binary data correctly
            with h.div(class_='fields'):
                # h << h.label(_(u'Comment content:'))
                h << h.textarea(self.content(),
                                class_="comment wide",
                                rows="",
                                cols="",
                                placeholder=_(u'Post your comment')).action(self.content).error(self.content.error)
                h << h.label(_(u'Attached file (%d KB max):') % attachments_max_size())
                h << h.input(type='file',
                             class_='file').action(self.attachment).error(self.attachment.error)

            with h.div(class_='buttons'):
                h << h.input(type="submit", class_="submit", value=_(u'post')).action(lambda: self.with_login(commit))

    return h.root


# ---------------------------------------

@presentation.render_for(CommentPager)
def render_comment_pager(self, h, comp, *args):
    if self.feedback_message:
        h << component.Component(FlashMessage(self.feedback_message.pop()))

    comments = self.comments()
    if comments:
        with h.ul(class_='comments-list'):
            print comments[0]
            h << comments
    else:
        with h.ul(class_='comments-list'):
            h << h.li(_(u'No comment'))  # deal with the deletion of the last remaining comment

    return h.root
