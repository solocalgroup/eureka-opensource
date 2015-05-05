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

import ntpath
import re
import string
import sys
from datetime import datetime

from nagare.validator import Validator
from nagare import validator
from nagare.i18n import _L, _N

from eureka.domain.repositories import UserRepository
from eureka.infrastructure.tools import is_string, remove_duplicates, \
    find_duplicates


# mail regex extracted from http://www.regular-expressions.info/email.html
# MAIL_RE = r"(?i)^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$"
# identifier regex
IDENTIFIER_RE = r"^[A-Za-z][A-Za-z0-9]*$"

email_text = string.ascii_letters + string.digits + "!#$%&'*+-/=?^_`{|}~"
email_domain = string.ascii_letters + string.digits + ".-"
email_ip_re = re.compile(r'^\[(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\]$')
email_re = re.compile(r'"[^"]*"@')


def validateEmail(a):
    local_part, i, domain_part = a.rpartition('@')

    return _is_local(local_part) and _is_domain(domain_part)


def _is_local(part):
    """
    Test if the first part of an email address is valid (i.e. before `@`).
    """
    # replace some valid characters by `_` email like:
    # "Fred Bloggs"@example.com -> _@example.com
    # name.lastname@domain.com -> name_lastname@domain.com
    part = re.sub(r'\.', '_', part)
    part = re.sub(r'"[^"]+"', '_', part)

    if '@' in part:
        # No `@` authorized in email first part
        return False

    if len(part) == 0:
        # First part must not be empty
        return False

    # replace newlines emails like:
    # 'Test \\' + chr(10) + ' Folding \\' + chr(10) + ' Whitespace@example.com'
    # -> 'Test_Folding_Whitespace@example.com'
    part = re.sub(r' +\\\n ', '_', part)

    return len([x for x in part if x not in email_text]) == 0


def _is_domain_ip(domain_name):
    # Check if domain_name is a valid IP address
    m = email_ip_re.match(domain_name)
    if m:
        if (len([int(i) for i in m.groups()
                 if i.isdigit() and int(i) < 256]) != 4):
            # a valid IP is a list of 4 integers between 0 and 255
            return False
        return True

    if email_ip_re.match('[%s]' % domain_name):
        # ip need to be between []
        return False

    # domain_name is not an IP address or even a bad IP address we
    # delegate validation
    return None


def _is_domain_parts(domain_name):
    parts = domain_name.split('.')

    # Count numbert of parts in domain_name
    if len(parts) < 2:
        # nb parts should be at least 2
        return False

    if len(parts[-1]) < 2 or len(parts[-1]) > 6:
        # top level extension should have a length between 2 and 6
        # (i.e. .com, .fr, .museum, .travel) an extensive list is available for
        # stricter validation http://data.iana.org/TLD/tlds-alpha-by-domain.txt
        return False

    tainted_parts = []

    for part in parts:
        if len(part) == 0:
            # parts of domain_name cannot be empty
            return False

        if part.startswith('-') or part.endswith('-'):
            # `-` cannot start or end a part
            return False

        # Add current part to a "bad" list if characters are not valid in
        # email domain
        tainted_parts.append(''.join(
            [p for p in part if p not in email_domain]))

    if len(''.join(tainted_parts)) > 0:
        # at least one part as non valid characters
        return False

    return True


def _is_domain(domain_name):
    """
    Test if the NDD part of an email address is valid (i.e. after `@`).
    """

    # remove comments from domain_name, email like this are valide:
    # HM2Kinsists@(that comments are allowed)this.is.ok
    domain_name = re.sub(r'\([^()]*\)', '', domain_name)

    # Test if domain_name seems like an IP address
    check = _is_domain_ip(domain_name)
    if check is not None:
        return check

    # domain_name should now validate as a true Domain Name
    return _is_domain_parts(domain_name)


def remove_invalid_chars(value):
    """
    Remove invalid characters from `value`:
    - invalid XML characters (see http://en.wikipedia.org/wiki/XML)
    - invalid Unicode codepoints
    """
    # See http://stackoverflow.com/questions/1707890/fast-way-to-filter-illegal-xml-unicode-chars-in-python
    if value is None:
        return None

    illegal_unichrs = (
        (0x00, 0x08),
        (0x0B, 0x1F),
        (0x7F, 0x84),
        (0x86, 0x9F),
        (0xD800, 0xDFFF),
        # we also forbid the private use area
        (0xE000, 0xF8FF),
        (0xFDD0, 0xFDDF),
        (0xFFFE, 0xFFFF),
        (0x1FFFE, 0x1FFFF),
        (0x2FFFE, 0x2FFFF),
        (0x3FFFE, 0x3FFFF),
        (0x4FFFE, 0x4FFFF),
        (0x5FFFE, 0x5FFFF),
        (0x6FFFE, 0x6FFFF),
        (0x7FFFE, 0x7FFFF),
        (0x8FFFE, 0x8FFFF),
        (0x9FFFE, 0x9FFFF),
        (0xAFFFE, 0xAFFFF),
        (0xBFFFE, 0xBFFFF),
        (0xCFFFE, 0xCFFFF),
        (0xDFFFE, 0xDFFFF),
        (0xEFFFE, 0xEFFFF),
        (0xFFFFE, 0xFFFFF),
        (0x10FFFE, 0x10FFFF)
    )

    illegal_ranges = ["%s-%s" % (unichr(low), unichr(high))
                      for (low, high) in illegal_unichrs
                      if low < sys.maxunicode]

    illegal_xml_re = re.compile(u'[%s]' % u''.join(illegal_ranges))

    return illegal_xml_re.sub('', value)


