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

import argparse
import contextlib
import datetime
import os
import re
import sqlite3
import sys

import epipydb

from typing import *


def parse_cmdline() -> argparse.Namespace:

    'Parse the commandline, collecting syslog paths to import'

    parser = argparse.ArgumentParser(
        description='Import syslog to epipyweb database')

    parser.add_argument(
        'logfiles', metavar='logfile', nargs='+',
        help='log files to import')

    return parser.parse_args()


def import_log(
        db: sqlite3.Connection,
        logpath: str) -> None:

    'Match all the DNS query lines in the logfile and store them in the DB'

    linecount = 0
    with open(logpath) as logfile:
        for logline in logfile:
            epipydb.log_line(db, logline)

            linecount += 1
            if linecount % 100 == 0:
                sys.stdout.write('.')
                sys.stdout.flush()

    sys.stdout.write('\n')


def main() -> None:

    'Given a list of logfiles, record all their DNS queries'

    args = parse_cmdline()

    with contextlib.closing(epipydb.open_database()) as db:
        success = True
        for log in args.logfiles:
            try:
                import_log(db, log)
                db.commit()
            except IOError as e:
                err = sys.argv[0] + ': ' + log + ' ' + str(e) + '\n'
                sys.stderr.write(err)
                success = False

        if not success:
            sys.exit(1)


if __name__ == '__main__':
    main()
