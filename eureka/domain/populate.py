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

import csv
import os
import sys

from eureka.app import BaseApplication
from eureka.domain.models import (ArticleTopicData, DomainData,
                                  ImprovementDomainData, OrganizationData,
                                  OrganizationType, RoleType, StateData,
                                  StepData)
from eureka.domain.repositories import UserRepository
from eureka.domain.services import get_workflow
from eureka.infrastructure.unicode_csv import UnicodeDictReader
from eureka.infrastructure.users import get_default_users
from eureka.pkg import resource_filename, resource_stream
from nagare.admin.util import read_application_options
from nagare.database import session


def populate_organization_types(types):
    for type in types:
        OrganizationType(type)


def populate_organizations(csv_filepath):
    delimiter = None

    with open(csv_filepath, 'rb') as csv_file:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(csv_file.readline())
        delimiter = dialect.delimiter

    if not delimiter:
        raise ValueError("Unknown CSV delimiter!")

    with open(csv_filepath, 'rb') as csv_file:
        for row in UnicodeDictReader(csv_file, delimiter=delimiter):
            corporation_name = row["corporation_name"]
            direction_name = row["direction_name"]
            service_name = row["service_name"]
            site_name = row["site_name"]

            if not corporation_name:
                continue
            corporation = get_or_create_organization(
                corporation_name, u'corporation', None
            )

            if not direction_name:
                continue
            direction = get_or_create_organization(
                direction_name, u'direction', corporation
            )

            if not service_name:
                continue
            service = get_or_create_organization(
                service_name, u'service', direction
            )

            if not site_name:
                continue
            site = get_or_create_organization(
                site_name, u'site', service
            )


def populate_steps():
    wfsteps = get_workflow().WFSteps

    steps = (
        (wfsteps.NO_STEP, 100),
        (wfsteps.SUBMITTED_STEP, 1),
        (wfsteps.STUDY_STEP, 2),
        (wfsteps.SUGGESTED_STEP, 3),
        (wfsteps.SELECTED_STEP, 4),
        (wfsteps.PROJECT_STEP, 5),
        (wfsteps.PROTOTYPE_STEP, 6),
        (wfsteps.EXTENDED_STEP, 7)
    )

    for label, rank in steps:
        StepData(label=label, rank=rank)

    session.flush()


def populate_states():
    workflow = get_workflow()
    WFSteps = workflow.WFSteps
    WFStates = workflow.WFStates

    states = (
        (WFStates.INITIAL_STATE, WFSteps.NO_STEP),
        (WFStates.DRAFT_STATE, WFSteps.NO_STEP),
        (WFStates.FI_NORMALIZE_STATE, WFSteps.SUBMITTED_STEP),
        (WFStates.AUTHOR_NORMALIZE_STATE, WFSteps.SUBMITTED_STEP),
        (WFStates.DI_APPRAISAL_STATE, WFSteps.STUDY_STEP),
        (WFStates.RETURNED_BY_DI_STATE, WFSteps.STUDY_STEP),
        (WFStates.DI_APPROVED_STATE, WFSteps.SUGGESTED_STEP),
        (WFStates.SELECTED_STATE, WFSteps.SELECTED_STEP),
        (WFStates.PROJECT_STATE, WFSteps.PROJECT_STEP),
        (WFStates.PROTOTYPE_STATE, WFSteps.PROTOTYPE_STEP),
        (WFStates.EXTENDED_STATE, WFSteps.EXTENDED_STEP),
        (WFStates.FI_REFUSED_STATE, WFSteps.SUBMITTED_STEP),
        (WFStates.PROTOTYPE_REFUSED_STATE, WFSteps.PROTOTYPE_STEP),
        (WFStates.DI_REFUSED_STATE, WFSteps.STUDY_STEP),
        (WFStates.PROJECT_REFUSED_STATE, WFSteps.PROJECT_STEP),
        (WFStates.SELECT_REFUSED_STATE, WFSteps.SELECTED_STEP),
        (WFStates.APPROVAL_REFUSED_STATE, WFSteps.SUGGESTED_STEP),
        (WFStates.DSIG_BASKET_STATE, WFSteps.NO_STEP),
    )

    for label, step in states:
        step = StepData.get_by(label=step)
        StateData(label=label, step=step)

    session.flush()


