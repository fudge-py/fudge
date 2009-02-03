===================
Fudge Documentation
===================

Fudge is a Python module for using fake objects (mocks, stubs, etc) to test real ones.

The module is designed for two specific situations:

- Replace an object
  
  - Temporarily return a canned value for a 
    method or allow a method to be called without affect.

- Ensure an object is used correctly

  - Declare expectations about what methods should be 
    called and what arguments should be sent.

Fudge was inspired by `Mocha <http://mocha.rubyforge.org/>`_ (Ruby) which is a simpler version of `jMock <http://www.jmock.org/>`_ (Java).

Download / Install
==================

Just type::

    $ sudo easy_install fudge

If you don't have ``easy_install`` for Python you can get it like this::

    $ wget http://peak.telecommunity.com/dist/ez_setup.py
    $ sudo python ez_setup.py

.. _fudge-source:

Source
======

The Fudge source can be downloaded as a tar.gz file from http://pypi.python.org/pypi/fudge

To checkout the Fudge source, install `Mercurial <http://www.selenic.com/mercurial/wiki/>`_ and type::
    
    $ hg clone http://hg.farmdev.com/fudge/

You can get updates with::
    
    $ hg pull --update

Contents
========

.. toctree::
   :maxdepth: 2
   
   examples
   javascript
   why-fudge

API Reference
=============

.. toctree::
    :glob:
    
    api/*

Contributing
============

Please submit bugs and patches, preferably with tests.  All contributors will be acknowledged.  Thanks!
