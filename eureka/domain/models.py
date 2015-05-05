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

import gc
import hashlib
import itertools
import operator
import os
import random
import re
import string
from datetime import datetime, timedelta

from elixir import (Boolean, ColumnProperty, DateTime, Entity, Field, Float,
                    Integer, ManyToMany, ManyToOne, OneToMany, OneToOne,
                    options_defaults, Unicode, UnicodeText, using_options)
from elixir.events import after_update, before_delete, after_insert
from eureka.domain import mail_notification
from eureka.infrastructure import avatars, registry, tools
from eureka.infrastructure.filesystem import get_fs_service
from eureka.infrastructure.password_policy import PasswordPolicy
from eureka.infrastructure.tools import create_unique_file, Enum
from eureka.infrastructure.workflow import voucher
from eureka.pkg import available_locales
from nagare import log, security
from nagare.database import session
from nagare.i18n import _, _L, get_locale
from sqlalchemy import MetaData
from sqlalchemy.ext.associationproxy import AssociationProxy
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.sql.expression import and_, desc, func, not_, or_, select

# database metadata singleton
__metadata__ = MetaData()

# for MySQL, use InnoDB engine and utf-8 default charset
options_defaults['table_options'].update(
    dict(mysql_engine="InnoDB", mysql_charset='utf8'))


# domain entities and value object as defined in
# http://domaindrivendesign.org/node/109 and
# http://domaindrivendesign.org/node/135
# FIXME: move all queries from here to the adequate repository
class UnpicklableError(Exception):
    """Exception raises when we try to pickle an unpicklable object"""


class Unpicklable(object):
    """A mixin that is not pickable and must be used in all entities to avoid
    mistakes like storing one in the continuation because of a callback for
    instance. It can not be a class inheriting from Entity because it is not
    supported by Elixir."""

    def __reduce__(self):
        msg = 'This object is unpicklable: ' + repr(self)
        #  FIXME: show references chain
        gc.collect()
        msg += '\nReferenced by: ' + ', '.join(
            map(str, gc.get_referrers(self)))
        raise UnpicklableError(msg)


class VersionData(Entity, Unpicklable):
    using_options(tablename='version')

    version = Field(Unicode(70))


# class OrganizationType(object):
#    Corporation = u'corporation'
#    Direction = u'direction'
#    Service = u'service'
#    Site = u'site'

# -- Eventually, remove the organization_types table
#
# -- select o.id, o.label, t.label as type, o.parent_id
# -- from organizations o
# -- inner join organization_types t on o.type_id = t.id;

# FIXME: use a static enumeration or rename to OrganizationTypeData?
class OrganizationType(Entity, Unpicklable):
    using_options(tablename='organization_types')

    label = Field(Unicode(20), colname='label', index=True, unique=True,
                  nullable=False)

    organizations = OneToMany('OrganizationData', inverse='type')

    def __init__(self, label):
        super(OrganizationType, self).__init__()
        self.label = label


class OrganizationData(Entity, Unpicklable):
    using_options(tablename='organizations')

    label = Field(Unicode(70), colname='label', index=True, nullable=False)

    type = ManyToOne('OrganizationType', inverse='organizations',
                     required=True)
    parent = ManyToOne('OrganizationData', inverse='children')
    children = OneToMany('OrganizationData', inverse='parent')

    def path(self, sep=u'#'):
        parent_path = self.parent.path(sep) if self.parent else u''
        return parent_path + sep + self.label

    @staticmethod
    def fix_corporation(name):
        if name:
            name = name.title()
            if name.startswith(u'Pages Jaunes'):
                name = u'PagesJaunes'

        return name

    @staticmethod
    def fix_direction(name):
        if name:
            name = name.title()
            name = name.replace(u'D ', u'Dir. ')
            name = name.replace(u'Direction ', 'Dir. ')
            name = name.replace(u'Dir ', 'Dir. ')

        return name

    @staticmethod
    def fix_service(name):
        if name:
            name = name.title()
            name = re.sub(u'Vtc Sevres Client', u'Vtc Sevres Clients', name)

            for accr in [u'Spo', u'Vtc', u'Vrp', u'Rvs', u'Dmc', u'Drh',
                         u'Dsi', u'Dfc', u'Dc', u'Dap', u'Di']:
                name = name.replace(accr + u' ', accr.upper() + u' ', 1)

            for accr in [u'Ai']:
                name = name.replace(u' ' + accr, u' ' + accr.upper(), 1)

            name = name.replace(u'Développement', u'Dév.')

        return name

    @staticmethod
    def fix_site(name):
        if name:
            name = name.title()
            name = name.replace(u'Dijon-Fdv', u'Dijon - Fdv')

            for accr in [u'- Fdv', u'- Tlv']:
                name = name.replace(accr, accr.upper(), 1)

        return name

    @classmethod
    def fix_path(cls, path, sep=u'#'):
        # remove redundant spaces
        path = re.sub(ur'\s+', u' ', path)

        # decode the organization parts
        (corporation_name,
         direction_name,
         service_name,
         site_name) = path[1:].split(sep)

        # fix the individual parts
        corporation_name = cls.fix_corporation(corporation_name)
        direction_name = cls.fix_direction(direction_name)
        service_name = cls.fix_service(service_name)
        site_name = cls.fix_site(site_name)

        # merge parts back
        return sep + sep.join((
            corporation_name or u'', direction_name or u'',
            service_name or u'',
            site_name or u''))

    @classmethod
    def get_organizations(cls, org_type, parent_id=None):
        query = (session.query(
            cls.label,
            cls.id
        ).outerjoin(cls.type))

        query = (query.filter(OrganizationType.label == org_type)
                 .order_by(cls.label))

        if parent_id:
            query = query.filter(cls.parent_id == parent_id)
        return [(elt.label, elt.id) for elt in query]

    @classmethod
    def get_corporations(cls, parent_id=None):
        return cls.get_organizations(u'corporation')

    @classmethod
    def get_sites(cls, parent_id=None):
        return cls.get_organizations(u'site', parent_id=parent_id)

    @classmethod
    def get_directions(cls, parent_id=None):
        return cls.get_organizations(u'direction', parent_id=parent_id)

    @classmethod
    def get_services(cls, parent_id=None):
        return cls.get_organizations(u'service', parent_id=parent_id)

    @classmethod
    def get_subsites(cls, parent_id=None):
        return cls.get_organizations(u'subsite', parent_id=parent_id)

    @classmethod
    def get_organization(cls, organization_id):
        return cls.get(organization_id) if organization_id != -1 else None


def attachments_max_size():
    """Returns the attachments max size in kilobytes"""
    return int(registry.get_configuration('misc')['attachments_max_size'])


class AttachmentData(Entity, Unpicklable):
    using_options(tablename='attachments')

    # filename without path (name of the uploaded file)
    filename = Field(Unicode(255), nullable=False)
    # mime content-type
    mimetype = Field(Unicode(255), nullable=False)
    # path in the data filesystem, relative to the attachments directory
    filepath = Field(Unicode(512), nullable=False)

    def __init__(self, filename, mimetype, data):
        super(AttachmentData, self).__init__()  # call base
        self.filename = filename
        self.mimetype = mimetype
        self.filepath = None  # will be initialized later
        self.data = data

    @property
    def data(self):
        with open(get_fs_service().expand_path(
                ['attachments', self.filepath or ''])) as f:
            return f.read()

    @data.setter
    def data(self, value):
        self._remove_old_file()
        datafile, self.filepath = create_unique_file(
            get_fs_service().expand_path(['attachments', '']),
            self.filename)
        print >> datafile, value

    @before_delete
    def _remove_old_file(self):
        if self.filepath is not None:
            os.remove(get_fs_service().expand_path(
                ['attachments', self.filepath or '']))


