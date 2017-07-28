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

TIMESTAMP=$(date +%Y%m%d%H%M%S)
VERSION=0.1
PACKAGE=epipyweb_$VERSION-$TIMESTAMP

BINS="\
    bin/epipyweb-database-rotate"

SYSTEMD="\
    systemd/epipyweb.service \
    systemd/epipyweb.socket \
    systemd/epipyweb-database-rotate.service \
    systemd/epipyweb-database-rotate.timer"

DEBIAN="\
    debian/postinst \
    debian/prerm"

rm -fr $PACKAGE
mkdir -p $PACKAGE/DEBIAN

cat <<CONTROL_END >$PACKAGE/DEBIAN/control
Package: epipyweb
Version: $VERSION-$TIMESTAMP
Architecture: all
Section: admin
Priority: optional
Depends: python3, python3-typing, systemd, uwsgi, uwsgi-plugin-python3, epipynet, nginx, rsyslog
Maintainer: Matt Kimball <matt.kimball@gmail.com>
Homepage: http://www.epipylon.com/
Description: Epipylon Web user interface
 A web interface for controlling and inspecting an Epipylon device
CONTROL_END

chmod a+rx $DEBIAN
cp $DEBIAN $PACKAGE/DEBIAN

mkdir -p $PACKAGE/usr/sbin
cp $BINS $PACKAGE/usr/sbin

mkdir -p $PACKAGE/usr/share/epipyweb
cp -r record serve ui $PACKAGE/usr/share/epipyweb

mkdir -p $PACKAGE/etc
cp -r etc/nginx etc/rsyslog.d etc/uwsgi $PACKAGE/etc

mkdir -p $PACKAGE/lib/systemd/system
cp $SYSTEMD $PACKAGE/lib/systemd/system

chown -R root.root $PACKAGE
dpkg-deb --build $PACKAGE
