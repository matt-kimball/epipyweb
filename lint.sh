#!/bin/sh

JS_SOURCE=$(find . -name '*.js' | grep -v jquery)
PY_SOURCE=$(find . -name '*.py')

jslint --terse $JS_SOURCE
pep8 $PY_SOURCE
mypy --silent-imports $PY_SOURCE