class DateValidator(validator.Validator):
    """A validator for date fields"""

    def __init__(self, v, format='%d/%m/%Y',
                 msg=_L(u'Should be a date formatted as dd/mm/yyyy')):
        """Initialization

        Date validator for input fields validation.

        In:
          - ``v`` -- value to validate
          - ``date_format`` -- a python date formatting string such as '%d/%m/%Y'
        """
        self.format = format
        try:
            self.value = datetime.strptime(v, self.format) if v else None
        except (ValueError, TypeError):
            raise ValueError(msg)

    def not_empty(self, msg=_L(u"Can't be empty")):
        if self.value is not None:
            return self
        raise ValueError(msg)

    def lesser_than(self, max_date, msg=_L(u'Must be lesser than %s')):
        if self.value < max_date:
            return self
        raise ValueError(msg % max_date.strftime(self.format))

    def lesser_or_equal_than(self, max_date,
                             msg=_L(u'Must be lesser than or equal to %s')):
        if self.value <= max_date:
            return self
        raise ValueError(msg % max_date.strftime(self.format))

    def greater_than(self, min_date, msg=_L(u'Must be greater than %s')):
        if self.value > min_date:
            return self
        raise ValueError(msg % min_date.strftime(self.format))

    def greater_or_equal_than(self, min_date,
                              msg=_L(u'Must be greater than or equal to %s')):
        if self.value >= min_date:
            return self
        raise ValueError(msg % min_date.strftime(self.format))

    def to_date(self):
        return self.value

    __call__ = to_date


def date(date):
    return DateValidator(date).to_date()


def non_empty_date(date):
    return DateValidator(date).not_empty().to_date()


def validate_file(data, max_size=None,
                  msg=_L(u'Size must be less than %d KB')):
    """
    Validate a 'file' input data against the max size in KB
    """
    # check against the first roundtrip with the client
    if data is None or is_string(data):
        return None

    if data.done == -1:
        raise ValueError(_L(u'Transfer was interrupted'))

    # gets the file size (it's a StringIO)
    data.file.seek(0, 2)  # 0 from EOF
    filesize = data.file.tell()
    data.file.seek(0)

    if max_size is not None and filesize > max_size * 1024:
        raise ValueError(msg % max_size)

    filedata = data.file.read()
    filename = ntpath.basename(unicode(data.filename))

    return {'filename': filename,
            'filedata': filedata,
            'content_type': unicode(data.type)}


class ExtendedStringValidator(validator.StringValidator):
    def __init__(self, v, strip=True, rstrip=False, lstrip=False, chars=None,
                 msg=_L(u'Must be a string')):
        # fix a nagare bug where StringValidator accepts None but fail in the not_empty check
        if v is not None and not is_string(v):  # we accept None or a string
            raise ValueError(msg)
        if v is None:  # strip will crash if the given value is None...
            strip = False

        super(ExtendedStringValidator, self).__init__(remove_invalid_chars(v),
                                                      strip, rstrip, lstrip,
                                                      chars)

    def not_empty(self, msg=_L(u"Can't be empty")):
        if self.value:
            return self

        raise ValueError(msg)

    def is_email(self, msg=_L(u"Must be an email address")):
        """Check that the value is an email

        In:
          - ``msg`` -- message to raise

        Return:
          - ``self``
        """
        if not self.value:
            return self

        if validateEmail(self.value):
            return self

        raise ValueError(msg)

    def is_user_email(self, msg=_L(u"No user with this email")):
        """Check that there is a known user with this email

        In:
          - ``msg`` -- message to raise

        Return:
          - ``self``
        """
        if not self.value:
            return self

        if not UserRepository().get_by_email(self.value):
            raise ValueError(msg)

        return self

    def is_unused_email(self, msg=_L(u'Email already used')):
        """Check that there is no user with this email

        In:
          - ``msg`` -- message to raise

        Return:
          - ``self``
        """
        if not self.value:
            return self

        if UserRepository().get_by_email(self.value):
            raise ValueError(msg)

        return self

    def is_unused_uid(self, msg=_L(u'User id already used')):
        """Check that there is no user with this identifier

        In:
          - ``msg`` -- message to raise

        Return:
          - ``self``
        """
        if not self.value:
            return self

        if UserRepository().get_by_uid(self.value):
            raise ValueError(msg)

        return self

    def is_identifier(self, msg=_L('Should start with an ASCII letter and '
                                   'contain only ASCII letters or digits')):
        """Validate an identifier"""
        if not self.value:
            return self

        return self.match(IDENTIFIER_RE, msg)


