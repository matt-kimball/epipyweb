#!/usr/bin/env python3
#
#    epipyweb - Epipylon web user interface
#    Copyright (C) 2017  Matt Kimball
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

import http.client
import json
import os
import tempfile
import typing
import unittest

from typing import *


DATABASE_FILENAME = '/var/lib/epipyweb/dns.db'
DATABASE_BACKUP_FILENAME = '/var/lib/epipyweb/dns.backup.db'
TEST_LOCK_FILENAME = '/var/lib/epipyweb/dns.test-lock'


class LogImportError(Exception):
    pass


def write_dns_line(
        log: typing.IO,
        date: str,
        value: str,
        host: str) -> None:

    'Write a DNS query line to the simulated log file in dnsmasq format'

    line = date + ' sys dnsmasq[1]: query[A] ' + value + ' from ' + host + '\n'
    log.write(line)


def write_dhcp_line(
        log: typing.IO,
        date: str,
        ip_address: str,
        mac_address: str,
        hostname: str) -> None:

    'Write a simulated DHCP address assignment log line'

    line = date + ' sys dnsmasq-dhcp[1]: DHCPACK(eth0) ' + ip_address + \
        ' ' + mac_address + ' ' + hostname + '\n'
    log.write(line)


def generate_test_log() -> str:

    'Generate a syslog with DNS queries for testing'

    filename = tempfile.mktemp('log', 'epipywebtest')

    with open(filename, "w") as log:
        write_dhcp_line(
            log, 'Jan  1 08:00:00', '192.168.1.1',
            '01:01:01:01:01:01', 'device-name')
        write_dns_line(
            log, 'Jan  1 09:00:00', 'www.example.com', '192.168.1.1')

    return filename


class GetQueryGroupTest(unittest.TestCase):

    'Check that we can retrieve DNS query groups'

    def setUp(self) -> None:

        '''Back up the existing database and create a simulated database
        of DNS queries'''

        lock_file = open(TEST_LOCK_FILENAME, 'w')
        lock_file.close()

        try:
            os.rename(DATABASE_FILENAME, DATABASE_BACKUP_FILENAME)
        except FileNotFoundError:
            pass

        log_filename = generate_test_log()
        try:
            if os.system('python3 record/import-syslog.py ' + log_filename):
                raise LogImportError()
        finally:
            os.unlink(log_filename)

    def tearDown(self) -> None:

        'Restore the backed up database'

        try:
            os.unlink(DATABASE_FILENAME)
        except FileNotFoundError:
            pass

        try:
            os.rename(DATABASE_BACKUP_FILENAME, DATABASE_FILENAME)
        except FileNotFoundError:
            pass

        try:
            os.unlink(TEST_LOCK_FILENAME)
        except FileNotFoundError:
            pass

    def test_latest(self) -> None:

        'Test that we can get a page of DNS query groups'

        conn = http.client.HTTPConnection("localhost")
        try:
            conn.request("GET", "/q/dnsquerygroup")
            response_str = conn.getresponse().read().decode('utf-8')
        finally:
            conn.close()

        response = json.loads(response_str)
        self.assertEqual(response['groups'][0]['value'], 'www.example.com')
        self.assertEqual(response['groups'][0]['host'], 'device-name')


if __name__ == '__main__':
    unittest.main()
