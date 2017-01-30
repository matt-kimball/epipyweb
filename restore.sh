#!/bin/sh

cat dns.db.bz | ssh rpi3 'bzip2 -d >dns.back.db \
    && sudo sqlite3 /var/lib/epipyweb/dns.db ".restore dns.back.db" \
    && rm dns.back.db'
