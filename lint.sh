#!/bin/sh

JS_SOURCE=$(find . -name '*.js' | grep -v jquery)
PY_SOURCE="$(find . -name '*.py') $(find bin -type f)"

jslint --terse $JS_SOURCE
pep8 $PY_SOURCE
mypy --ignore-missing-imports $PY_SOURCE
