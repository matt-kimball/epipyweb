#!/bin/sh

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
