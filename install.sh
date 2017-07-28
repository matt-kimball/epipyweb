#!/bin/sh
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

VAR_EPI=/var/lib/epipyweb
RUN_EPI=/var/run/epipyweb
SHARE_EPI=/usr/share/epipyweb

mkdir -p $VAR_EPI
mkdir -p $RUN_EPI
mkdir -p $SHARE_EPI

chown www-data.www-data $RUN_EPI

cp -r record serve ui uwsgi.sh $SHARE_EPI

cp -r etc/nginx etc/rsyslog.d etc/uwsgi /etc

ln -sf /etc/nginx/sites-available/epipyweb /etc/nginx/sites-enabled/epipyweb
rm -f /etc/nginx/sites-enabled/default

systemctl enable epipyweb.socket
systemctl enable epipyweb.service
