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

END = -1


class UnbalancedError(Exception):
    pass


class OpenTag:
    def __init__(self, tag, rest=''):
        self.tag = tag
        self.rest = rest

    def as_string(self):
        return '<' + self.tag + self.rest + '>'


class CloseTag(OpenTag):
    def as_string(self):
        return '</' + self.tag + '>'


class SelfClosingTag(OpenTag):
    pass


class Tokenizer:
    def __init__(self, input):
        self.input = input
        # points at the next unconsumed character of the input
        self.counter = 0

    def __next_char(self):
        self.counter += 1
        return self.input[self.counter]

    def next_token(self):
        try:
            char = self.input[self.counter]
            self.counter += 1
            if char == '&':
                return self.__entity()
            elif char != '<':
                return char
            elif self.input[self.counter] == '/':
                self.counter += 1
                return self.__close_tag()
            else:
                return self.__open_tag()
        except IndexError:
            return END

    def __entity(self):
        """Return a token representing an HTML character entity.
        Precondition: self.counter points at the charcter after the &
        Postcondition: self.counter points at the character after the ;
        """
        char = self.input[self.counter]
        entity = ['&']
        while char != ';':
            entity.append(char)
            char = self.__next_char()
        entity.append(';')
        self.counter += 1
        return ''.join(entity)

    def __open_tag(self):
        """Return an open/close tag token.
        Precondition: self.counter points at the first character of the tag
                      name
        Postcondition: self.counter points at the character after the <tag>
        """
        char = self.input[self.counter]
        tag = []
        rest = []
        while char != '>' and char != ' ':
            tag.append(char)
            char = self.__next_char()
        while char != '>':
            rest.append(char)
            char = self.__next_char()
        if self.input[self.counter - 1] == '/':
            self.counter += 1
            return SelfClosingTag(''.join(tag), ''.join(rest))
        else:
            self.counter += 1
            return OpenTag(''.join(tag), ''.join(rest))

    def __close_tag(self):
        """Return an open/close tag token.
        Precondition: self.counter points at the first character of the tag
                      name
        Postcondition: self.counter points at the character after the <tag>
        """
        char = self.input[self.counter]
        tag = []
        while char != '>':
            tag.append(char)
            char = self.__next_char()
        self.counter += 1
        return CloseTag(''.join(tag))


def truncate(str, target_len, ellipsis=''):
    """Returns a copy of str truncated to target_len characters,
    preserving HTML markup (which does not count towards the length).
    Any tags that would be left open by truncation will be closed at
    the end of the returned string.  Optionally append ellipsis if
    the string was truncated."""
    # open tags are pushed on here, then popped when the matching
    # close tag is found
    stack = []
    # string to be returned
    retval = []
    # number of characters (not counting markup) placed in retval so far
    length = 0
    tokens = Tokenizer(str)
    tok = tokens.next_token()
    while tok != END:
        if not length < target_len:
            retval.append(ellipsis)
            break
        if tok.__class__.__name__ == 'OpenTag':
            stack.append(tok)
            retval.append(tok.as_string())
        elif tok.__class__.__name__ == 'CloseTag':
            if stack[-1].tag == tok.tag:
                stack.pop()
                retval.append(tok.as_string())
            else:
                raise UnbalancedError(tok.as_string())
        elif tok.__class__.__name__ == 'SelfClosingTag':
            retval.append(tok.as_string())
        else:
            retval.append(tok)
            length += 1
        tok = tokens.next_token()
    while len(stack) > 0:
        tok = CloseTag(stack.pop().tag)
        retval.append(tok.as_string())
    return ''.join(retval)
