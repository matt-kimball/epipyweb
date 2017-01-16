import json
import re
import sqlite3
import urllib.parse

from typing import *


DATABASE_PATH = '/var/lib/epipyweb/dns.db'


StartResponseHeaders = Iterable[Tuple[str, str]]
StartResponse = Callable[[str, StartResponseHeaders], None]

QueryArgs = Dict[str, List[str]]


def groupqueries_page(
        db: sqlite3.Connection,
        group_id: int,
        count: int) -> Dict:

    'Retrieve a page of DNS queries associated with a group ID.'

    cursor = db.cursor()
    try:
        cursor.execute(
            'SELECT id, value, time FROM dnsquery' +
            ' WHERE group_id = ?' +
            ' ORDER BY id ASC' +
            ' LIMIT ?',
            (group_id, count))

        result = cast(Dict, {
            'queries': [],
        })
        for row in cursor.fetchall():
            result['queries'].append({
                'id': row[0],
                'value': row[1],
                'time': row[2],
            })

        return result
    finally:
        cursor.close()


def dnsquerygroup_page_sql(
        search_value: Optional[str],
        before_id: Optional[int],
        after_id: Optional[int],
        count: int) -> Tuple[str, List[Any], bool]:

    'Generate the SQL for searching for a page of DNS query groups'

    sql = ''
    where = ''
    sql_args = cast(List[Any], [])
    order = 'DESC'
    reverse = False

    if before_id:
        where += ' WHERE querygroup.id < ?'
        sql_args += [before_id]
    elif after_id:
        where += ' WHERE querygroup.id > ?'
        sql_args += [after_id]
        order = 'ASC'
        reverse = True

    if search_value:
        if where == '':
            where = ' WHERE'
        else:
            where = where + ' AND'

        sql = \
            'SELECT DISTINCT querygroup.id, querygroup.query_count,' + \
            '     querygroup.start_time, querygroup.host,' + \
            '     querygroup.first_value' + \
            ' FROM querydomain, querygroup' + \
            where + \
            '     querydomain.domain COLLATE NOCASE BETWEEN ? AND ?' + \
            '     AND querydomain.group_id = querygroup.id' + \
            ' ORDER BY querydomain.group_id ' + order + \
            ' LIMIT ?'
        sql_args += [search_value, search_value + '~', count]

        where = ''
    else:
        sql = \
            'SELECT id, query_count, start_time,' + \
            '     host, first_value' + \
            ' FROM querygroup' + \
            where + \
            ' ORDER BY id ' + order + \
            ' LIMIT ?'

        sql_args += [count]

    return (sql, sql_args, reverse)


def check_neighbor_pages_present(
        db: sqlite3.Connection,
        rows: List[Any],
        count: int,
        search_value: Optional[str],
        before_id: Optional[int],
        after_id: Optional[int]) -> Tuple[bool, bool]:

    'Check whether the previous page and next page of DNS query groups exist'

    previous_page_present = False
    next_page_present = False

    if len(rows) > count:
        if after_id is not None:
            previous_page_present = True
        else:
            next_page_present = True

    cursor = db.cursor()
    try:
        if before_id is not None:
            (sql, sql_args, _) = dnsquerygroup_page_sql(
                search_value, None, before_id, 1)
            cursor.execute(sql, sql_args)
            if cursor.fetchone():
                previous_page_present = True

        if after_id is not None:
            (sql, sql_args, _) = dnsquerygroup_page_sql(
                search_value, after_id, None, 1)
            cursor.execute(sql, sql_args)
            if cursor.fetchone():
                next_page_present = True
    finally:
        cursor.close()

    return (previous_page_present, next_page_present)


def dnsquerygroup_page(
        db: sqlite3.Connection,
        search_value: Optional[str],
        before_id: Optional[int],
        after_id: Optional[int],
        count: int) -> Dict:

    '''Retrieve a particular number of the latest DNS query log entries
    from the database.'''

    if count > 100:
        count = 100

    cursor = db.cursor()
    try:
        (sql, sql_args, reverse) = dnsquerygroup_page_sql(
            search_value, before_id, after_id, count + 1)

        cursor.execute(sql, sql_args)
        rows = cursor.fetchall()
    finally:
        cursor.close()

    result = cast(Dict, {
        'groups': [],
        'next_page_present': False,
        'previous_page_present': False,
    })

    (result['previous_page_present'], result['next_page_present']) = \
        check_neighbor_pages_present(
            db, rows, count, search_value, before_id, after_id)

    if len(rows) > count:
        rows = rows[:count]

    for row in rows:
        result['groups'].append({
            'id': row[0],
            'query_count': row[1],
            'time': row[2],
            'host': row[3],
            'value': row[4],
        })

    if reverse:
        result['groups'].reverse()

    return result


def sanitize_search(
        search_value: str) -> str:

    'Ensure a search term contains only valid domain name characters'

    match = re.match(r'^[-A-Za-z0-9\.]+$', search_value)

    if not match:
        raise ValueError(search_value)

    return match.group(0)


def groupqueries(
        query: QueryArgs) -> Dict:

    '''Handle a request for the DNS queries associated with a
    connection group.'''

    count = 100
    try:
        count = int(query['count'][0])
    except (KeyError, ValueError):
        pass

    group_id = None
    try:
        group_id = int(query['id'][0])
    except (KeyError, ValueError):
        return {'error': 'missing group id'}

    db = sqlite3.connect(DATABASE_PATH)
    try:
        return groupqueries_page(db, group_id, count)
    finally:
        db.close()


def dnsquerygroup(
        query: QueryArgs) -> Dict:

    'Retrieve a batch of DNS query log entries'

    count = 100
    try:
        count = int(query['count'][0])
    except (KeyError, ValueError):
        pass

    before_id = None
    try:
        before_id = int(query['before'][0])
    except (KeyError, ValueError):
        pass

    after_id = None
    try:
        after_id = int(query['after'][0])
    except (KeyError, ValueError):
        pass

    search_value = None
    try:
        search_value = sanitize_search(query['search'][0])
    except ValueError:
        return {'error': 'Invalid search value'}
    except KeyError:
        pass

    db = sqlite3.connect(DATABASE_PATH)
    try:
        return dnsquerygroup_page(
            db, search_value, before_id, after_id, count)
    finally:
        db.close()


def start_ok(
        start_response: StartResponse) -> None:

    'Start a response to an understood request'

    start_response('200 OK', [('Content-Type', 'application/javascript')])


def application(
        env: Dict[str, str],
        start_response: StartResponse) -> Iterable[bytes]:

    'uWSGI entry point - dispatch as specified by the request type'

    path = env['PATH_INFO'].split('/')
    query = urllib.parse.parse_qs(env['QUERY_STRING'])

    request = None
    if len(path) > 2:
        request = path[2]

    if request == 'dnsquerygroup':
        start_ok(start_response)
        yield json.dumps(dnsquerygroup(query)).encode('utf-8')
    elif request == 'groupqueries':
        start_ok(start_response)
        yield json.dumps(groupqueries(query)).encode('utf-8')
    else:
        start_response('404 Not Found', [('Context-Type', 'text/plain')])
