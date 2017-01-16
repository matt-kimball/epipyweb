#!/bin/bash

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
time repeat_url http://localhost/q/dnsquerygroup?search=pornhub
