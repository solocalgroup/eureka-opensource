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

from optparse import OptionParser
import textwrap
from sqlalchemy.orm import eagerload
from nagare import log
from eureka.domain.repositories import UserRepository, IdeaRepository
from eureka.batch import configure


def rebuild_indexes(logger):
    global apps
    logger.info('Creating search indexes')
    search_engine = apps['eureka'].search_engine
    search_engine.clear()

    logger.info('Re-indexing ideas')
    # We index *all* ideas. We are safe because results are filtered by 'published' status
    ideas = IdeaRepository().get_all().options(
        eagerload('tags'), eagerload('authors_association')).all()
    search_engine.index_many(ideas)

    logger.info('Re-indexing users')
    users = UserRepository().get_all()
    search_engine.index_many(users)

    logger.info('Done')


def main():
    # configure the batch environment
    configure()

    # parse the command line
    description = """
    Rebuild the search indexes
    """
    parser = OptionParser(usage='Usage: %prog [options]',
                          description=textwrap.dedent(description).strip())
    (__, __) = parser.parse_args()

    # start the re-indexing
    rebuild_indexes(log.get_logger())


# call main
main()
