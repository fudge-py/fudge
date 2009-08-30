#!/bin/sh
# todo: make a nose plugin that executes sphinx doctests :)
set -e
make -C docs doctest
nosetests --with-doctest $@
