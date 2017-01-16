import datetime
import re
import os
import sqlite3

from typing import *


DATABASE_PATH = '/var/lib/epipyweb/dns.db'
TEST_LOCK_FILENAME = '/var/lib/epipyweb/dns.test-lock'


QUERY_GROUP_TIME_TOLERANCE = 60
QUERY_GROUP_EXTENDED_TIME = 60 * 60


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
        hostname: str) -> Iterator[str]:

    'Iterate over the subdomains in a domain name with two or more components'

    components = hostname.split('.')
    num = len(components)
    for i in range(2, num + 1):
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
            'SELECT id, start_time, end_time, query_count' +
            ' FROM querygroup' +
            ' WHERE start_time <= ? AND host = ?' +
            ' ORDER BY end_time DESC LIMIT 1',
            (querytime_iso, queryhost))

        row = cursor.fetchone()
        if row:
            (group_id, start_time_iso, end_time_iso, count) = row

            start_time = isotime_to_datetime(start_time_iso)
            end_time = isotime_to_datetime(end_time_iso)
            querytime = isotime_to_datetime(querytime_iso)

            if count < 100 and is_query_in_group(
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


def find_hostname_from_ip(
        db: sqlite3.Connection,
        time: str,
        ip_address: str) -> str:

    '''Search the DHCP assignments for a hostname corresponding to
    an IP address at a specific time'''

    cursor = db.cursor()
    try:
        cursor.execute(
            'SELECT hostname FROM dhcpassignment' +
            ' WHERE ip_address = ? AND time <= ?' +
            ' ORDER BY time DESC' +
            ' LIMIT 1',
            (ip_address, time))

        row = cursor.fetchone()
        if row is not None:
            return row[0]
        else:
            return ip_address
    finally:
        cursor.close()


def log_dns_query(
        db: sqlite3.Connection,
        querytime: str,
        querytype: str,
        queryvalue: str,
        address: str) -> None:

    'Store the DNS query in the database'

    isotime = syslog_time_to_datetime(querytime).isoformat()

    cursor = db.cursor()
    try:
        hostname = find_hostname_from_ip(db, isotime, address)
        group_id = log_dns_query_group(db, isotime, queryvalue, hostname)

        cursor.execute(
            'INSERT INTO dnsquery' +
            ' (group_id, time, type, value, host, host_ip)' +
            ' VALUES (?,?,?,?,?,?)',
            (group_id, isotime, querytype, queryvalue, hostname, address))
        query_id = cursor.lastrowid

        #  Update derived querygroup columns
        cursor.execute(
            'UPDATE querygroup SET ' +
            ' start_time=(SELECT MIN(time)' +
            '     FROM dnsquery WHERE group_id = ?),' +
            ' end_time=(SELECT MAX(time)' +
            '     FROM dnsquery WHERE group_id = ?),' +
            ' first_value=(SELECT value' +
            '     FROM dnsquery WHERE group_id = ? ORDER BY id LIMIT 1),' +
            ' query_count=(SELECT COUNT(id)' +
            '     FROM dnsquery WHERE group_id = ?)' +
            ' WHERE id = ?',
            (group_id, group_id, group_id, group_id, group_id))

        #  Associate the subdomains with the query
        for subdomain in list_domains(queryvalue):
            querydomain = (query_id, group_id, isotime, subdomain)
            db.execute(
                'INSERT INTO querydomain (query_id, group_id, time, domain)' +
                ' VALUES (?,?,?,?)',
                querydomain)
    finally:
        cursor.close()


def log_dhcp_assignment(
        db: sqlite3.Connection,
        time: str,
        ip_address: str,
        mac_address: str,
        hostname: str) -> None:

    'Record DHCP address assignment with a time and hostname'

    isotime = syslog_time_to_datetime(time).isoformat()

    cursor = db.cursor()
    try:
        cursor.execute(
            'INSERT INTO dhcpassignment' +
            ' (ip_address, mac_address, hostname, time)' +
            ' VALUES (?,?,?,?)',
            (ip_address, mac_address, hostname, isotime))
    finally:
        cursor.close()


def log_line(
        db: sqlite3.Connection,
        line: str) -> None:

    'Match the log line against DNS queries or DHCP allocations and log them'

    time_re = r'([A-Za-z]+ +[0-9]+ +[0-9:]+)'
    dnsmasq_re = r'dnsmasq\[[0-9]+\]'
    query_re = r'query\[([A-Z]+)\] ([A-Za-z0-9-\.]+) from ([0-9A-Fa-f:\.]+)'
    dns_query_re = r'%s .* %s: %s' % (time_re, dnsmasq_re, query_re)

    dnsmasq_dhcp_re = r'dnsmasq-dhcp\[[0-9]+\]'
    dchpack_re = r'DHCPACK\([A-Za-z0-9]+\) ([0-9A-Fa-f:\.]+)' + \
        r' ([0-9A-Fa-f:]+) ([A-Za-z0-9-\.]+)'
    dhcp_assignment_re = r'%s .* %s: %s' % \
        (time_re, dnsmasq_dhcp_re, dchpack_re)

    match = re.match(dns_query_re, line)
    if match:
        log_dns_query(db, *match.groups())

    match = re.match(dhcp_assignment_re, line)
    if match:
        log_dhcp_assignment(db, *match.groups())


def create_tables(
        db: sqlite3.Connection) -> None:

    'Create tables and indices for the DNS database'

    db.execute(
        'CREATE TABLE IF NOT EXISTS querygroup' +
        ' (id INTEGER PRIMARY KEY, host, start_time, end_time,' +
        '     first_value, query_count INTEGER)')
    db.execute(
        'CREATE INDEX IF NOT EXISTS querygroup_end_time ON querygroup' +
        ' (end_time, host)')

    db.execute(
        'CREATE TABLE IF NOT EXISTS dnsquery' +
        ' (id INTEGER PRIMARY KEY, group_id INTEGER, time,' +
        '     type, value, host, host_ip)')
    db.execute(
        'CREATE INDEX IF NOT EXISTS dnsquery_group ON dnsquery' +
        ' (group_id)')

    db.execute(
        'CREATE TABLE IF NOT EXISTS querydomain' +
        ' (query_id INTEGER, group_id INTEGER, time, domain)')
    db.execute(
        'CREATE INDEX IF NOT EXISTS querydomain_domain ON querydomain' +
        ' (domain COLLATE NOCASE, group_id)')

    db.execute(
        'CREATE TABLE IF NOT EXISTS dhcpassignment' +
        ' (id INTEGER PRIMARY KEY, ip_address,' +
        ' mac_address, hostname, time)')
    db.execute(
        'CREATE INDEX IF NOT EXISTS dhcpassignment_ip_address' +
        ' ON dhcpassignment' +
        ' (ip_address, time)')


def open_database() -> sqlite3.Connection:

    '''Ensure the database and its tables exist, open it, and
    return a connection'''

    try:
        os.mkdir(os.path.dirname(DATABASE_PATH))
    except FileExistsError:
        pass

    db = sqlite3.connect(DATABASE_PATH)

    create_tables(db)

    return db
