===================
Fudge Documentation
===================

Fudge is a Python module for using fake objects (mocks, stubs, etc) to test real ones.

This module is designed for two specific situations:

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
    
    $ hg clone http://bitbucket.org/kumar303/fudge/

You can get updates with::
    
    $ hg pull --update

Contents
========

.. toctree::
   :maxdepth: 2
   
   using-fudge
   javascript
   why-fudge

API Reference
=============

.. toctree::
    :glob:
    
    api/*

Contributing
============

Please submit `bugs and patches <http://bitbucket.org/kumar303/fudge/issues/>`_, preferably with tests.  All contributors will be acknowledged.  Thanks!

Credits
=======

Fudge was created by `Kumar McMillan <http://farmdev.com/>`_ and contains contributions by Cristian Esquivias.

Changelog
=========

- 0.9.2
  
  - Added keyword :func:`fudge.Fake.next_call(for_method="other_call") <fudge.Fake.next_call>` to make for 
    more readable declarations.
  - Added :func:`fudge.Fake.remember_order` so that order of expected calls can be verified.
  - Fixed bug in :func:`fudge.Fake.next_call` so that this now works: ``Fake(callable=True).next_call().returns(...)``
  - Added :func:`fudge.Fake.raises` for simulating exceptions

- 0.9.1
  
  - **DEPRECATED** fudge.start() in favor of :func:`fudge.clear_calls`
  - **DEPRECATED** fudge.stop() in favor of :func:`fudge.verify`
  - Added context manager :func:`fudge.patched_context` so the with statement can be used for 
    patching (contributed by Cristian Esquivias)
  - Added :func:`fudge.Fake.times_called` to expect a certain call count (contributed by Cristian Esquivias)
  - Added :class:`Fake(expect_call=True) <fudge.Fake>` to indicate an expected callable.  Unlike 
    :class:`Fake(callable=True) <fudge.Fake>` the former will raise an error if not called.
  
- 0.9.0
  
  - first release