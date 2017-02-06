#!/usr/bin/env python3

import contextlib
import os
import sys
import syslog
import traceback

import epipydb

from typing import *


def syslog_trace(
        trace: str) -> None:

    '''Log a python stack trace to syslog, to be used when we have an
    unhandled exception.'''

    log_lines = trace.split('\n')
    for line in log_lines:
        if len(line):
            syslog.syslog(line)


def test_lock_held() -> bool:

    '''Check to see if the testing lock file is held, indicating
    we shouldn't be logging anything to avoid interfering with testing.'''

    try:
        os.stat(epipydb.TEST_LOCK_FILENAME)

        return True
    except FileNotFoundError:
        return False


def handle_log_line(
        line: str) -> None:

    'Commit a single log line to the database'

    with contextlib.closing(epipydb.open_database()) as db:
        if not test_lock_held():
            epipydb.log_line(db, line)
            db.commit()


def main() -> None:

    'Record dnsmasq syslog lines to the epipyweb database'

    for line in sys.stdin:
        try:
            handle_log_line(line)
        except:
            syslog_trace(traceback.format_exc())


if __name__ == '__main__':
    main()