class ExtendedIntValidator(validator.IntValidator):
    def __init__(self, v, msg=_L(u'Must be an integer'), *args, **kw):
        try:
            super(ExtendedIntValidator, self).__init__(v, *args, **kw)
        except ValueError:
            raise ValueError(msg)


class FloatValidator(Validator):
    def __init__(self, v, *args, **kw):
        """Initialisation

        Check that the value is an float or empty

        In:
          - ``v`` -- value to validate
        """
        super(FloatValidator, self).__init__(v, *args, **kw)

        try:
            if self.value:
                self.value = float(self.value)
        except (ValueError, TypeError):
            raise ValueError(_L(u'Must be a float'))

    def to_float(self):
        """Return the value, converted to a float or ''

        Return:
          - the integer value
        """
        return self.value

    __call__ = to_float


# shortcuts
def integer(v):
    return ExtendedIntValidator(v).to_int()


def positive_integer(v):
    return ExtendedIntValidator(v).greater_than(0, _L(
        u"Must be greater than %(min)d")).to_int()


def positive_or_null_integer(v):
    return ExtendedIntValidator(v).greater_or_equal_than(0, _L(
        u"Must be greater than %(min)d")).to_int()


def string(t):
    return ExtendedStringValidator(t).to_string()


def non_empty_string(t):
    return ExtendedStringValidator(t).not_empty(
        _L(u"Can't be empty")).to_string()


def _email_validator(t, required=False):
    email_validator = ExtendedStringValidator(t)
    if required:
        email_validator = email_validator.not_empty(_L(u"Can't be empty"))
    return email_validator.is_email()


def email(t, required=True):
    return _email_validator(t, required).to_string()


def user_email(t, required=False):
    return _email_validator(t, required).is_user_email().to_string()


def unused_email(t, required=False):
    return _email_validator(t, required).is_unused_email().to_string()


def _uid_validator(t, required=True):
    uid_validator = ExtendedStringValidator(t)
    if required:
        uid_validator = uid_validator.not_empty(_L(u"Can't be empty"))
    return uid_validator.is_identifier().shorter_than(50)


def uid(t, required=True):
    return _uid_validator(t, required).to_string()


def unused_uid(t, required=True):
    return _uid_validator(t, required).is_unused_uid().to_string()


def check_duplicates(values):
    duplicates = find_duplicates(values)
    if duplicates:
        duplicates_str = ', '.join(map(str, duplicates))
        raise ValueError(_N(u"Duplicate value: %s",
                            u"Duplicate values: %s",
                            len(duplicates)) % duplicates_str)
    return values


def in_words_list(text, separator=',', required=False, duplicates='warn',
                  words=()):
    values = word_list(text, separator=separator, required=required,
                       duplicates=duplicates)

    bad_words = set(values) - set(words)

    if bad_words:
        bad_words = list(bad_words)
        if len(bad_words) < 2:
            raise ValueError(_L(u"%s is not a valid value") % bad_words[0])
        else:
            raise ValueError(
                _L(u"%s are not valid values") % ', '.join(bad_words))

    return values


def word_list(text, separator=',', required=False, duplicates='warn'):
    if not text:
        if required:
            raise ValueError(_L(u"Can't be empty"))
        return []

    words = [item.strip() for item in text.split(separator) if
             item.strip() != '']

    duplicates_handlers = {
        'ignore': (lambda w: w),
        'warn': check_duplicates,
        'remove': remove_duplicates,
    }
    return duplicates_handlers[duplicates](words)


def user_email_list(text, separator=',', check_user_email=True):
    """Validate a list of email addresses between commas"""
    emails = [item.strip() for item in text.split(separator) if
              item.strip() != '']

    if not emails:
        raise ValueError(_L(u"Can't be empty"))

    for email in emails:
        if not validateEmail(email):
            raise ValueError(_L(u"%s is not a valid email address") % email)
        if check_user_email and not UserRepository().get_by_email(email):
            raise ValueError(
                _L(u"There's no user with this email address: %s") % email)

    return emails
