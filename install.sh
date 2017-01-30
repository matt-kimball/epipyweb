#!/bin/sh

VAR_EPI=/var/lib/epipyweb
RUN_EPI=/var/run/epipyweb
SHARE_EPI=/usr/share/epipyweb

mkdir -p $VAR_EPI
mkdir -p $RUN_EPI
mkdir -p $SHARE_EPI

chown www-data.www-data $RUN_EPI

cp -r record serve ui uwsgi.sh $SHARE_EPI

cp -r etc/nginx etc/rsyslog.d etc/systemd etc/uwsgi /etc

ln -sf /etc/nginx/sites-available/epipyweb /etc/nginx/sites-enabled/epipyweb
rm -f /etc/nginx/sites-enabled/default

systemctl enable epipyweb.socket
systemctl enable epipyweb.service
