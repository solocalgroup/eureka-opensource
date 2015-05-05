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

import solr
from eureka.domain.models import IdeaData, UserData
from whoosh import query, writing
from whoosh.analysis import CharsetFilter, NgramFilter, StemmingAnalyzer
from whoosh.fields import ID, Schema, TEXT
from whoosh.index import create_in, EmptyIndexError, open_dir
from whoosh.qparser import QueryParser
from whoosh.support.charset import accent_map

__search_engine = None


def set_search_engine(search_engine):
    global __search_engine
    __search_engine = search_engine


def get_search_engine():
    return __search_engine


class IndexableIdea(object):
    def __init__(self, idea):
        self.type = u'idea'
        self.id = unicode(idea.id)
        self.title = idea.title
        self.description = idea.description
        self.tags = u','.join(tag.label for tag in idea.tags)
        self.creators = u' '.join(author.fullname for author in idea.authors)


class IndexableUser(object):
    def __init__(self, user):
        self.type = u'user'
        self.id = unicode(user.uid)
        self.firstname = user.firstname or u''
        self.lastname = user.lastname or u''
        business_unit_attrs = (
            'corporation_label',
            'direction_label',
            'service_label',
            'site_label'
        )
        self.business_unit = u' '.join(
            self._get(user, attr) for attr in business_unit_attrs
        )
        self.position = user.position
        self.competencies = user.competencies
        description_attrs = ('competencies', 'expertises',
                             'hobbies', 'specialty')
        self.description = u' '.join(
            self._get(user, attr) for attr in description_attrs
        )

    def _get(self, user, attr):
        return getattr(user, attr, None) or u''


def find_index_wrapper(obj):
    wrappers = {
        UserData: IndexableUser,
        IdeaData: IndexableIdea
    }
    return wrappers[obj.__class__](obj)


class DummySearchEngine(object):

    SPEC = {}

    def __init__(self, **kwargs):
        pass

    def clear(self):
        pass

    def index(self, obj):
        pass

    def index_many(self, objs):
        pass

    def remove(self, obj):
        pass

    def search(self, type, pattern, start=0, rows=10, default_field='text'):
        assert type in ('idea', 'user'), "Type %r not supported" % type
        return [], 0


class SafeSolr(solr.Solr):
    """Context manager used to ensure the connection is closed"""
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()


class SolrEngine(DummySearchEngine):
    SPEC = {
        'uri': 'string(default="http://localhost:8983/solr")',
        'timeout': 'integer(default=5)',
        'max_retries': 'integer(default=3)',
    }

    def __init__(self, **kwargs):
        super(SolrEngine, self).__init__()
        self.uri = kwargs['uri']
        self.timeout = kwargs['timeout']
        self.max_retries = kwargs['max_retries']

    def _conn(self):
        return SafeSolr(self.uri, timeout=5, max_retries=3)

    def clear(self):
        with self._conn() as conn:
            conn.delete_query('*:*', commit=True)

    def index(self, obj):
        with self._conn() as conn:
            conn.add(find_index_wrapper(obj).__dict__, commit=True)

    def index_many(self, objs):
        with self._conn() as conn:
            conn.add_many(
                (find_index_wrapper(obj).__dict__ for obj in objs),
                commit=True
            )

    def remove(self, obj):
        with self._conn() as conn:
            conn.delete(id=find_index_wrapper(obj).id, commit=True)

    def _make_query(self, pattern):
        words = [w.strip() for w in pattern.split(' ')]
        q = []
        for w in words:
            if w.startswith('*') or w.startswith('?'):
                w = w[1:]
            q.append(w)
        return ' '.join(q)

    def search(self, type, pattern, start=0, rows=10, default_field='text'):
        """Perform a search
        In:
            - ``type`` -- the type of document to return
                (currently 'user' or 'idea' supported)
            - ``pattern`` -- the searched string
            - ``start`` -- return the results starting on 'start'
                (for batching purpose)
            - ``rows`` -- the max number of results we want
        Return:
            - the result ids
            - the number of total results (doesn't depend on rows value)
        """
        assert type in ('idea', 'user'), "Type %r not supported" % type
        with self._conn() as conn:
            query = self._make_query(pattern)
            response = conn.select(
                query,
                fq='type:%s' % type, fields=['id'],
                start=start,
                rows=rows,
                df=default_field
            )
            return [item['id'] for item in response.results], response.numFound


class WhooshEngine(DummySearchEngine):
    """Search engine using Whoosh backend"""
    SPEC = {
        'dir': 'string(default="")',
    }

    def __init__(self, **kwargs):
        super(WhooshEngine, self).__init__()

        analyzer = (
            StemmingAnalyzer()
            | CharsetFilter(accent_map)
            | NgramFilter(minsize=4, maxsize=10)
        )
        self.schema = Schema(
            id=ID(stored=True),
            title=TEXT(stored=True, field_boost=5.0, analyzer=analyzer),
            firstname=TEXT(stored=True, field_boost=2.0, analyzer=analyzer),
            lastname=TEXT(stored=True, field_boost=2.0, analyzer=analyzer),
            type=ID(stored=True),
            description=TEXT(stored=True, analyzer=analyzer),
            creators=TEXT(stored=False, analyzer=analyzer),
            tags=TEXT(stored=False, analyzer=analyzer),
            business_unit=TEXT(stored=False, analyzer=analyzer),
            position=TEXT(stored=False, analyzer=analyzer),
            competencies=TEXT(stored=False, analyzer=analyzer),
            text=TEXT(stored=True, analyzer=analyzer))

        self.dir = kwargs['dir']
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)
        try:
            self._index = open_dir(self.dir)
        except EmptyIndexError:
            self._index = create_in(self.dir, self.schema)

    def clear(self):
        with self._index.writer() as writer:
            writer.mergetype = writing.CLEAR

    def index(self, obj, writer=None):
        # Is there an equivalent of Solr copyField in Whoosh ?
        self.remove(obj, writer=writer)
        obj_dict = find_index_wrapper(obj).__dict__
        obj_dict['text'] = u' '.join(v for v in obj_dict.values() if v)

        if writer:
            writer.add_document(**obj_dict)
        else:
            with self._index.writer() as writer:
                writer.add_document(**obj_dict)

    def index_many(self, objs):
        with self._index.writer() as writer:
            for obj in objs:
                self.index(obj, writer=writer)

    def remove(self, obj, writer=None):
        if writer:
            writer.delete_by_term('id', find_index_wrapper(obj).id)
        else:
            with self._index.writer() as writer:
                writer.delete_by_term('id', find_index_wrapper(obj).id)

    def search(self, type, pattern, start=0, rows=10, default_field='text'):
        assert type in ('idea', 'user'), "Type %r not supported" % type
        with self._index.searcher() as searcher:
            q = QueryParser(
                default_field,
                schema=self._index.schema
            ).parse(pattern)

            results = searcher.search(
                q,
                limit=max(start + rows, 1),
                filter=query.Term('type', type)
            )
            return (
                [item['id'] for item in results[start:start + rows]],
                len(results)
            )
