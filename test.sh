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

LOG=test.log
EXIT_VALUE=0

TESTS="""
    test/querygroup.py
"""

rm -f $LOG

for TEST in $TESTS
do
    echo "@" $TEST >>$LOG
    echo "" >>$LOG

    python3 $TEST --quiet 2>>$LOG >>$LOG

    if [ $? -ne 0 ]
    then
        echo Failed test $TEST
        EXIT_VALUE=1
    fi

    echo "" >>$LOG
done

if [ $EXIT_VALUE -eq 0 ]
then
    echo Tests passed
else
    echo ""
    echo Failures logged to $LOG
fi

exit $EXIT_VALUE