class IdeaData(Entity, Unpicklable):
    using_options(tablename='ideas')

    show_creator = Field(Boolean)
    description = Field(UnicodeText)
    origin = Field(UnicodeText)
    implementation = Field(UnicodeText)
    impact = Field(UnicodeText)
    benefit_department = Field(UnicodeText, default=u'')
    title = Field(Unicode(150))
    submission_date = Field(DateTime)

    submitted_by = ManyToOne('UserData', inverse='ideas_as_submitter')
    proxy_submitter = ManyToOne('UserData', inverse='ideas_as_proxy_submitter')

    authors_association = OneToMany('AuthorData',
                                    cascade='all,delete-orphan',
                                    collection_class=ordering_list('position'),
                                    order_by='position')

    authors = AssociationProxy('authors_association', 'user')

    tracked_by = ManyToMany('UserData',
                            inverse='tracked_ideas')

    tags = ManyToMany('TagData',
                      tablename='tags_ideas',
                      inverse='ideas')

    votes = OneToMany('VoteIdeaData',
                      cascade='all,delete-orphan')

    comments = OneToMany('CommentData',
                         cascade='all,delete-orphan',
                         order_by='submission_date')

    events = OneToMany('EventData',
                       inverse='idea',
                       cascade='all,delete-orphan')

    wf_context = ManyToOne('IdeaWFContextData',
                           inverse='idea',
                           cascade='all')

    eval_context = ManyToOne('IdeaEvalContextData',
                             inverse='idea',
                             cascade='all')

    challenge = ManyToOne('ChallengeData',
                          required=False)

    domain = ManyToOne('DomainData')

    # FIXME: need delete-orphan
    read_ideas_association = OneToMany('ReadIdeaData',
                                       cascade='all')

    readers = AssociationProxy(
        'read_ideas_association',
        'user',
        creator=lambda user: ReadIdeaData(user=user, idea=None))

    total_readers = Field(Integer, default=0, index=True)

    already_done = Field(Boolean)

    # FIXME: would be better to use a ManyToMany relationship
    # and delete-orphan cascade rules
    attachment_1 = ManyToOne('AttachmentData', single_parent=True,
                             cascade='all,delete-orphan')
    attachment_2 = ManyToOne('AttachmentData', single_parent=True,
                             cascade='all,delete-orphan')
    attachment_3 = ManyToOne('AttachmentData', single_parent=True,
                             cascade='all,delete-orphan')

    # reminders
    reminders = OneToMany('ReminderData',
                          inverse='idea',
                          cascade='all,delete-orphan')

    # caches around heavily used lists counter
    # FIXME: total_comments should be removed
    total_comments = Field(Integer, nullable=False,
                           default=0)  # only visible ones
    # FIXME: total_votes should be removed
    total_votes = Field(Integer, nullable=False, default=0)

    def __str__(self):
        return self.title

    def __repr__(self):
        return u"<IdeaData('%s')>" % self.id

    def readers_updated(self):
        self.total_readers = (
            session.query(ReadIdeaData.id)
                   .join(IdeaData)
                   .filter(IdeaData.id == self.id)
                   .count()
        )

    # logger
    @property
    def log(self):
        return log.get_logger('.' + __name__)

    # -----------
    # votes
    def vote(self, user, rate=1):
        vote = self.find_vote(user)
        if not vote:
            self.votes.append(
                VoteIdeaData(rate=rate, user=user, timestamp=datetime.now()))
        else:
            # substract the old vote from the total
            self.total_votes -= vote.rate
            vote.rate = rate

        user.process_point_event(voucher.PointEvent.VOTE)
        self.total_votes += rate

    def find_vote(self, user):
        for vote in self.votes:
            if vote.user == user:
                return vote
        return None

    # comments
    @property
    def visible_comments(self):
        return [comment for comment in self.comments if comment.visible]

    @property
    def all_notified_users(self):
        if self.proxy_submitter:
            return itertools.chain(self.authors, [self.proxy_submitter])
        else:
            return self.authors

    def add_comment(self, user, content, attachment=None):
        comment = CommentData(idea=self,
                              created_by=user,
                              content=content,
                              attachment=attachment)

        # FIXME: we really should remove the total_comments field
        self.total_comments = len(self.visible_comments)
        user.process_point_event(voucher.PointEvent.ADD_COMMENT,
                                 comment_id=comment.id)
        self.tracked_by.append(user)

        # notify interested users that a comment has been posted
        target_users = set(
            u for u in (self.tracked_by + self.authors) if u.uid != user.uid)
        for target_user in target_users:
            mail_notification.send(
                'mail-event-comment-added.html',
                to=target_user,
                comment=content,
                comment_author=user,
                idea=self,
                delivery_priority=mail_notification.DeliveryPriority.Low)
            target_user.add_event(EventType.CommentAdded, self)

        return comment

    def remove_comment(self, comment, reason=''):
        user = comment.created_by
        d = comment.submission_date
        #        self.comments.remove(comment)
        comment.deleted = True
        user.process_point_event(voucher.PointEvent.REMOVE_COMMENT,
                                 comment_date=d, reason=reason,
                                 comment_id=comment.id)
        self.total_comments = len(self.visible_comments)

    def _comment_visibility_changed(self, comment):
        self.total_comments = len(self.visible_comments)

    # -----------
    # reminders
    def _find_reminders_by_type(self, type):
        return [reminder for reminder in self.reminders if
                reminder.type == type]

    def _find_reminder_by_type(self, type):
        for reminder in self.reminders:
            if reminder.type == type:
                return reminder

    @property
    def unchanged_state_reminder_date(self):
        reminder = self._find_reminder_by_type(ReminderType.UnchangedState)
        return reminder.date if reminder else None

    @unchanged_state_reminder_date.setter
    def unchanged_state_reminder_date(self, date):
        reminder = self._find_reminder_by_type(ReminderType.UnchangedState)
        if date is not None:
            if not reminder:
                self.reminders.append(
                    ReminderData(type=ReminderType.UnchangedState, date=date))
            else:
                reminder.date = date
        else:
            if reminder:
                reminder.delete()

    @after_update
    @after_insert
    def _search_engine_index(self):
        from eureka.domain.services import get_search_engine

        try:
            get_search_engine().index(self)
        except Exception:
            self.log.debug('Error while indexing object %r', self,
                           exc_info=True)

    @before_delete
    def _search_engine_remove(self):
        from eureka.domain.services import get_search_engine

        try:
            get_search_engine().remove(self)
        except Exception:
            self.log.debug('Error while deleting object %r', self,
                           exc_info=True)


class VoteIdeaData(Entity, Unpicklable):
    using_options(tablename='votes_ideas')

    # idea and user fields are not primary keys
    #   because a DSIG can post more than one vote (cheat)
    # FIXME: this is NOT a good reason since we can increase the rate instead:
    #   implement this in the code
    idea = ManyToOne('IdeaData', required=True)
    user = ManyToOne('UserData', required=True)
    rate = Field(Integer, nullable=False, default=1)
    timestamp = Field(DateTime, nullable=False)


class ReadIdeaData(Entity, Unpicklable):
    using_options(tablename='read_ideas')

    #  user and idea are not the primary keys
    #   because a user can read an idea more than once
    user = ManyToOne('UserData', required=True)
    idea = ManyToOne('IdeaData', required=True)
    timestamp = Field(DateTime, nullable=False)


