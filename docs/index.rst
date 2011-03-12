===================
Fudge Documentation
===================

Fudge is a Python module for using fake objects (mocks and stubs) to test real ones.

In readable Python code, you declare what methods are available on your fake and how they should be called.  Then you inject that into your application and start testing.  This declarative approach means you don't have to record and playback actions and you don't have to inspect your fakes after running code.  If the fake object was used incorrectly then you'll see an informative exception message with a traceback that points to the culprit.

Fudge was inspired by `Mocha <http://mocha.rubyforge.org/>`_ which is a simpler version of `jMock <http://www.jmock.org/>`_.  But unlike Mocha, Fudge does not automatically hijack real objects; you explicitly :ref:`patch <using-fudge>` them in your test.  And unlike jMock, Fudge is only as strict about expectations as you want it to be.  If the type of arguments sent to the fake method aren't important then you don't have to declare an expectation for them.

Download / Install
==================

Just type::

    $ pip install fudge

You can get the `pip command here`_.  Fudge requires Python 2.5 or higher.

.. _pip command here: http://pip.openplans.org/

.. _install-for-python-3:

Installing for Python 3
=======================

As of version 0.9.5, Fudge supports Python 3.  Just install `distribute`_ and type::
    
    $ python3.x setup.py install

This step will convert the Fudge source code using the 2to3 tool.

.. _distribute: http://packages.python.org/distribute/

.. _fudge-source:

Source
======

The Fudge source can be downloaded as a tar.gz file from http://pypi.python.org/pypi/fudge  

Using `Mercurial <http://www.selenic.com/mercurial/wiki/>`_ you can clone the source from http://bitbucket.org/kumar303/fudge/  

Fudge is free and open for usage under the `MIT license`_.

.. _MIT license: http://en.wikipedia.org/wiki/MIT_License

Contents
========

.. toctree::
   :maxdepth: 2
   
   using-fudge
   javascript
   why-fudge
   migrating-0.9-to-1.0

.. _fudge-api:

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

Fudge was created by `Kumar McMillan <http://farmdev.com/>`_ and contains contributions by Cristian Esquivias, Michael Williamson, and Luis Fagundes.

.. _fudge-changelog:

Changelog
=========

- 1.0.3

  - Added :func:`fudge.Fake.is_a_stub` :ref:`documented here <creating-a-stub>`
  - :func:`arg.any_value() <fudge.inspector.ValueInspector.any_value>`
    is **DEPRECATED** in favor of
    :func:`arg.any() <fudge.inspector.ValueInspector.any>`
  - Attributes declared by :func:`fudge.Fake.has_attr` are now settable.
    Thanks to Mike Kent for the bug report.
  - Fixes ImportError when patching certain class methods like
    smtplib.SMTP.sendmail
  - Fixes representation of chained fakes for class instances.

- 1.0.2

  - Object patching is a lot safer in many cases and now supports getter objects
    and static methods. Thanks to Michael Foord and mock._patch for ideas and code.

- 1.0.1
  
  - Fixed ImportError when a patched path traverses object attributes within a module.

- 1.0.0

  - After extensive usage and community input, the fudge interface has
    been greatly simplified!
  - There is now a :ref:`way better pattern <using-fudge>` for setting up fakes. The old way is
    still supported but you'll want to write all new code in this pattern once
    you see how much easier it is.
  - Added :func:`fudge.patch` and :func:`fudge.test`
  - Added :func:`fudge.Fake.expects_call` and :func:`fudge.Fake.is_callable`
  - **Changed**: The tests are no longer maintained in Python 2.4 although 
    Fudge probably still supports 2.4

- 0.9.6

  - Added support to patch builtin modules.  Thanks to Luis Fagundes for the 
    patch.

- 0.9.5
  
  - **Changed**: multiple calls to :func:`fudge.Fake.expects` behave just like 
    :func:`fudge.Fake.next_call`.  The same goes for :func:`fudge.Fake.provides`.
    You probably won't need to update any old code for this change, it's just 
    a convenience.
  - Added :func:`fudge.Fake.with_matching_args` so that expected 
    arguments can be declared more loosely
  - Added :ref:`support for Python 3 <install-for-python-3>`
  - Improved support for Jython

- 0.9.4
  
  - Fixed bug where __init__ would always return the Fake instance of itself.  
    Now you can return a custom object if you want.

- 0.9.3
  
  - Added ``with_args()`` to :ref:`JavaScript Fudge <javascript-fudge>`.
  - Fixed bug where argument values that overloaded __eq__ might cause declared expectations to fail (patch from Michael Williamson, Issue 9)
  - Fixed bug where :func:`fudge.Fake.raises` obscured :func:`fudge.Fake.with_args` (Issue 6)
  - Fixed ``returns_fake()`` in JavaScript Fudge.

- 0.9.2
  
  - **Changed**: values in failed comparisons are no longer shortened when too long.
  - **Changed**: :func:`fudge.Fake.calls` no longer trumps expectations 
    (i.e. :func:`fudge.Fake.with_args`)
  - **Changed**: :func:`fudge.Fake.with_args` is more strict.  You will now see an error 
    when arguments are not expected yet keyword arguments were expected and vice versa.  
    This was technically a bug but is listed under 
    changes in case you need to update your code.  Note that you can work 
    with arguments more expressively using the new :mod:`fudge.inspector` functions.
  - Added :mod:`fudge.inspector` for :ref:`working-with-arguments`.
  - Added :func:`fudge.Fake.remember_order` so that order of expected calls can be verified.
  - Added :func:`fudge.Fake.raises` for simulating exceptions
  - Added keyword :func:`fudge.Fake.next_call(for_method="other_call") <fudge.Fake.next_call>` 
    so that arbitrary methods can be modified (not just the last one).
  - Fixed: error is raised if you declare multiple :func:`fudge.Fake.provides` for the same Fake. 
    This also applies to :func:`fudge.Fake.expects`
  - Fixed bug where :func:`fudge.Fake.returns` did not work if you had replaced a call with :func:`fudge.Fake.calls`
  - Fixed bug in :func:`fudge.Fake.next_call` so that this now works: ``Fake(callable=True).next_call().returns(...)``
  - Fixed: Improved Python 2.4 compatibility.
  - Fixed bug where ``from fudge import *`` did not import proper objects.

- 0.9.1
  
  - **DEPRECATED** fudge.start() in favor of :func:`fudge.clear_calls`
  - **DEPRECATED** fudge.stop() in favor of :func:`fudge.verify`
  - Added context manager :func:`fudge.patcher.patched_context` so the with statement can be used for 
    patching (contributed by Cristian Esquivias)
  - Added :func:`fudge.Fake.times_called` to expect a certain call count (contributed by Cristian Esquivias)
  - Added :class:`Fake(expect_call=True) <fudge.Fake>` to indicate an expected callable.  Unlike 
    :class:`Fake(callable=True) <fudge.Fake>` the former will raise an error if not called.
  
- 0.9.0
  
  - first release