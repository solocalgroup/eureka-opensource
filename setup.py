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

import os

from setuptools import setup, find_packages
from setuptools import Distribution


def find_data_files(top):
    result = []
    for (root, dirs, files) in os.walk(top):
        files = [os.path.join(root, fn) for fn in files]

        if files:
            result.append((root, files))

    return result


def get_requirements():
    requirements_filepath = os.path.join(os.path.dirname(__file__),
                                         "requirements.txt")
    with open(requirements_filepath) as reqs:
        requirements = tuple(r.strip() for r in reqs.readlines() if r.strip())

    return requirements


setup(
    name='eureka-opensource',
    version='1.0.1',
    author='Solocal Group',
    author_email='eureka@solocal.com',
    description='Innovative think tank web application',
    license='CeCILL',
    keywords='innovation,web,application',
    url='https://eureka-opensource.solocalgroup.com',
    packages=find_packages(),
    include_package_data=True,
    data_files=find_data_files('data')
    + find_data_files('static')
    + find_data_files('conf')
    + find_data_files('contrib')
    + find_data_files(os.path.join('eureka', 'tests', 'data')),  # Required to run tests
    zip_safe=False,
    install_requires=get_requirements(),
    test_suite='eureka.tests',
    entry_points="""
    [nagare.applications]
    eureka = eureka.app:desktop_app
    [eureka.templates]
    default = eureka.ui.templates.default
    [eureka.workflow]
    default = eureka.domain.workflow
    [eureka.workflow_menu]
    default = eureka.ui.desktop.workflow.security
    [eureka.search_engine]
    solr = eureka.domain.services:SolrEngine
    dummy = eureka.domain.services:DummySearchEngine
    whoosh = eureka.domain.services:WhooshEngine
    """,
)