# workflow
class IdeaWFContextData(Entity, Unpicklable):
    using_options(tablename='wfcontexts')

    idea = OneToOne('IdeaData', inverse='wf_context')
    state = ManyToOne('StateData', inverse="state_for")
    comments = OneToMany('WFCommentData',
                         cascade='all,delete-orphan',
                         inverse="idea_wf")
    publication_date = Field(DateTime)
    recommendation_date = Field(DateTime)

    assignated_fi = ManyToOne('UserData', inverse="assignated_fi_ideas")
    assignated_di = ManyToOne('UserData', inverse="assignated_di_ideas")

    def __str__(self):
        return str(self.state)

    # FIXME: remove setter
    # FIXME: hide state object behind an association proxy
    def set_state(self, state):
        self.state = StateData.query.filter(StateData.label == state).first()

    def add_comment(self, created_by, content, old_state, new_state):
        """Add new comment on a transition.

        WF Comment contains author, from_state, to_state, date and a comment.

        In:
          - `content`   -- content of comment
          - `old_state` -- from state
          - `new_state` -- to state

        """
        from eureka.domain.services import get_workflow

        workflow = get_workflow()

        # we don't want to track draft state changes
        if new_state == workflow.WFStates.DRAFT_STATE:
            return

        from_state = StateData.query.filter(
            StateData.label == old_state).first()
        to_state = StateData.query.filter(StateData.label == new_state).first()

        c = WFCommentData()
        c.created_by = created_by
        c.content = content or u''
        c.submission_date = datetime.today()
        c.idea_wf = self
        c.from_state = from_state
        c.to_state = to_state


class IdeaEvalContextData(Entity, Unpicklable):
    using_options(tablename='evalcontexts')

    title = Field(Unicode(150))
    description = Field(UnicodeText)
    impact = Field(UnicodeText)

    financial_gain = Field(UnicodeText)
    customer_satisfaction = Field(UnicodeText)
    process_tier_down = Field(UnicodeText)
    public_image = Field(UnicodeText)
    environment_improvement = Field(UnicodeText)
    other_impact = Field(UnicodeText)

    innovation_scale = Field(Integer, nullable=False, default=0)
    complexity_scale = Field(Integer, nullable=False, default=0)
    duplicate = Field(Integer, nullable=False, default=0)
    localization = Field(Integer, nullable=False, default=0)

    target_date = Field(DateTime)
    goal = Field(Float)
    revenues_first_year = Field(Integer)
    revenues_first_year_value = Field(Float)
    revenues_second_year = Field(Integer)
    revenues_second_year_value = Field(Float)
    expenses_first_year = Field(Integer)
    expenses_first_year_value = Field(Boolean)
    expenses_second_year = Field(Integer)
    expenses_second_year_value = Field(Boolean)
    evaluation_impact = Field(UnicodeText)

    idea = OneToOne('IdeaData', inverse='eval_context')
    comments = OneToMany('EvalCommentData')

    def __str__(self):
        return str(self.state)


# -- users' mail settings --
class MailDeliveryFrequency(Enum):
    Immediately = u'immediately'
    Daily = u'daily'


