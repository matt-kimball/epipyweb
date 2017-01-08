#!/usr/bin/env python3

import argparse
import datetime
import os
import re
import sqlite3
import sys
import typing


QUERY_GROUP_TIME_TOLERANCE = 60
QUERY_GROUP_EXTENDED_TIME = 60 * 60


def parse_cmdline() -> argparse.Namespace:

    'Parse the commandline, collecting syslog paths to import'

    parser = argparse.ArgumentParser(
        description='Import syslog to epipyweb database')

    parser.add_argument(
        'logfiles', metavar='logfile', nargs='+',
        help='log files to import')

    return parser.parse_args()


def syslog_time_to_datetime(
        syslog_time: str) -> datetime.datetime:

    'Give a time in syslog format, convert to a datetime object'

    now = datetime.datetime.now()
    logday = datetime.datetime.strptime(syslog_time, '%b %d %H:%M:%S')

    logtime_year_now = datetime.datetime(
        now.year, logday.month, logday.day,
        logday.hour, logday.minute, logday.second)
    logtime_year_last = datetime.datetime(
        now.year - 1, logday.month, logday.day,
        logday.hour, logday.minute, logday.second)

    #  Since we don't get a year from syslog, assume it was either this
    #  year or last.  This year if the date has passed already, otherwise
    #  last.
    if logtime_year_now > now:
        logtime = logtime_year_last
    else:
        logtime = logtime_year_now

    return logtime


def isotime_to_datetime(
        isotime: str) -> datetime.datetime:

    'Convert a string in ISO 8601 time format to a datetime object'

    return datetime.datetime.strptime(isotime, '%Y-%m-%dT%H:%M:%S')


def list_domains(
        hostname: str) -> typing.Iterator[str]:

    'Iterate over the subdomains in a domain name with two or more components'

    components = hostname.split('.')
    num = len(components)
    for i in range(2, num):
        yield str.join('.', components[num - i:num])


def is_value_already_in_query_group(
        db: sqlite3.Connection,
        group_id: int,
        query_value: str) -> bool:

    '''Returns true if the query value is used by one of the
    DNS queries in the given query group'''

    cursor = db.cursor()
    try:
        cursor.execute(
            'SELECT id FROM dnsquery' +
            ' WHERE group_id = ? AND value = ?' +
            ' LIMIT 1',
            (group_id, query_value))

        return cursor.fetchone() is not None
    finally:
        cursor.close()


def is_query_in_group(
        db: sqlite3.Connection,
        group_id: int,
        query_time: datetime.datetime,
        query_value: str,
        start_time: datetime.datetime,
        end_time: datetime.datetime) -> bool:

    'Is the query time in the existing range?'

    if start_time <= query_time and query_time <= end_time:
        return True
    elif start_time < query_time:
        diff_time = query_time - start_time

        #  Is the time within the tolerance of the end time?
        if diff_time.days == 0 and \
                diff_time.seconds < QUERY_GROUP_TIME_TOLERANCE:
            return True

        if diff_time.days == 0 and \
                diff_time.seconds < QUERY_GROUP_EXTENDED_TIME and \
                is_value_already_in_query_group(db, group_id, query_value):
            return True

    return False


def log_dns_query_group(
        db: sqlite3.Connection,
        querytime_iso: str,
        queryvalue: str,
        queryhost: str) -> int:

    '''Find the query group which a new query belongs to, or create
    a new group for the query'''

    cursor = db.cursor()
    try:
        cursor.execute(
            'SELECT id, start_time, end_time FROM querygroup' +
            ' WHERE host = ? AND start_time <= ?' +
            ' ORDER BY end_time DESC LIMIT 1',
            (queryhost, querytime_iso))

        row = cursor.fetchone()
        if row:
            (group_id, start_time_iso, end_time_iso) = row

            start_time = isotime_to_datetime(start_time_iso)
            end_time = isotime_to_datetime(end_time_iso)
            querytime = isotime_to_datetime(querytime_iso)

            if is_query_in_group(
                    db, group_id, querytime, queryvalue,
                    start_time, end_time):
                return group_id

        cursor.execute(
            'INSERT INTO querygroup (start_time, end_time, host)' +
            ' VALUES (?,?,?)',
            (querytime_iso, querytime_iso, queryhost))
        group_id = cursor.lastrowid
        return group_id
    finally:
        cursor.close()


