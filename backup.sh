#!/bin/sh

ssh rpi3 'sudo sqlite3 /var/lib/epipyweb/dns.db ".backup dns.back.db" \
	&& cat dns.back.db | bzip2 && rm dns.back.db' >dns.back.db.bz

if [ -e dns.db.bz ]
then
    mv -f dns.db.bz dns.db.bz.1
fi

mv -f dns.back.db.bz dns.db.bz