class UserData(Entity, Unpicklable):
    using_options(tablename='users')

    # user identifier
    uid = Field(Unicode(50), index=True, unique=True, nullable=False,
                primary_key=True)

    # important dates (see the corresponding read-only properties)
    _creation_date = Field(DateTime, colname='creation_date',
                           synonym='creation_date', nullable=False)
    _profile_modification_date = Field(DateTime,
                                       colname='profile_modification_date',
                                       synonym='profile_modification_date',
                                       nullable=False)
    _last_connection_date = Field(DateTime, colname='last_connection_date',
                                  synonym='last_connection_date')

    # name
    firstname = Field(Unicode(50), index=True, nullable=False)
    lastname = Field(Unicode(70), index=True, nullable=False)
    fullname = ColumnProperty(lambda c: c.firstname + u' ' + c.lastname)

    # email
    email = Field(Unicode(150), index=True, unique=False, nullable=False)

    # password...
    # salt for password encryption: 32 characters string
    _salt = Field(Unicode(32), colname='salt', synonym='salt', nullable=False)
    # encrypted password: 512 bits number in hex representation
    _password = Field(Unicode(128), colname='password', synonym='password',
                      nullable=False)
    # is the password generated? In this case,
    #   the user will be asked to change it at connection time
    _password_generated = Field(Boolean, colname='password_generated',
                                synonym='password_generated', nullable=False,
                                default=True)
    # last password modification date
    _password_modification_date = Field(DateTime,
                                        colname='password_modification_date',
                                        nullable=False)

    # is the user allowed to connect to the application?
    enabled = Field(Boolean, default=False)

    # corporate information
    corporation = ManyToOne('OrganizationData')
    direction = ManyToOne('OrganizationData')
    service = ManyToOne('OrganizationData')
    site = ManyToOne('OrganizationData')
    subsite = ManyToOne('OrganizationData')

    position = Field(Unicode(70), index=True, nullable=False)
    incorporated = Field(Boolean, nullable=False, default=False)

    # phone numbers
    mobile_phone = Field(Unicode(150), index=True)
    work_phone = Field(Unicode(150), index=True)

    # This user was imported by a script
    imported = Field(Boolean, default=False)

    # points
    points = OneToMany('PointData', inverse='user')

    # FIXME: rename to skills
    description = Field(UnicodeText)
    competencies = Field(UnicodeText)
    expertises = Field(UnicodeText)
    hobbies = Field(UnicodeText)
    specialty = Field(UnicodeText)
    di_business_area = Field(UnicodeText)  # business area handled as a DI

    ideas_as_submitter = OneToMany('IdeaData',
                                   inverse='submitted_by')

    ideas_as_proxy_submitter = OneToMany('IdeaData',
                                         inverse='proxy_submitter')

    authors_association = OneToMany('AuthorData',
                                    cascade='all,delete-orphan',
                                    collection_class=ordering_list('position'),
                                    order_by='position')

    ideas_as_author = AssociationProxy('authors_association', 'idea')

    tracked_ideas = ManyToMany('IdeaData',
                               inverse='tracked_by')

    roles = OneToMany('RoleData',
                      cascade='all,delete-orphan')

    comments = OneToMany('CommentData',
                         cascade='all,delete-orphan')

    pending_email_messages = OneToMany('PendingEmailMessageData',
                                       cascade='all,delete-orphan')

    di_for_challenges = ManyToMany('ChallengeData',
                                   tablename="dis_for_challenges",
                                   inverse='associated_dis')

    #  FIXME: we'd better store the image filename directly!
    _photo_date = Field(DateTime, colname='photo_date', synonym='photo_date')

    fi = ManyToOne('UserData', inverse='fi_for', required=True)
    fi_for = OneToMany('UserData', inverse='fi')

    assignated_fi_ideas = OneToMany('IdeaWFContextData',
                                    inverse="assignated_fi")

    assignated_di_ideas = OneToMany('IdeaWFContextData',
                                    inverse="assignated_di")

    managed_domains = ManyToMany('DomainData',
                                 tablename="dis_for_domains",
                                 inverse='dis')

    read_ideas_association = OneToMany('ReadIdeaData',
                                       inverse='user',
                                       cascade='all')  # FIXME: delete-orphan?

    read_ideas = AssociationProxy(
        'read_ideas_association',
        'idea',
        creator=lambda idea: ReadIdeaData(idea=idea, timestamp=datetime.now()))

    events = OneToMany('EventData',
                       cascade='all,delete-orphan',
                       inverse='user')

    timeline = OneToMany('TimeLineData',
                         cascade='all,delete-orphan',
                         inverse='user',
                         order_by='-date',
                         uselist=True)

    # votes
    votes_for_ideas = OneToMany('VoteIdeaData', cascade='all,delete-orphan',
                                inverse='user')
    votes_for_comments = OneToMany('VoteCommentData',
                                   cascade='all,delete-orphan', inverse='user')
    votes_for_polls = OneToMany('VotePollData', cascade='all,delete-orphan',
                                inverse='user')

    # prefered locale
    locale = Field(Unicode(10), nullable=False)

    # home page settings
    _home_settings = OneToMany('HomeSettingsData',
                               # colname='home_settings',
                               uselist=False,
                               # cascade='all,delete-orphan',
                               inverse='user')

    # mail settings
    mail_delivery_frequency = Field(Unicode(20), nullable=False,
                                    default=MailDeliveryFrequency.Immediately)

    # FIXME: remove this counter cache (not needed!)
    nb_votes_this_day = Field(Integer, nullable=False,
                              default=0)  # votes for ideas

    # FIXME: it would be better to store the profile information
    #   not in the UserData but in a dedicated entity

    # these are the fields that can be edited in the user profile
    _profile_fields = (
        mobile_phone, work_phone, competencies, expertises, hobbies, specialty,
        _photo_date)

    # handles the profile modification date
    def __setattr__(self, name, value):
        # update the profile modification date
        profile_fields_names = set(
            field.name for field in self._profile_fields)
        if name in profile_fields_names:
            super(UserData, self).__setattr__('_profile_modification_date',
                                              datetime.now())

        # call the base implementation
        return super(UserData, self).__setattr__(name, value)

    # constructor
    def __init__(self, uid, email, firstname, lastname, position=u'',
                 password=None, locale=None,
                 incorporated=False, enabled=True, **kwargs):
        """
        Create a new user.
        If no password is provided, a new password will be generated
        """
        super(UserData, self).__init__(
            uid=uid,
            email=email,
            firstname=firstname,
            lastname=lastname,
            position=position,
            locale=locale or available_locales[0][0],
            incorporated=incorporated,
            enabled=enabled,
            _creation_date=datetime.now(),
            _modification_date=datetime.now(),
            _profile_modification_date=datetime.now(),
            _last_connection_date=None,
            **kwargs)
        self._set_password(password)

    # read only properties
    @property
    def creation_date(self):
        return self._creation_date

    @property
    def last_connection_date(self):
        return self._last_connection_date

    @property
    def profile_modification_date(self):
        return self._profile_modification_date

    # roles/workflow helper functions
    def is_dsig(self):
        return self.has_role(RoleType.DSIG)

    def is_facilitator(self, idea=None):
        """
        Check if the user is the facilitator of an idea,
        or just a facilitator if no idea is specified
        """
        if not self.has_role(RoleType.Facilitator):
            return False

        if not idea:
            return True

        assignated_fi = idea.wf_context.assignated_fi
        return assignated_fi is not None and assignated_fi.uid == self.uid

    def is_developer(self, idea=None):
        """Check if the user is the developer of an idea, or just a developer if
        no idea is specified"""
        if not self.has_role(RoleType.Developer):
            return False

        if not idea:
            return True

        assignated_di = idea.wf_context.assignated_di
        return assignated_di is not None and assignated_di.uid == self.uid

    def has_mobile_access(self):
        return self.has_role(RoleType.MobileAccess)

    # logger
    @property
    def log(self):
        return log.get_logger('.' + __name__)

    # comparison & hashing
    def __cmp__(self, other):
        return cmp(self.uid, other.uid) if other else +1

    def __hash__(self):
        return hash(self.uid)

    # display
    def __str__(self):
        return u'%s (%s)' % (self.fullname, self.uid)

    def __repr__(self):
        return u"<UserData('%s')>" % self.uid

    # -----------
    def on_connection(self, platform, date=None):
        """
        Trigger business rules that apply on a new connection
        from the current user to the application
        """
        date = date or datetime.now()

        today_connection_points = list(self.get_points(
            category=voucher.PointEvent.FIRST_CONNECTION_OF_THE_DAY,
            from_date=date.date(),
            subject_id=platform))
        if today_connection_points:  # not a new connection
            return

        # log the new connection
        self.log.debug('New connection of %s on %s' % (self.uid, platform))

        # adds points for the first connection, if necessary
        first_connection_points = list(
            self.get_points(category=voucher.PointEvent.FIRST_CONNECTION,
                            subject_id=platform))
        if not first_connection_points:
            self.process_point_event(voucher.PointEvent.FIRST_CONNECTION,
                                     subject_id=platform)

        # adds points for the first connection of the day
        #   and reinitializes the daily votes
        self.process_point_event(
            voucher.PointEvent.FIRST_CONNECTION_OF_THE_DAY,
            subject_id=platform)
        # FIXME: we should not have to store the vote count in the entity!
        self.nb_votes_this_day = 0

        # updates the last connection timestamp
        self._last_connection_date = date

    # -----------

    # home settings
    @property
    def home_settings(self):
        if not self._home_settings:
            from eureka.domain.repositories import ChallengeRepository

            challenges = list(ChallengeRepository().get_by_active_at_date())
            self._home_settings = HomeSettingsData(challenges=challenges)
        return self._home_settings

    @home_settings.setter
    def home_settings(self, home_settings):
        self._home_settings = home_settings

    # -----------
    # password
    @property
    def password_policy(self):
        try:
            # FIXME: we should push the password_policy to the UserData
            #   instead of pulling it from the security manager
            #   which is not always available.
            return security.get_manager().password_policy
        except AttributeError:
            # You should configure the environment
            #   before trying to use UserData...
            #   But there are exceptions to this rule
            log.debug(
                'No security manager available: '
                'using the default password policy',
                exc_info=True)
            return PasswordPolicy()

    @property
    def password(self):
        return self._password

    def change_password(self, password):
        """Set the user's password"""
        assert password
        self._set_password(password)

    def reset_password(self):
        """Generate a new password for the user, return his new password"""
        return self._set_password(None)

    def should_change_password(self):
        """Should the user change his password at connection time?"""
        return self._password_generated or self._password_expired

    def validate_password(self, new_password):
        """Validate that the new_password conforms to the password policy"""
        return self.password_policy.validate_password(new_password)

    @staticmethod
    def _create_random_salt(length=32):
        allowed_chars = string.ascii_letters + string.digits
        return u''.join(random.choice(allowed_chars) for i in range(length))

    def encrypt_password(self, clear_password):
        """Encrypt the given clear text password using the user specific salt"""
        secret = "hGc9PE8WHy7mluzxYOFnb5P8zeJU8VDs"
        secret_salt = hashlib.sha512(secret + self._salt).hexdigest()
        utf8_password = clear_password.encode('utf-8')
        return unicode(hashlib.sha512(secret_salt + utf8_password).hexdigest())

    def _set_password(self, password=None):
        generated = password is None
        password = password or self.password_policy.generate_password()

        error = self.validate_password(password)
        if error:
            raise ValueError(error)

        self._salt = self._create_random_salt()
        self._password = self.encrypt_password(password)
        self._password_generated = generated
        self._password_modification_date = datetime.now()

        return password

    @property
    def _password_expired(self):
        expiration_delay = self.password_policy.expiration_delay
        if not expiration_delay:
            return False

        expiration_date = self._password_modification_date + timedelta(
            days=expiration_delay)
        return expiration_date < datetime.now()

    # -----------
    # emails
    def send_email(self, template_name, **kwargs):
        """Send an email to the user"""
        mail_notification.send(template_name, to=self, **kwargs)

    def send_welcome_email(self, password):
        """
        Send a welcome email to the user with his login
        and his temporary password
        """
        self.send_email('mail-welcome.html', comment=password)

    # -----------
    # photo & thumbnails
    @property
    def photo(self):
        if not self._photo_date:
            return None

        return avatars.read_photo(self.uid, self._photo_date)

    @photo.setter
    def photo(self, photo):
        self._change_photo(photo)
        self.process_point_event(voucher.PointEvent.CHANGE_AVATAR)

    def _change_photo(self, photo):
        """
        Utility method to change the user photo
        without changing its points
        """
        old_photo_date = self._photo_date

        # write the new photo
        self._photo_date = avatars.write_photo(self.uid,
                                               photo) if photo else None

        # remove the old photo
        if old_photo_date:
            avatars.remove_photo(self.uid, old_photo_date)

    # -----------
    # points
    def process_point_event(self, point_event, **kwargs):
        """
        Record a point event. Use the voucher to find out
        how many points are to be given to this user
        """
        voucher.add_points(self, point_event, **kwargs)

    @ColumnProperty
    def available_points(self):
        return select([func.coalesce(func.sum(PointData.nb_points), 0)],
                      whereclause=PointData.user_uid == self.uid)

    @ColumnProperty
    def acquired_points(self):
        spent_points_labels = set(voucher.get_sorted_spent_point_categories())
        return select([func.coalesce(func.sum(PointData.nb_points), 0)],
                      whereclause=and_(PointData.user_uid == self.uid, not_(
                          PointData.label.in_(spent_points_labels))))

    @property
    def spent_points(self):
        return self.acquired_points - self.available_points

    @property
    def status_level(self):
        points = self.acquired_points
        if points == 0:
            return 0
        if points <= 100:
            return 1
        if points <= 200:
            return 2
        if points <= 2000:
            return 3
        if points <= 10000:
            return 4
        return 5

    StatusLevelLabels = (
        _L("status_level0"),
        _L("status_level1"),
        _L("status_level2"),
        _L("status_level3"),
        _L("status_level4"),
        _L("status_level5"),
    )

    @property
    def status_level_label(self):
        return self.StatusLevelLabels[self.status_level]

    def add_points(self, category, nb_points, reason=None, timestamp=None,
                   subject_id=None):
        """Add points to the user"""
        assert category in voucher.PointCategory
        p = PointData(label=category,
                      nb_points=nb_points,
                      reason=reason,
                      date=timestamp or datetime.now(),
                      subject_id=subject_id)
        self.points.append(p)

    def get_points(self, category=None, from_date=None, to_date=None,
                   subject_id=None):
        # FIXME: use (filter) self.points
        q = PointData.query.filter(PointData.user_uid == self.uid)
        if category:
            q = q.filter(PointData.label == category)
        if from_date:
            q = q.filter(PointData.date >= from_date)
        if to_date:
            q = q.filter(PointData.date < to_date)
        if subject_id:
            q = q.filter(PointData.subject_id == subject_id)
        return q.all()

    def get_points_by_category(self):
        """Return points grouped by category"""
        # the order_by clause is necessary for the groupby
        q = PointData.query.filter(PointData.user_uid == self.uid).order_by(
            PointData.label)
        g = itertools.groupby(q, key=operator.attrgetter('label'))
        return dict(map(lambda (k, v): (k, list(v)), g))

    # -----------
    # organization
    @property
    def corporation_label(self):
        return self.corporation.label if self.corporation else u''

    @property
    def direction_label(self):
        return self.direction.label if self.direction else u''

    @property
    def service_label(self):
        return self.service.label if self.service else u''

    @property
    def site_label(self):
        return self.site.label if self.site else u''

    @property
    def subsite_label(self):
        return self.subsite.label if self.subsite else u''

    @property
    def organization_path(self):
        return (
            self.corporation_label or None,
            self.direction_label or None,
            self.service_label or None,
            self.site_label or None,
        )

    # -----------
    # ROLES
    # FIXME: the code using this user instance should deal
    #   with a collection of roles labels instead of methods like these
    #   use an AssociationProxy?!
    def get_roles(self):
        return [role.type for role in self.roles]

    def has_role(self, role_type):
        """
        Determine if this user has a given role
        """
        return self._find_role(role_type) is not None

    def add_role(self, role_type):
        """
        Add a role to this user (secured way to add a role)
        """
        if self.has_role(
                role_type):  # make sure we do not add the same role twice
            return False

        self.roles.append(RoleData(role_type))
        return True

    def remove_role(self, role_type):
        """
        Remove the role and the associated privileges
        (secured way to remove a role)
        """
        role = self._find_role(role_type)
        if role:
            self.roles.remove(role)

    def _find_role(self, role_type):
        for role in self.roles:
            if role.type == role_type:
                return role
        return None

    def transfer_facilitator_basket(self, new_user):
        """
        Transfer the facilitator basket to a new user.
        This user should be a facilitator.
        """
        assert new_user.has_role(RoleType.Facilitator)
        from eureka.domain.repositories import IdeaRepository

        idea_repository = IdeaRepository()
        for idea in idea_repository.get_assigned_to_facilitator(self):
            idea.wf_context.assignated_fi_uid = new_user.uid

    def transfer_developer_basket(self, new_user):
        """
        Transfer the developer basket to a new user.
        This user should be a developer.
        """
        assert new_user.has_role(RoleType.Developer)
        from eureka.domain.repositories import IdeaRepository

        # FIXME: we are not supposed to create the repository here
        idea_repository = IdeaRepository()
        for idea in idea_repository.get_assigned_to_developer(self):
            idea.wf_context.assignated_di_uid = new_user.uid

    def transfer_responsibilities(self, role_type, new_user):
        """
        Transfer the responsibilities granted to the current user
        by one of his roles (e.g. baskets, assigned users or ideas, ...)
        to another user. Be careful, this method DOES NOT remove the role
        for the current user.
        """
        from eureka.domain.repositories import UserRepository

        user_repository = UserRepository()

        if role_type == RoleType.Facilitator:
            # define the target user
            target_user = new_user or user_repository.facilitator
            # add the facilitator role to the new user if needed
            target_user.add_role(RoleType.Facilitator)
            # replace the facilitator of the users
            #   that were previously "facilitated" by this user
            for user in self.fi_for:
                user.fi_uid = target_user.uid
                # transfer the ideas basket to the new user
            self.transfer_facilitator_basket(target_user)
        elif role_type == RoleType.Developer:
            # define the target user
            target_user = new_user or user_repository.developer
            # add the developer role to the new user if needed
            target_user.add_role(RoleType.Developer)
            # replace the challenge developer if any
            for challenge in self.di_for_challenges:
                challenge.associated_dis.remove(self)
                if new_user:
                    challenge.associated_dis.append(new_user)
                    # transfer the ideas basket to the new user
            self.transfer_developer_basket(target_user)

    def remove_responsibilities(self, role_type):
        """
        Remove the user responsibilities according to its role
        """
        self.transfer_responsibilities(role_type, None)

    # -----------
    # ideas
    def _get_idea(self, idea_id):
        from eureka.domain.repositories import IdeaRepository

        return IdeaRepository().get_by_id(idea_id)

    def untrack_idea(self, idea_id):
        """Remove given idea from user's list of tracked ideas"""
        self.tracked_ideas = [elt for elt in self.tracked_ideas if
                              elt.id != idea_id]

    def track_idea(self, idea_id):
        """Add an idea to the user's list of tracked ideas"""
        idea = self._get_idea(idea_id)
        self.tracked_ideas.append(idea)
        self.add_timeline_idea(idea)

    # -----------
    # read ideas
    @property
    def nb_read_ideas(self):
        return len(self.read_ideas)

    # ------------
    # events on ideas
    def unread_events(self, date=None):
        # FIXME: rename event to notification
        return [e for e in self.events if e.status == EventStatus.New and (
            e.date > date if date else True)]

    def visible_events(self, date=None):
        return [e for e in self.events if e.status != EventStatus.Hidden and (
            e.date > date if date else True)]

    def add_event(self, label, idea):
        # FIXME: rename event to notification or something like that
        return EventData(label, self, idea)

    def hide_event(self, event_id):
        event = EventData.get(event_id)
        event.status = EventStatus.Hidden
        return event

    def read_event(self, event_id):
        event = EventData.get(event_id)
        event.status = EventStatus.Read
        return event

    def read_all_events(self):
        for event in self.events:
            event.status = EventStatus.Read

    # pending email messages
    def add_pending_email_message(self, subject, content):
        self.pending_email_messages.append(
            PendingEmailMessageData(subject, content))

    @after_update
    @after_insert
    def _search_engine_index(self):
        from eureka.domain.services import get_search_engine

        try:
            get_search_engine().index(self)
        except Exception:
            self.log.debug('Error while indexing object %r', self,
                           exc_info=True)

    @before_delete
    def _search_engine_remove(self):
        from eureka.domain.services import get_search_engine

        try:
            get_search_engine().remove(self)
        except Exception:
            self.log.debug('Error while deleting object %r', self,
                           exc_info=True)

    def get_timeline(self, size=10):
        # TODO: replace this with a dynamic relationship
        # sqlalchemy >0.7 is needed to do so
        return self.timeline[:size]

    def add_timeline_user(self, user):
        TimeLineUserData(user=self, target=user)

    def add_timeline_idea(self, idea):
        TimeLineIdeaData(user=self, target=idea)

    @classmethod
    def get_domain_managers(cls, domain, challenge=None, show_all=False):
        """
        Return domain's managers for a current domain

        In:
          - `domain_id` -- domain id
        Return:
          - list of user data
        """
        q = (session.query(cls, func.count(IdeaData.id)
                                    .label('nb_idea'))
             .outerjoin(cls.assignated_di_ideas)
             .outerjoin(IdeaWFContextData.idea)
             .outerjoin(cls.roles)
             .filter(RoleData.type == RoleType.Developer)
             .filter(cls.enabled == True)
             )

        if show_all:
            return q.group_by(cls.uid)

        if challenge:
            return q.outerjoin(cls.di_for_challenges).filter(
                ChallengeData.id == challenge.id).group_by(cls.uid)

        return q.outerjoin(cls.managed_domains).filter(
            DomainData.id == domain.id).group_by(cls.uid)

    @classmethod
    def search_users_fulltext_full(cls, search_string, limit=None):
        # Filter enabled users
        q = cls.query.filter(cls.enabled == True).order_by(cls.lastname)

        search_string = search_string.strip()

        # Splitting words.
        #   We assert each word must be in the lastname or firstname
        name_clauses = []
        for s in search_string.split(' '):
            name_clauses.append(or_(cls.lastname.like('%%%s%%' % s),
                                    cls.firstname.like('%%%s%%' % s)))

        q = q.filter(or_(cls.email.like('%%%s%%' % search_string),
                         and_(*name_clauses)))

        return q.limit(limit) if limit else q

    @classmethod
    def get_by_role(cls, role_type, enabled=True):
        q = cls.query.join(UserData.roles).filter(
            RoleData.type == role_type)
        return cls._filter_by_enabled(q, enabled)

    @classmethod
    def get_facilitators(cls, enabled=True):
        return cls.get_by_role(RoleType.Facilitator, enabled)

    @classmethod
    def _filter_by_enabled(cls, query, enabled):
        if enabled is not None:  # filter by 'enabled' status
            query = query.filter(cls.enabled == enabled)
        return query

    @classmethod
    def get_by_uid(cls, uid):
        if not uid:
            return None

        user = cls.get(uid)
        if user and user.uid == uid:  # fix DB case-insensivity problems!
            return user
        else:
            return None

    @classmethod
    def get_proxy_ideas(cls, uid):
        return IdeaData.query.outerjoin(IdeaData.proxy_submitter).filter(
            cls.uid == uid).order_by(desc(IdeaData.submission_date))


