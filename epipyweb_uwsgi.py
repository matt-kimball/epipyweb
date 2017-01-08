import json
import sqlite3
import typing
import urllib.parse


StartResponseHeaders = typing.Iterable[typing.Tuple[str, str]]
StartResponse = typing.Callable[[str, StartResponseHeaders], None]

QueryArgs = typing.Dict[str, typing.List[str]]


def groupqueries_page(
        db: sqlite3.Connection,
        group_id: int,
        count: int) -> typing.Dict:

    'Retrieve a page of DNS queries associated with a group ID.'

    cursor = db.cursor()
    try:
        cursor.execute(
            'SELECT id, value, time FROM dnsquery' +
            ' WHERE group_id = ?' +
            ' ORDER BY id ASC' +
            ' LIMIT ?',
            (group_id, count))

        result = typing.cast(typing.Dict, {
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


def dnsquerygroup_page(
        db: sqlite3.Connection,
        before_id: typing.Optional[int],
        after_id: typing.Optional[int],
        count: int) -> typing.Dict:

    '''Retrieve a particular number of the latest DNS query log entries
    from the database.'''

    if count > 100:
        count = 100

    cursor = db.cursor()
    try:
        if before_id:
            where = ' WHERE id < ?'
            sql_args = [before_id, count]
        elif after_id:
            where = ' WHERE id <= ?'
            sql_args = [after_id + count, count]
        else:
            where = ''
            sql_args = [count]

        cursor.execute(
            'SELECT id, dnsquery.count,' +
            ' start_time, host, dnsquery.value FROM querygroup' +
            ' JOIN (SELECT COUNT(id) as count, MIN(time),'
            '     value, group_id FROM dnsquery' +
            '     GROUP BY group_id) dnsquery' +
            '     ON querygroup.id = dnsquery.group_id' +
            where +
            ' ORDER BY id DESC' +
            ' LIMIT ?',
            sql_args)

        result = typing.cast(typing.Dict, {
            'groups': [],
        })
        for row in cursor.fetchall():
            result['groups'].append({
                'id': row[0],
                'query_count': row[1],
                'time': row[2],
                'host': row[3],
                'value': row[4],
            })

        return result
    finally:
        cursor.close()


def groupqueries(
        query: QueryArgs) -> typing.Dict:

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

    db = sqlite3.connect('dns.db')
    try:
        return groupqueries_page(db, group_id, count)
    finally:
        db.close()


def dnsquerygroup(
        query: QueryArgs) -> typing.Dict:

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

    db = sqlite3.connect('dns.db')
    try:
        return dnsquerygroup_page(db, before_id, after_id, count)
    finally:
        db.close()


def start_ok(
        start_response: StartResponse) -> None:

    'Start a response to an understood request'

    start_response('200 OK', [('Content-Type', 'application/javascript')])


def application(
        env: typing.Dict[str, str],
        start_response: StartResponse) -> typing.Iterable[bytes]:

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