def log_dns_query(
        db: sqlite3.Connection,
        querytime: str,
        querytype: str,
        queryvalue: str,
        host: str) -> None:

    'Store the DNS query in the database'

    logtime = syslog_time_to_datetime(querytime)
    isotime = logtime.isoformat()

    cursor = db.cursor()
    try:
        group_id = log_dns_query_group(db, isotime, queryvalue, host)

        cursor.execute(
            'INSERT INTO dnsquery (group_id, time, type, value, host)' +
            ' VALUES (?,?,?,?,?)',
            (group_id, isotime, querytype, queryvalue, host))
        query_id = cursor.lastrowid

        #  Update the group start time
        cursor.execute(
            'UPDATE querygroup SET start_time =' +
            ' (SELECT MIN(time) FROM dnsquery WHERE group_id = ?)' +
            ' WHERE id = ?',
            (group_id, group_id))

        #  Update the group end time
        cursor.execute(
            'UPDATE querygroup SET end_time =' +
            ' (SELECT MAX(time) FROM dnsquery WHERE group_id = ?)' +
            ' WHERE id = ?',
            (group_id, group_id))

        #  Associate the subdomains with the query
        for subdomain in list_domains(queryvalue):
            querydomain = (query_id, isotime, subdomain)
            db.execute(
                'INSERT INTO querydomain (query_id, time, domain)' +
                ' VALUES (?,?,?)',
                querydomain)
    finally:
        cursor.close()


def import_log(
        db: sqlite3.Connection,
        logpath: str) -> None:

    'Match all the DNS query lines in the logfile and store them in the DB'

    time_re = r'([A-Za-z]+ +[0-9]+ +[0-9:]+)'
    dnsmasq_re = r'dnsmasq\[[0-9]+\]'
    query_re = r'query\[([A-Z]+)\] ([A-Za-z0-9-.]+) from ([0-9a-f:.]+)'
    dns_query_re = r'%s .* %s: %s' % (time_re, dnsmasq_re, query_re)

    linecount = 0
    with open(logpath) as logfile:
        for logline in logfile:
            match = re.match(dns_query_re, logline)
            if not match:
                continue

            log_dns_query(db, *match.groups())

            linecount += 1
            if linecount % 100 == 0:
                sys.stdout.write('.')
                sys.stdout.flush()

    sys.stdout.write('\n')


def create_tables(
        db: sqlite3.Connection) -> None:

    'Create tables and indices for the DNS database'

    columns = '(id INTEGER PRIMARY KEY, host, start_time, end_time)'
    db.execute('CREATE TABLE querygroup ' + columns)
    db.execute(
        'CREATE INDEX querygroup_start_time ON querygroup (start_time)')
    db.execute(
        'CREATE INDEX querygroup_end_time ON querygroup (end_time)')
    db.execute(
        'CREATE INDEX querygroup_host_start_time' +
        ' ON querygroup (host, start_time)')
    db.execute(
        'CREATE INDEX querygroup_host_end_time' +
        ' ON querygroup (host, end_time)')

    columns = \
        '(id INTEGER PRIMARY KEY, group_id INTEGER, time, type, value, host)'
    db.execute('CREATE TABLE dnsquery ' + columns)
    db.execute('CREATE INDEX dnsquery_group_id ON dnsquery (group_id, value)')
    db.execute('CREATE INDEX dnsquery_time ON dnsquery (time)')
    db.execute('CREATE INDEX dnsquery_value ON dnsquery (value)')
    db.execute('CREATE INDEX dnsquery_host ON dnsquery (host)')

    columns = '(query_id INTEGER, time, domain)'
    db.execute('CREATE TABLE querydomain ' + columns)
    db.execute('CREATE INDEX querydomain_query_id ON querydomain (query_id)')
    db.execute('CREATE INDEX querydomain_domain ON querydomain (domain)')


def main() -> None:

    'Given a list of logfiles, record all their DNS queries'

    args = parse_cmdline()

    try:
        os.unlink('dns.db')
    except FileNotFoundError:
        pass

    db = sqlite3.connect('dns.db')
    try:
        create_tables(db)

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