# -- users' home page settings - -
class HomeSettingsData(Entity, Unpicklable):
    using_options(tablename='home_settings')

    user = ManyToOne('UserData', single_parent=True, inverse='home_settings')

    # FIXME: it would be better to separate the desktop
    #   and mobile settings in two tables

    # desktop version only
    show_progressing_ideas = Field(Boolean, nullable=False, default=True)
    show_tracked_ideas = Field(Boolean, nullable=False, default=True)
    show_challenges_ideas = Field(Boolean, nullable=False, default=True)
    keyword_filter = Field(Unicode(150), nullable=False, default=u'')
    period_filter = Field(Integer, nullable=False, default=0)

    users_filter = ManyToMany('UserData')

    domains = ManyToMany('DomainData')

    # mobile version only
    active_challenge_ideas_limit = Field(Integer, nullable=False, default=5)
    launched_ideas_limit = Field(Integer, nullable=False, default=5)
    progressing_ideas_limit = Field(Integer, nullable=False, default=5)
    domains_ideas_limit = Field(Integer, nullable=False, default=5)


class AuthorData(Entity, Unpicklable):
    using_options(tablename='authors')

    idea = ManyToOne('IdeaData', primary_key=True)
    user = ManyToOne('UserData', primary_key=True)
    position = Field(Integer, nullable=False, default=0)

    def __init__(self, user):
        super(AuthorData, self).__init__()
        self.user = user


