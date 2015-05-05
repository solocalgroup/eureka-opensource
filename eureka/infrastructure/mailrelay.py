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

"""This module implements an email relay: the emails received by the SMTP server are automatically transfered to the inbox
of a specific IMAP account.

Launch with:
~/mail_server.py -H localhost -p 10025 -i localhost -q 993 -s -u eureka -a
eureka -l smtpd.log
"""

from smtpd import SMTPServer
import asyncore
import imaplib
import time
from optparse import OptionParser
import os
import logging.handlers
import sys


# FIXME: move this out of the eureka application. This has nothing to do with the eureka application itself

LOGGER_NAME = 'mailrelay'


class IMAPServer(SMTPServer):
    def __init__(self, localaddr, remoteaddr, logger):
        SMTPServer.__init__(self, localaddr, remoteaddr)
        self.log = logger

    def process_message(self, peer, mailfrom, rcpttos, data):
        (imap_serv, imap_port, imap_ssl, imap_user, imap_auth) = self._remoteaddr

        self.log.debug('IMAP informations %s' % str((imap_serv, imap_port, imap_ssl,
                                                     imap_user, imap_auth)))

        try:
            if imap_ssl:
                M = imaplib.IMAP4_SSL(imap_serv, imap_port)
                self.log.debug('Using IMAP over SSL)')
            else:
                M = imaplib.IMAP4(imap_serv, imap_port)
                self.log.debug('Using IMAP with no SSL')

            M.login(imap_user, imap_auth)
            M.select()
            self.log.info("Send mail :: %s" % str(data))
            M.append('INBOX', '', imaplib.Time2Internaldate(time.time()), str(data))

            M.close()
            M.logout()
        except:
            self.log.exception('Failed to send the message to the IMAP mailbox:')


def configure_logger(log_file, verbose=True):
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    if log_file and os.path.exists(log_file):
        handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=20 * 1024, backupCount=5)
    else:
        handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.addHandler(handler)
    return logger


def main():
    parser = OptionParser(usage="Usage: %prog [options]", description="simple smtp_server")
    parser.add_option("-H", "--smtp-host", dest="smtp_host", default="localhost", help="SMTP host bind")
    parser.add_option("-p", "--smtp-port", dest="smtp_port", type="int", default=10025, help="SMTP port")
    parser.add_option("-i", "--imap-host", dest="imap_host", default="", help="IMAP host")
    parser.add_option("-q", "--imap-port", dest="imap_port", type="int", default=143, help="IMAP port")
    parser.add_option("-s", action="store_true", dest="imap_ssl", default=False, help="IMAP ssl")
    parser.add_option("-u", "--imap-user", dest="imap_user", default="", help="IMAP auth user")
    parser.add_option("-a", "--imap-auth", dest="imap_auth", default="", help="IMAP auth password")
    parser.add_option("-l", "--log-file", dest="log_file", default=None, help="log file")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="verbose mode")

    options = parser.parse_args()[0]
    logger = configure_logger(options.log_file, options.verbose)

    IMAPServer((options.smtp_host, options.smtp_port),
               (options.imap_host, options.imap_port, options.imap_ssl, options.imap_user, options.imap_auth),
               logger)

    logger.info('Server is listening...')
    asyncore.loop()


# call main
if __name__ == '__main__':
    main()