def populate_users(default_users):
    """Populate the default users (special accounts)"""
    facilitator_uid = default_users['FACILITATOR']
    developer_uid = default_users['DEVELOPER']
    admin_uid = default_users['ADMIN']
    innovator_uid = default_users['INNOVATOR']
    special_users = (
        (facilitator_uid, facilitator_uid,
            facilitator_uid.capitalize(), facilitator_uid.capitalize(),
            u'{}@eureka-open.com'.format(facilitator_uid), facilitator_uid,
            [RoleType.Facilitator]),
        (developer_uid, developer_uid, u'Ideas', developer_uid.capitalize(),
            u'{}@eureka-open.com'.format(developer_uid), facilitator_uid,
            [RoleType.Developer]),
        (admin_uid, admin_uid, admin_uid.capitalize(), u'Eureka',
            u'{}@eureka-open.com'.format(admin_uid), facilitator_uid,
            [RoleType.DSIG]),
        (innovator_uid, innovator_uid, innovator_uid.capitalize(), u'User',
            u'{}@eureka-open.com'.format(innovator_uid), facilitator_uid,
            []),
    )

    for (uid, password, firstname, lastname,
            email, fi_uid, roles) in special_users:
        user = UserRepository().create(
            uid=uid,
            password=password,
            firstname=firstname,
            lastname=lastname,
            email=email,
            fi_uid=fi_uid
        )
        for role in roles:
            user.add_role(role)

        session.flush()


def populate_articles():
    ArticleTopicData(label=u'Article', key=u'article', default=True)


def import_improvement_domains_csv(csv_file):
    reader = UnicodeDictReader(csv_file, delimiter=';')

    for line in reader:
        d = ImprovementDomainData.query.filter(
            ImprovementDomainData.label == line['label']).first()
        if d is None:
            d = ImprovementDomainData()
            d.label = line['label'].strip()
            d.rank = int(line['rank'].strip())

    session.flush()


def import_domains_csv(csv_file):
    reader = UnicodeDictReader(csv_file, delimiter=';')

    for line in reader:
        d = DomainData()
        d.label = line['label'].strip()
        d.rank = int(line['rank'].strip())
        d.en_label = line['en_label'].strip()
        d.fr_label = line['fr_label'].strip()

    session.flush()


def import_article_topics_csv(csv_file):
    reader = UnicodeDictReader(csv_file, delimiter=';')

    for row in reader:
        article = ArticleTopicData()
        article.label = row['label'].strip()
        article.key = row['key'].strip()
        article.default = int(row['default'].strip())

    session.flush()


def _get_organization_type(name):
    return OrganizationType.get_by(label=name)


def get_or_create_organization(name, type_name, parent=None):
    org_type = _get_organization_type(type_name)
    organization = OrganizationData.get_by(
        label=name, type=org_type, parent=parent
    )

    if not organization:
        organization = OrganizationData(
            label=name, type=org_type, parent=parent
        )

    return organization


def populate():
    populate_steps()
    populate_states()
    populate_users(get_default_users())
    populate_articles()
    populate_organization_types(
        [u'corporation', u'direction', u'service', u'site'])

    csv_file = os.path.join('data', 'fixtures', 'organizations.csv')
    populate_organizations(resource_filename(csv_file))

    csv_file = os.path.join('data', 'fixtures', 'domains.csv')
    import_domains_csv(resource_stream(csv_file))

    csv_file = os.path.join('data', 'fixtures', 'improvement_domains.csv')
    import_improvement_domains_csv(resource_stream(csv_file))

    csv_file = os.path.join('data', 'fixtures', 'article_topics.csv')
    import_article_topics_csv(resource_stream(csv_file))
