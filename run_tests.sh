#!/bin/sh
# todo: make a nose plugin that executes sphinx doctests :)
set -e
make -C docs doctest
_env/bin/nosetests --with-doctest $@
