#!/bin/sh

killall uwsgi
uwsgi --ini /etc/uwsgi/apps-available/epipyweb.ini