class PointData(Entity, Unpicklable):
    using_options(tablename='points')

    user = ManyToOne('UserData', inverse='points')
    # FIXME: rename to "category"
    label = Field(Unicode(150), index=True)
    # identifier of the subject, depend on the label
    subject_id = Field(Unicode(50), nullable=True, default=None)
    reason = Field(Unicode(150))
    nb_points = Field(Integer, nullable=False, default=0)
    date = Field(DateTime)

    def __str__(self):
        return self.label

    def subject_as_string(self):
        if self.subject_id is not None:
            if self.label in (voucher.PointCategory.REMOVE_COMMENT,
                              voucher.PointCategory.ADD_COMMENT):
                # FIXME: when we delete an idea and its comments,
                #   there's no cascade deletion of the points entries,
                #   so we may not find the comment
                comment = CommentData.get(int(self.subject_id))
                return comment.content if comment else ''
            if self.label in (
                voucher.PointCategory.FIRST_CONNECTION,
                    voucher.PointCategory.FIRST_CONNECTION_OF_THE_DAY):
                return _(self.subject_id)
        return ''


class TagData(Entity, Unpicklable):
    using_options(tablename='tags')

    label = Field(Unicode(150), nullable=False, index=True, unique=True)
    ideas = ManyToMany('IdeaData', inverse='tags')

    def __str__(self):
        return self.label


class CommentData(Entity, Unpicklable):
    using_options(tablename='comments')

    created_by = ManyToOne('UserData', required=True)
    idea = ManyToOne('IdeaData', required=True)
    content = Field(UnicodeText, nullable=False)
    attachment = ManyToOne('AttachmentData', single_parent=True,
                           cascade='all,delete-orphan')
    submission_date = Field(DateTime, nullable=False)
    _moderated = Field(Boolean, colname='moderated', nullable=False,
                       default=False)  # comment moderated
    _deleted = Field(Boolean, colname='deleted', nullable=False,
                     default=False)  # comment deleted
    votes = OneToMany('VoteCommentData', cascade='all,delete-orphan')

    def __init__(self, content, idea, created_by, submission_date=None,
                 attachment=None):
        super(CommentData, self).__init__()
        self.content = content
        self.idea = idea
        self.created_by = created_by
        self.submission_date = submission_date or datetime.now()
        self.attachment = attachment

    def __str__(self):
        return self.content[:10]

    # moderation
    @property
    def moderated(self):
        return self._moderated

    @moderated.setter
    def moderated(self, value):
        self._moderated = value
        if self.idea:
            self.idea._comment_visibility_changed(self)

    # deletion
    @property
    def deleted(self):
        return self._deleted

    @deleted.setter
    def deleted(self, deleted):
        self._deleted = deleted
        if self.idea:
            self.idea._comment_visibility_changed(self)

    # visibility
    @property
    def visible(self):
        return not self.moderated and not self.deleted

    # votes
    def add_vote_for_user(self, user, rate=1):
        self.votes.append(
            VoteCommentData(rate=rate, user=user, timestamp=datetime.now()))

    def find_vote_from_user(self, user):
        for vote in self.votes:
            if vote.user.uid == user.uid:
                return vote
        return None


class VoteCommentData(Entity, Unpicklable):
    using_options(tablename='votes_comments')

    comment = ManyToOne('CommentData', primary_key=True)
    user = ManyToOne('UserData', primary_key=True)
    rate = Field(Integer, nullable=False, default=1)
    timestamp = Field(DateTime, nullable=False)


