#!/bin/sh

WSGI_FILE=serve/epipyweb_uwsgi.py

UWSGI_SOCKET_FLAGS="--socket /tmp/epipyweb.sock --uid www-data --gid www-data"
UWSGI_DAEMON_FLAGS="--daemonize /tmp/epipyweb.log"
UWSGI_FLAGS="$UWSGI_SOCKET_FLAGS $UWSGI_DAEMON_FLAGS"

killall uwsgi
uwsgi $UWSGI_FLAGS --plugin python3 --wsgi-file $WSGI_FILE
