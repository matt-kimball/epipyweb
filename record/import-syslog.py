#!/usr/bin/env python3

import argparse
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

    db = epipydb.open_database()
    try:
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
    finally:
        db.close()


if __name__ == '__main__':
    main()