class WFCommentData(Entity, Unpicklable):
    using_options(tablename='wfcomments')

    created_by = ManyToOne('UserData')
    content = Field(UnicodeText)
    submission_date = Field(DateTime)
    idea_wf = ManyToOne('IdeaWFContextData',
                        inverse='comments',
                        required=True)
    from_state = ManyToOne('StateData')
    to_state = ManyToOne('StateData')

    def __str__(self):
        return self.content[:10]


class ChallengeStatus(Enum):
    NotStarted = u'Not started'
    InProgress = u'In progress'
    Finished = u'Finished'


class ChallengeData(Entity, Unpicklable):
    using_options(tablename='challenges')

    # author-related information
    # DIs that will deal with challenge ideas
    associated_dis = ManyToMany('UserData',
                                inverse='di_for_challenges')
    created_by = ManyToOne('UserData')  # author of the challenge
    organization = Field(
        Unicode(150))  # organization/unit that support this challenge

    # descriptions
    title = Field(Unicode(150), nullable=False)  # long title
    short_title = Field(Unicode(
        50))  # short title to use instead of the long one in navigation items
    summary = Field(UnicodeText, nullable=False)  # introduction text
    description = Field(UnicodeText,
                        nullable=False)  # details of the challenge
    # details of the challenge for the mobile version
    mobile_description = Field(UnicodeText,
                               nullable=False)
    outcome = Field(
        UnicodeText)  # when a challenge is finished, announce the results
    _tags = Field(Unicode(100), colname='tags', synonym='tags', nullable=False)

    # dates
    starting_date = Field(DateTime)  # start date of the challenge
    ending_date = Field(DateTime)  # end date of the challenge

    # ideas --> no cascade:
    #   we don't want to delete a challenge if it contains ideas
    ideas = OneToMany('IdeaData')

    def status(self, date=None):
        ref_date = date or datetime.now()
        if ref_date < self.starting_date:
            return ChallengeStatus.NotStarted

        if ref_date >= self.ending_date:
            return ChallengeStatus.Finished

        return ChallengeStatus.InProgress

    def is_active(self, date=None):
        return self.status(date) == ChallengeStatus.InProgress

    @property
    def is_deletable(self):
        return len(self.ideas) == 0

    @property
    def published_ideas(self):
        from eureka.domain.services import get_workflow

        workflow = get_workflow()
        return [idea for idea in self.ideas if
                idea.wf_context.state.label in workflow.get_published_states()]

    @property
    def popularity(self):
        return len(self.published_ideas)

    @property
    def tags(self):
        return [e.strip() for e in self._tags.split(',') if e.strip()]

    @tags.setter
    def tags(self, value):
        self._tags = u','.join([v.strip() for v in value if v.strip()])

    @classmethod
    def count(cls):
        return session.query(func.count(cls.id)).scalar()


class DomainData(Entity, Unpicklable):
    using_options(tablename='domains')

    label = Field(Unicode(150), nullable=False, index=True, unique=True)
    rank = Field(Integer)
    ideas = OneToMany('IdeaData')
    dis = ManyToMany('UserData', inverse='managed_domains')
    en_label = Field(Unicode(150), nullable=False, unique=True)
    fr_label = Field(Unicode(150), nullable=False, unique=True)

    def __str__(self):
        return self.label

    @property
    def published_ideas(self):
        from eureka.domain.services import get_workflow

        workflow = get_workflow()
        return [idea for idea in self.ideas if
                idea.wf_context.state.label in workflow.get_published_states()]

    @property
    def i18n_label(self):
        lang = get_locale().language
        available_langs = [code for code, __ in available_locales]
        lang = lang if lang in available_langs else 'en'
        return getattr(self, '%s_label' % lang)


class RoleType(Enum):
    Facilitator = u'facilitator'
    Developer = u'developer'
    DSIG = u'dsig'
    MobileAccess = u'mobile_access'


RoleLabels = {
    RoleType.Facilitator: _L("FACILITATOR_ROLE"),
    RoleType.Developer: _L("DEVELOPER_ROLE"),
    RoleType.DSIG: _L("DSIG_ROLE"),
    RoleType.MobileAccess: _L("MOBILE_ACCESS_ROLE"),
}


class RoleData(Entity, Unpicklable):
    using_options(tablename='roles')

    type = Field(Unicode(50), primary_key=True)  # should be a RoleType
    user = ManyToOne('UserData', primary_key=True)

    def __init__(self, type=None, user=None):
        super(RoleData, self).__init__()
        self.type = type
        self.user = user

    def __repr__(self):
        return "RoleData(%r,%r)" % (self.type, self.user)

    def __str__(self):
        return self.type


class PollData(Entity, Unpicklable):
    using_options(tablename='polls')

    title = Field(Unicode(50), nullable=False)
    question = Field(Unicode(150), nullable=False)
    enabled = Field(Boolean, default=False, nullable=False)
    multiple = Field(Boolean, default=False, nullable=False)
    end_date = Field(DateTime, nullable=False)
    choices = OneToMany('PollChoiceData', cascade='all,delete-orphan')

    @property
    def votes(self):
        return [vote for choice in self.choices for vote in choice.votes]


class PollChoiceData(Entity, Unpicklable):
    using_options(tablename='polls_choices')

    label = Field(Unicode(150), nullable=False)
    poll = ManyToOne('PollData', required=True)
    votes = OneToMany('VotePollData', cascade='all,delete-orphan')


class VotePollData(Entity, Unpicklable):
    using_options(tablename='votes_polls')

    choice = ManyToOne('PollChoiceData', primary_key=True)
    user = ManyToOne('UserData', inverse='votes_for_polls', primary_key=True)


class EvalCommentData(Entity, Unpicklable):
    using_options(tablename='evalcomments')

    created_by = ManyToOne('UserData', required=True)
    expert = ManyToOne('UserData', required=True)
    content = Field(UnicodeText, nullable=False)
    submission_date = Field(DateTime, nullable=False)
    idea_context = ManyToOne('IdeaEvalContextData')

    def __str__(self):
        return self.content[:10]


class ImprovementData(Entity, Unpicklable):
    using_options(tablename='improvements')

    user = ManyToOne('UserData')
    domain = ManyToOne('ImprovementDomainData')
    content = Field(UnicodeText)
    submission_date = Field(DateTime)
    visible = Field(Boolean, nullable=False, default=True)
    state = Field(Unicode(150))  # see ImprovementState


class ImprovementState(Enum):
    NEW = None
    RUNNING = u'RUNNING'
    TREATED = u'TREATED'
    REJECTED = u'REJECTED'


class ImprovementDomainData(Entity, Unpicklable):
    using_options(tablename='improvement_domains')

    label = Field(Unicode(150), nullable=False, index=True, unique=True)
    rank = Field(Integer)
    improvements = OneToMany('ImprovementData')

    def __str__(self):
        return self.label


class EventType(object):
    CommentAdded = u'COMMENT_ADDED'
    StateChanged = u'STATE_CHANGED'


class EventStatus(object):
    New = u'New'
    Read = u'Read'
    Hidden = u'Hidden'


class EventData(Entity, Unpicklable):
    using_options(tablename='events')

    user = ManyToOne('UserData', inverse='events', required=True)
    label = Field(Unicode(150), nullable=False)
    date = Field(DateTime, nullable=False)
    idea = ManyToOne('IdeaData', inverse='events', required=True)
    status = Field(Unicode(20), nullable=False,
                   default=EventStatus.New)  # EventStatus

    def __init__(self, label, user, idea, date=None, status=EventStatus.New):
        super(EventData, self).__init__()
        self.label = label
        self.user = user
        self.idea = idea
        self.date = date or datetime.now()
        self.status = status


