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

"""RSS (0.91, 0.92, 1.1 and 2.0) renderer"""

from nagare.namespaces import xml
from nagare.namespaces.xml import TagProp

# Official RSS namespaces
NS090 = "http://my.netscape.com/rdf/simple/0.9/"
NS091 = "http://purl.org/rss/1.0/modules/rss091#"
NS11 = "http://purl.org/net/rss1.1#"
NS2 = "http://backend.userland.com/RSS2"

NS_BLOGCHANNEL = "http://backend.userland.com/blogChannelModule"

DOCS = "http://cyber.law.harvard.edu/rss/rss.html"


class RssRenderer(xml.XmlRenderer):
    """ The RSS renderer
    """

    # The RSS tags
    # ------------

    rss = TagProp('rss', set(('version',)))

    channel = TagProp('channel', set())
    title = TagProp('title', set())
    link = TagProp('link', set())
    description = TagProp('description', set())
    language = TagProp('language', set())
    copyright = TagProp('copyright', set())
    managingEditor = TagProp('managingEditor', set())
    webMaster = TagProp('webMaster', set())
    pubDate = TagProp('pubDate', set())
    lastBuildDate = TagProp('lastBuildDate', set())
    category = TagProp('category', set())
    generator = TagProp('generator', set())
    docs = TagProp('docs', set())
    cloud = TagProp('cloud', set(('domain', 'port', 'path',
                                  'registerProcedure', 'protocol')))
    ttl = TagProp('ttl', set())

    image = TagProp('image', set())
    url = TagProp('url', set())
    width = TagProp('width', set())
    height = TagProp('height', set())

    rating = TagProp('rating', set())

    textInput = TagProp('textInput', set())
    name = TagProp('name', set())

    skipHours = TagProp('skipHours', set())
    skipDays = TagProp('skipDays', set())

    item = TagProp('item', set())
    title = TagProp('title', set())
    link = TagProp('link', set())
    description = TagProp('description', set())
    author = TagProp('author', set())
    category = TagProp('category', set(('domain',)))
    comments = TagProp('comments', set())
    enclosure = TagProp('enclosure', set(('url', 'length', 'type')))
    guid = TagProp('guid', set(('isPermaLink',)))
    pubDate = TagProp('pubDate', set())
    source = TagProp('source', set(('url',)))
