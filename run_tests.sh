#!/bin/sh

if [ -e "`which tox`" ]; then
    tox $@
else
    echo "**** install tox to run the tests http://codespeak.net/tox/"
fi