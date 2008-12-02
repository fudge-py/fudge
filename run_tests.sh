#!/bin/sh
# todo: make a nose plugin that executes sphinx doctests :)
pushd docs
make doctest
# hmm, this doesn't work from make
if [ $? -ne 0 ]; then
    exit 1
fi
popd
nosetests --with-doctest $@
