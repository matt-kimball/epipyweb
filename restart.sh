#!/bin/sh

systemctl restart nginx
systemctl restart rsyslog
systemctl restart epipyweb
