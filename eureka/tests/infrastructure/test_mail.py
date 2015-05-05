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

import unittest

import peak.rules

from eureka.infrastructure import mail


# decorates mail:smtp_send to collect its parameter and check data is correct
smtp_data = None


@peak.rules.around(mail.Mailer._smtp_send)
def collect_smtp_send_data(next_method, self, from_, to, msg):
    global smtp_data
    smtp_data = [self.smtp_host, self.smtp_port, from_, to,
                 extract_mail_fields(msg.as_string())]


class TestMail(unittest.TestCase):
    def test_cc_recipients(self):
        """
        Test if the 'Cc:' recipients are correctly handled.
        """
        mailer = mail.get_mailer()
        mailer.activated = True
        mailer.smtp_host = '<dummy_host>'
        mailer.smtp_port = 25
        mailer.hidden_recipients = []

        expected_host = mailer.smtp_host
        expected_port = mailer.smtp_port

        # checks with Cc: recipients
        mailer.send_mail('Welcome on board!', 's.d@netng', ['a.b@netng'],
                         'Welcome!', ['c.d@netng', 'e.f@netng'])

        expected_to = ['a.b@netng', 'c.d@netng', 'e.f@netng']
        expected_fields = {'Subject:': 'Welcome on board!',
                           'To:': 'a.b@netng',
                           'Cc:': 'c.d@netng, e.f@netng'}
        self.assert_smtp_send_data_equal('s.d@netng', expected_to, expected_fields, expected_host, expected_port)

        # checks without Cc: recipients
        mailer.send_mail('Welcome on board!', 's.d@netng', ['a.b@netng'], 'Welcome!')

        expected_to = ['a.b@netng']
        expected_fields = {'Subject:': 'Welcome on board!',
                           'To:': 'def1@netng, def2@netng', 'Cc:': None}

        # self.assert_smtp_send_data_equal('s.d@netng', expected_to, expected_fields, expected_host, expected_port)

    def assert_smtp_send_data_equal(self,
                                    expected_from, expected_to,
                                    expected_fields, expected_host, expected_port):

        # checks the enveloppe
        self.assertEquals(expected_host, smtp_data[0])
        self.assertEquals(expected_port, smtp_data[1])
        self.assertEquals(expected_from, smtp_data[2])
        self.assertEquals(expected_to, smtp_data[3])

        # checks the contents
        expected_fields['From:'] = expected_from
        self.assertEquals(expected_fields, smtp_data[4])


def extract_mail_fields(contents):
    fields = {'Subject:': None, 'From:': None, 'To:': None, 'Cc:': None}

    for l in contents.splitlines():
        for f in fields:
            if fields[f] is None and l.startswith(f):
                fields[f] = l.replace(f + ' ', '')

    return fields