class TimeLineData(Entity, Unpicklable):
    using_options(tablename='timeline', inheritance='multi')

    user = ManyToOne('UserData', inverse='events', required=True)
    date = Field(DateTime, default=datetime.now())

    def get_type(self):
        return None


class TimeLineIdeaData(TimeLineData):
    using_options(tablename='timeline_idea', inheritance='multi')

    target = ManyToOne('IdeaData', required=True)

    def get_type(self):
        return 'IDEA'


class TimeLineUserData(TimeLineData):
    using_options(tablename='timeline_user', inheritance='multi')

    target = ManyToOne('UserData', required=True)

    def get_type(self):
        return 'USER'


class StateData(Entity, Unpicklable):
    using_options(tablename='states')

    label = Field(Unicode(150))
    state_for = OneToMany('IdeaWFContextData', inverse='state')
    step = ManyToOne('StepData', inverse="step_for")

    def __str__(self):
        return self.label

    @classmethod
    def get_ideas_count_by_states(cls, states=()):
        q = session.query(
            cls.label.label('state'),
            func.count(IdeaWFContextData.id).label('count')
        )
        if states:
            q = q.filter(cls.label.in_(states))

        q = q.outerjoin(cls.state_for)
        q = q.outerjoin(cls.step)
        q = q.group_by(cls.label)
        q = q.order_by(StepData.rank, cls.id)

        return q


class StepData(Entity, Unpicklable):
    using_options(tablename='steps')

    label = Field(Unicode(150))
    rank = Field(Integer)
    step_for = OneToMany('StateData', inverse='step')


class ArticleType(Enum):
    News = u'News'
    Ongoing = u'Ongoing'
    Headline = u'Headline'


class ArticleTopicData(Entity, Unpicklable):
    using_options(tablename='article_topics')
    label = Field(Unicode(100), nullable=False, index=True, unique=True)
    key = Field(Unicode(50), nullable=False)
    default = Field(Boolean)
    articles = OneToMany('ArticleData', inverse='topic')


class ArticleData(Entity, Unpicklable):
    using_options(tablename='articles')

    type = Field(Unicode(20), nullable=False)
    # topic = Field(Unicode(100), nullable=False)
    title = Field(Unicode(100), nullable=False)
    creation_date = Field(DateTime, nullable=True)
    # FIXME: move the thumbnail into the gallery?
    thumbnail_filename = Field(Unicode(100))
    content = Field(UnicodeText, nullable=False)
    mobile_content = Field(UnicodeText, nullable=False)
    rank = Field(Integer, nullable=False)
    published = Field(Boolean)
    _tags = Field(Unicode(100), colname='tags', synonym='tags', nullable=False)
    topic = ManyToOne('ArticleTopicData', inverse='articles', required=True)

    def __str__(self):
        return (self.title[:50] + '...') if len(
            self.title > 50) else self.title

    @property
    def tags(self):
        return [e.strip() for e in self._tags.split(',') if e.strip()]

    @tags.setter
    def tags(self, value):
        self._tags = u','.join([v.strip() for v in value if v.strip()])

    @classmethod
    def get_articles(cls, published=None, article_type=None,
                     article_topic=None, max_items=None, start=None):
        q = cls.query
        if published is not None:
            q = q.filter_by(published=published)
        if article_type:
            q = q.filter_by(type=article_type)
        if article_topic:
            q = q.join(cls.topic).filter(
                ArticleTopicData.label == article_topic)
        q = q.order_by(cls.rank)

        if start:
            q = q.offset(start)

        if max_items:
            q = q.limit(max_items)
        return q


class GalleryImageData(Entity, Unpicklable):
    using_options(tablename='gallery_images')

    filename = Field(Unicode(100), nullable=False)
    checksum = Field(Unicode(32), nullable=False)
    created_on = Field(DateTime, nullable=False)
    tags = ManyToMany('GalleryImageTagData',
                      tablename='gallery_image_tags',
                      inverse='images',
                      local_colname='image_id',
                      remote_colname='tag_id')

    def __init__(self, filename, data):
        super(GalleryImageData, self).__init__()
        assert not self.exist(data)
        self.filename = tools.fix_filename(filename)
        self.checksum = tools.compute_md5(data)
        self.created_on = datetime.now()
        self.tags = []
        self._write_image(self.filename, data)
        self._write_image(self.thumbnail_filename,
                          self._create_thumbnail(data))

    @classmethod
    def exist(cls, data):
        """Check wether the image already exist in the gallery and return it"""
        return cls.get_by(checksum=tools.compute_md5(data))

    @property
    def thumbnail_filename(self):
        return '%s-tb%s' % os.path.splitext(self.filename)

    def _gallery_path(self, filename):
        return get_fs_service().expand_path(['gallery', filename])

    def _write_image(self, filename, data):
        with open(self._gallery_path(filename), 'wb') as target:
            print >> target, data

    def _create_thumbnail(self, data):
        return tools.create_thumbnail(data, 92, 92)

    @property
    def data(self):
        return open(self._gallery_path(self.filename), 'rb').read()

    @before_delete
    def _remove_old_file(self):
        if self.filename is not None:
            os.remove(self._gallery_path(self.filename))
            os.remove(self._gallery_path(self.thumbnail_filename))


class GalleryImageTagData(Entity, Unpicklable):
    using_options(tablename='gallery_tags')

    name = Field(Unicode(100), nullable=False, index=True, unique=True)
    images = ManyToMany('GalleryImageData', inverse='tags')


# ------------------ Not persistent entities ------------------
class UserGroup(object):
    """
    Represents a group of users. Useful for classifying users into categories
    (when rendering user related
    aggregate information) or for applying changes in batches.
    """

    def __init__(self, name, organizations=None, specific_users=None):
        from eureka.domain.repositories import UserRepository
        super(UserGroup, self).__init__()
        self.name = name
        self.organizations = organizations or []
        self.specific_users = specific_users or []
        self.user_repository = UserRepository()
        self._users = None

    # logger
    @property
    def log(self):
        return log.get_logger('.' + __name__)

    @property
    def users(self):
        if self._users is None:
            self._users = self._find_users()
        return self._users

    def _find_users(self):
        users = []
        self.log.debug('Fetching users in group %s' % self.name)
        for organization in self.organizations:
            users.extend(self._find_users_by_organization(organization))
        for user in self.specific_users:
            users.append(self._find_user_by_uid(user))
        return users

    def apply(self, func):
        """
        Apply a function to each user. The function will be called
        with a user as parameter.
        """
        for user in self.users:
            func(user)

    def _find_user_by_uid(self, user_uid):
        user = UserData.get_by_uid(user_uid)
        if not user:
            self.log.warning("No user found with the login %s" % user_uid)
        return user

    def _find_users_by_organization(self, organization_tuple):
        # find the corresponding users
        users = self.user_repository.get_by_organization(*organization_tuple)
        if not users:
            self.log.warning(
                "No user found in the organization %s" % organization_tuple)
        return users


# reminders
class ReminderType(Enum):
    UnchangedState = u'unchanged_state'


class ReminderData(Entity, Unpicklable):
    using_options(tablename='reminders')

    idea = ManyToOne('IdeaData', inverse='reminders')
    type = Field(Unicode(150), nullable=False)
    date = Field(DateTime, nullable=False)
    # we may add recipients and a description later...


class PendingEmailMessageData(Entity, Unpicklable):
    using_options(tablename='pending_email_messages')

    user = ManyToOne('UserData', inverse='pending_email_messages')
    creation_date = Field(DateTime, nullable=False)
    subject = Field(Unicode(200), nullable=False)
    content = Field(UnicodeText, nullable=False)

    def __init__(self, subject, content, user=None, creation_date=None):
        creation_date = creation_date or datetime.now()
        super(PendingEmailMessageData, self).__init__(
            user=user,
            subject=subject,
            content=content,
            creation_date=creation_date
        )
