
===============================
Migrating from Fudge 0.9 to 1.0
===============================

After :ref:`many 0.9.x versions <fudge-changelog>` and some great input from the community, Fudge has evolved to 1.0.  This introduces a much *simpler* API and while it doesn't deprecate the old API you'll probably want to update your code.

Take a look at the new code examples in :ref:`using Fudge <using-fudge>` to get a feel for it.

Here is a summary of changes:

The new @patch and @test decorators
===================================

You no longer have to worry about when and where to call :func:`fudge.clear_calls`, :func:`fudge.verify`, and :func:`fudge.clear_expectations`!  Instead, just wrap each test in the :func:`fudge.patch` decorator and declare expectations within your test.  If you don't need to patch anything, use the :func:`fudge.test` decorator.

Expectations that were declared in setup
========================================

If you were declaring expectations in a module-level ``setup()`` or ``unittest.setUp()`` method then you either have to continue managing the clear/verify calls manually and decorate your tests with :func:`fudge.with_fakes` or you need to move all declaration into the test function (not setup) using the :func:`fudge.patch` decorator.
