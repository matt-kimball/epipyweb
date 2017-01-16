#!/bin/sh

ps ax | grep syslog.py | grep -v grep | awk '{ print $1 }' | xargs kill
