#!/bin/sh

TIMESTAMP=$(date +%Y%m%d%H%M%S)
VERSION=0.1
PACKAGE=epipyweb_$VERSION-$TIMESTAMP

SYSTEMD="\
    systemd/epipyweb.service \
    systemd/epipyweb.socket"

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

mkdir -p $PACKAGE/usr/share/epipyweb
cp -r record serve ui uwsgi.sh $PACKAGE/usr/share/epipyweb

mkdir -p $PACKAGE/etc
cp -r etc/nginx etc/rsyslog.d etc/uwsgi $PACKAGE/etc

mkdir -p $PACKAGE/lib/systemd/system
cp $SYSTEMD $PACKAGE/lib/systemd/system

chown -R root.root $PACKAGE
dpkg-deb --build $PACKAGE
