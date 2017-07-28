#!/bin/bash
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

repeat_url() {
    for i in `seq 1 10`;
    do
        curl -s $1 >/dev/null
    done
}

time_url() {
    curl -s $1

    time repeat_url $1
}

echo Recent list:
time repeat_url http://localhost/q/qnsquerygroup

echo Search:
time repeat_url http://localhost/q/dnsquerygroup?search=amazon

echo Rare:
time repeat_url http://localhost/q/dnsquerygroup?search=theatlantic
