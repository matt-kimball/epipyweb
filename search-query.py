#!/usr/bin/env python3

import argparse
import sqlite3
import typing


DnsQuery = typing.Tuple[str, str, str, str]


def parse_cmdline() -> argparse.Namespace:

    'Parse the commandline, looking for a query string to search'

    parser = argparse.ArgumentParser(
        description='Search DNS queries')

    parser.add_argument(
        'queryvalue', metavar='value',
        help='DNS value queried')

    return parser.parse_args()


def find_query(
        db: sqlite3.Connection,
        queryid: int) -> DnsQuery:

    'Given a query ID, return a tuple with query data'

    cursor = db.cursor()
    try:
        cursor.execute(
            'SELECT time, host, type, value FROM dnsquery WHERE id = ?',
            (queryid,))

        (time, host, type, value) = cursor.fetchone()
        return (time, host, type, value)
    finally:
        cursor.close()


def search_dnsqueries(
        db: sqlite3.Connection,
        dnsvalue: str) -> typing.Iterator[DnsQuery]:

    'Search the DNS queries for a particular query value'

    cursor = db.cursor()
    try:
        cursor.execute(
            'SELECT query FROM querydomain WHERE domain = ?' +
            ' ORDER BY time DESC',
            (dnsvalue,))

        for (qid,) in typing.cast(typing.Iterable, cursor):
            yield find_query(db, qid)
    finally:
        cursor.close()


def main():

    'Search DNS queries stored in Epipyweb'

    args = parse_cmdline()

    db = sqlite3.connect('dns.db')
    try:
        for query in search_dnsqueries(db, args.queryvalue):
            line = str.join(' ', query)
            print(line)
    finally:
        db.close()


if __name__ == '__main__':
    main()
