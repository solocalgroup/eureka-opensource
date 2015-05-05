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

from eureka.domain.populate import import_article_topics_csv
from optparse import OptionParser, NO_DEFAULT


def set_options(optparser):
    optparser.usage = " [application] ..."
    optparser.add_option('-c', '--csv-file', dest='csv_filepath',
                         default=NO_DEFAULT, help='CSV filepath')


def _validate(options):
    if len(args) != 1:
        ValueError('Bad number of parameters')

    if options.csv_filepath is None:
        ValueError('csv_filepath not given!')


def populate():
    """Import article topics from a given CSV file"""
    parser = OptionParser(usage='Usage: %prog [options]',
                          description=populate.__doc__)
    set_options(parser)
    (__, __) = parser.parse_args()
    options = parser.values

    with open(options.csv_filepath) as csv_file:
        import_article_topics_csv(csv_file)


populate()
session.commit()
