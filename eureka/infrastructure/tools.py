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

from cStringIO import StringIO
from datetime import datetime
import hashlib
import os
import re
import unicodedata
import string
import imghdr
import webob
import random

try:
    from PIL import Image
except ImportError:
    import Image


def create_timestamp(date):
    return date.strftime('%Y%m%d%H%M%S%f')


def remove_duplicates(values):
    """Remove duplicates while keeping the values in order"""
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)
    return result


def find_duplicates(values):
    """Find duplicates in a list of values"""
    seen = set()
    duplicates = []
    for value in values:
        if value in seen:
            duplicates.append(value)
        else:
            seen.add(value)
    return duplicates


def create_unique_file(path, filename, mode='wb'):
    """Return a new file in the specified path, return a (file-like object, name) pair"""
    timestamp = create_timestamp(datetime.now())
    basename, extension = os.path.splitext(filename)
    unique_filename = '%s-%s%s' % (basename, timestamp, extension)
    filepath = os.path.join(path, unique_filename)
    return open(filepath, mode), unique_filename


def generate_id(prefix='id'):
    """Generate a unique id"""
    return prefix + str(random.randint(10000000, 99999999))


def is_integer(arg):
    try:
        int(arg)
        return True
    except (TypeError, ValueError):
        return False


def is_string(arg):
    return isinstance(arg, basestring)


def limit_string(msg, limit):
    l = msg.split()
    last = len(l)
    res = ''
    i = 0
    while len(res) < limit and i < last:
        res += (' ' + l[i])
        i += 1
    if len(res) < len(msg):
        res += ' ...'
    return res


def fix_filename(filename):
    safe_chars = set("-_.() %s%s" % (string.ascii_letters, string.digits))
    cleaned_filename = unicodedata.normalize('NFKD', unicode(filename)).encode('ascii', 'ignore')
    return u''.join(c for c in cleaned_filename if c in safe_chars)


_HTML_CHARACTERS = {
    "&": "&amp;",
    '"': "&quot;",
    # "'": "&#39",
    ">": "&gt;",
    "<": "&lt;",
}


def to_ascii(text):
    text = text if isinstance(text, unicode) else unicode(text)
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore')


def html_escape(text):
    """Produce entities within text."""
    return "".join(_HTML_CHARACTERS.get(c, c) for c in text)


def html_unescape(text):
    """
    Remove entities from text and replace them by the corresponding characters
    """
    for c, e in _HTML_CHARACTERS.items():
        text = text.replace(e, c)
    return text

# match text that look like http/https urls even if they are not valid urls (we don't care)
# inspired from http://daringfireball.net/2010/07/improved_regex_for_matching_urls
_URL_REGEX = re.compile(r"""
(?xi)
\b
(
https?://
[^\s`!\[\]{}\(\);'"<>«»“”‘’]*[^\s`!\[\]{}\(\);:'",<>«»“”‘’.]
)
""")


def text_to_html(text):
    """Transform a (formatted) text to an html string"""
    # we may use a wiki formatting engine (markdown, creole, mediawiki, ...) if new requirements come later

    # urls transformation, first step
    text = _URL_REGEX.sub(r'LINK_TO_URL{\1}', text)
    # escape html special characters
    text = html_escape(text)
    # urls transformation, second step
    text = re.sub(r'LINK_TO_URL{([^}]*)}', r'<a href="\1">\1</a>', text)
    # end of line characters
    text = re.sub(r'\n', r'<br/>', text)

    return text


def text_to_html_elements(h, text):
    return h.parse_htmlstring(text_to_html(text), fragment=True, xhtml=True)


def remove_silently(*paths):
    failed_paths = []

    for path in paths:
        if path:  # handle path = None for simplicity of cleanup in the caller
            try:
                os.remove(path)
            except OSError:
                failed_paths.append(path)

    return failed_paths


def log_progress(log, i, count, template, every_percents=10):
    if i == count - 1:
        log(template % 100)
    elif count >= every_percents:
        (div, mod) = divmod(i, count / every_percents)
        if mod == 0 and (div * every_percents < 100):
            log(template % (div * every_percents))


def compute_md5(data):
    m = hashlib.md5()
    m.update(data)
    return unicode(m.hexdigest())


def create_thumbnail(source, width, height, format='PNG'):
    if width is None and height is None:
        raise ValueError('Either the width or the height must be set')

    if isinstance(source, str):
        source = StringIO(source)

    img = Image.open(source)
    # convert to RGB (in case the source image is in CMYK for example)
    img = img.convert('RGB')

    if width is None:
        width = img.size[0]
    elif height is None:
        height = img.size[1]

    img.thumbnail((width, height), Image.ANTIALIAS)
    i = StringIO()
    img.save(i, format)
    return i.getvalue()


def read_file(path):
    with open(path, 'rb') as f:
        return f.read()


def write_file(path, data):
    with open(path, 'wb') as f:
        f.write(data)


def redirect_to(location='/', permanent=False, base_url=''):
    if location.startswith('/'):
        location = base_url + location
    response = webob.exc.HTTPMovedPermanently if permanent else webob.exc.HTTPSeeOther
    return response(location=location)


def serve_static_content(path):
    from eureka.infrastructure.content_types import view_content_response

    # static content delivery for standalone mode
    try:
        data = read_file(path)
    except IOError:
        raise webob.exc.HTTPNotFound()

    # FIXME: this is no more image specific
    # ctype = mimetypes.guess_type(p)[0]
    image_format = 'image/' + (imghdr.what(None, data[:32]) or '*')
    response = view_content_response(image_format, data)
    response.cache_expires(seconds=1800)
    raise response


def percentage(count, total):
    if total == 0:
        return 0.0
    return float(count * 100) / float(total)


def group_as_dict(iterable, key_func):
    """
    Kind of group by function that group items from an iterable by key_func and returns a mapping from a key
    to the list of items that share this key
    """
    result = {}
    for item in iterable:
        result.setdefault(key_func(item), []).append(item)
    return result


class EnumMeta(type):
    def keys(self):
        return [item for item in dir(self) if not item.startswith('_')]

    def values(self):
        return [getattr(self, key) for key in self.keys()]

    def __contains__(self, value):
        return value in self.values()

    def __iter__(self):
        return (value for value in self.values())


class Enum(object):
    """
    Inherit from this class to define an enumeration. That way, you could call ``in`` to test if an value is in
    the enumeration

    Example:
        >>> class BinaryDigits(Enum):
        ...   Zero, One = range(2)

        >>> BinaryDigits.Zero in BinaryDigits
        True

        >>> 1 in BinaryDigits
        True

        >>> 'invalid' in BinaryDigits
        False
    """
    __metaclass__ = EnumMeta


class NiceReprMixin(object):
    """Mixin that provides a nice repr method"""
    def __repr__(self):
        attributes = ["%s=%r" % (k, v) for k, v in self.__dict__.items() if not k.startswith('_')]
        return "<%s(%s)>" % (self.__class__.__name__, ', '.join(attributes))
