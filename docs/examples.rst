
.. _fudge-examples:

==============
Fudge Examples
==============

Fudging Email
=============

Say you have a method that uses Python's standard `smtplib <http://docs.python.org/library/smtplib.html#module-smtplib>`_ module 
to send email:

.. doctest::

    >>> def send_email(recipient, sender, msg):
    ...     import smtplib
    ...     msg = ("From: %s\r\nTo: %s\r\n\r\n%s" % (
    ...             sender, ", ".join(recipient), msg))
    ...     s = smtplib.SMTP()
    ...     s.connect()
    ...     s.sendmail(sender, recipient, msg)
    ...     s.close()
    ...     print "Sent an email to %s" % recipient
    ... 
    >>> 

You don't want to send an email each time you run a test but you want to be 
sure that your code is able to send email.  Fudge recommends this strategy: 
Since you trust that the SMTP class works, expect that your application 
under test uses the SMTP class correctly.  If the application calls the wrong 
method or forgets to call a method then your test should fail.  Here's how to set 
it up:

.. doctest::
    
    >>> import fudge
    >>> SMTP = fudge.Fake('SMTP')
    >>> SMTP = SMTP.expects('__init__')
    >>> SMTP = SMTP.expects('connect')
    >>> SMTP = SMTP.expects('sendmail').with_arg_count(3)
    >>> SMTP = SMTP.expects('close')

Next, patch the module temporarily with your fake:
    
.. doctest::

    >>> patched_smtplib = fudge.patch_object("smtplib", "SMTP", SMTP)

Now you can run the code with the fake object.  Begin each test with :func:`fudge.clear_calls` so that call history is reset:

.. doctest::
    
    >>> fudge.clear_calls()

Run the code you want to test:

.. doctest::

    >>> send_email( "kumar@hishouse.com", "you@yourhouse.com", 
    ...                                   "hi, I'm reading about Fudge!")
    ... 
    Sent an email to kumar@hishouse.com

Call :func:`fudge.verify` to make sure all expectations were met:

.. doctest::

    >>> fudge.verify()

And, finally, restore your patches:

.. doctest::

    >>> patched_smtplib.restore()
    
A Simple Test Case
==================

The above code could also be written as a test function, compatible with `Nose`_ or `py.test`_:

.. doctest::
    
    >>> @fudge.with_fakes
    ... @fudge.with_patched_object("smtplib", "SMTP", SMTP)
    ... def test_email():
    ...     send_email( "kumar@hishouse.com", 
    ...                 "you@yourhouse.com", 
    ...                 "Mmmm, fudge")
    ... 
    >>> test_email()
    Sent an email to kumar@hishouse.com

You can also patch code using the `with statement <http://www.python.org/dev/peps/pep-0343/>`_; see :func:`fudge.patched_context`.

A unittest.TestCase
===================

The same test above can be written using the standard ``unittest.TestCase`` module like this:

.. doctest::
    
    >>> import unittest
    >>> class TestEmail(unittest.TestCase):
    ...     def setUp(self):
    ...         self.patched = fudge.patch_object("smtplib", "SMTP", SMTP)
    ...         fudge.clear_calls()
    ... 
    ...     def tearDown(self):
    ...         self.patched.restore()
    ...     
    ...     def test_email(self):
    ...         send_email( "kumar@hishouse.com", 
    ...                     "you@yourhouse.com", 
    ...                     "Mmmm, fudge")
    ...         fudge.verify()
    ... 
    >>> test = TestEmail('test_email')
    >>> test.run()
    Sent an email to kumar@hishouse.com

Notice how :func:`fudge.verify` is called within the test itself, not in tearDown().  This is because :func:`fudge.verify` might raise errors about failed expectations, which is part of your test.

Failed Expectations
===================

Since the previous code declared expectations for how the 
sendmail() method should be called, your test will raise an 
AssertionError when those expectations are not met.  For example:

.. doctest::

    >>> s = SMTP()
    >>> s.connect()
    >>> s.sendmail("whoops")
    Traceback (most recent call last):
    ...
    AssertionError: fake:SMTP.sendmail() was called with 1 arg(s) but expected 3

If your code forgets to call an important method, that would be an error too:

.. doctest::
    
    >>> fudge.clear_calls()
    >>> s = SMTP()
    >>> s.connect()
    >>> fudge.verify()
    Traceback (most recent call last):
    ...
    AssertionError: fake:SMTP.sendmail() was not called

Clearing Expectations
=====================

Fudge assumes that when you declare expectations on a Fake, 
you will use the Fake object in more than one test.  For this reason, 
you'll need to clear the expectation registry explicitly if you 
want to start testing with another fake object.

In other words, if one test uses a fake SMTP but some test later on 
uses a fake database and has nothing to do with email then you'll need 
to clear the SMTP expectations before testing with the fake database.

.. doctest::

    >>> fudge.clear_expectations()

This is different from :func:`fudge.clear_calls`, which only 
clears the actual calls made to your objects.

A Complete Test Module
======================

If you're using a test framework like `Nose`_ or `py.test`_ that supports 
module level setup / teardown hooks, one strategy is to declare all Fake 
objects at the top of your test module and clear expectations after all tests 
are run on your Fake objects.  Here is an example of how you could lay out 
your test module:

.. doctest::
    
    >>> import fudge
    
    >>> SMTP = fudge.Fake()
    >>> SMTP = SMTP.expects('__init__')
    >>> SMTP = SMTP.expects('connect')
    >>> SMTP = SMTP.expects('sendmail').with_arg_count(3)
    >>> SMTP = SMTP.expects('close')
    
    >>> def teardown():
    ...     fudge.clear_expectations()
    ... 
    >>> @fudge.with_fakes
    ... @fudge.with_patched_object("smtplib", "SMTP", SMTP)
    ... def test_email():
    ...     send_email( "kumar.mcmillan@gmail.com", 
    ...                 "you@yourhouse.com", 
    ...                 "Mmmm, fudge")
    ... 

The `Nose`_ framework executes the above test module as follows:
    
.. doctest::

    >>> try:
    ...     test_email()
    ... finally:
    ...     teardown()
    Sent an email to kumar.mcmillan@gmail.com

Stubs Without Expectations
==========================

If you want a fake object where the methods can be called but are not 
expected to be called, the code is just the same but instead of 
:meth:`Fake.expects() <fudge.Fake.expects>` you use :meth:`Fake.provides() <fudge.Fake.provides>`.  Here is an example of always returning True 
for the method is_logged_in():

.. doctest::
    
    >>> auth = fudge.Fake()
    >>> user = auth.provides('current_user').returns_fake()
    >>> user = user.provides('is_logged_in').returns(True)
    
    >>> def show_secret_word(auth):
    ...     user = auth.current_user()
    ...     if user.is_logged_in():
    ...         print "Bird is the word"
    ...     else:
    ...         print "Access denied"
    ... 
    
    >>> fudge.clear_calls()
    >>> show_secret_word(auth)
    Bird is the word
    >>> fudge.verify()

Note that if user.is_logged_in() is not called then no error will be raised.

Replacing A Method
==================

Sometimes returning a static value isn't good enough, you actually need to run some code.  
You can do this using :meth:`Fake.calls() <fudge.Fake.calls>` like this:

.. doctest::
    
    >>> auth = fudge.Fake()
    
    >>> def check_user(username):
    ...     if username=='bert':
    ...         print "Bird is the word"
    ...     else:
    ...         print "Access denied"
    ... 
    >>> auth = auth.provides('show_secret_word_for_user').calls(check_user)
    
    >>> auth.show_secret_word_for_user("bert")
    Bird is the word
    >>> auth.show_secret_word_for_user("ernie")
    Access denied

Fudging A Callable
==================

Sometimes you might only need to replace a single function, not an instance of a class.  
You can do this with the keyword argument :class:`callable=True <fudge.Fake>`.  For example:

.. doctest::
    
    >>> login = fudge.Fake(callable=True).with_args("eziekel", "pazzword").returns(True)
    
    >>> @fudge.with_fakes
    ... @fudge.with_patched_object("auth", "login", login)
    ... def test_login():
    ...     import auth
    ...     logged_in = auth.login("eziekel", "pazzword")
    ...     if logged_in:
    ...         print "Welcome!"
    ...     else:
    ...         print "Access Denied"
    ... 
    >>> test_login()
    Welcome!

However, the above test will *not* raise an error if you forget to call login().  If you want to fudge a callable and declare an expectation that it should be called, use :class:`expect_call=True <fudge.Fake>`:

.. doctest::
    
    >>> login = fudge.Fake('login', expect_call=True).returns(True)
    >>> fudge.clear_calls()
    >>> remote_user = None
    >>> if remote_user:
    ...     auth.login("joe","sekret")
    ... 
    >>> fudge.verify()
    Traceback (most recent call last):
    ...
    AssertionError: fake:login() was not called

Cascading Objects
=================

Some objects you might want to work with will support *cascading* which means each method returns an object.  Here is an example of fudging a cascading `SQLAlchemy query <http://www.sqlalchemy.org/docs/05/ormtutorial.html#querying>`_.  Notice that :meth:`Fake.returns_fake() <fudge.Fake.returns_fake>` is used to specify that ``session.query(User)`` should return a new object.  Notice also that because query() should be iterable, it is set to return a list of fake User objects.

.. doctest::
    
    >>> session = fudge.Fake('session')
    >>> query = session.provides('query').returns_fake()
    >>> query = query.provides('order_by').returns(
    ...             [fudge.Fake('User').has_attr(name='Al', lastname='Capone')]
    ...         )
    
    >>> from models import User
    >>> for instance in session.query(User).order_by(User.id):
    ...     print instance.name, instance.lastname
    ... 
    Al Capone

Multiple Return Values
======================

Let's say you want to test code that needs to call a function multiple times and get back multiple values.  Up until now, you've just seen the :meth:`Fake.returns() <fudge.Fake.returns>` method which will return a value infinitely.  To change that, call ``next_call()`` to advance the call sequence.  Here is an example using a shopping cart scenario:

.. doctest::
    
    >>> cart = fudge.Fake('cart').provides('add').with_args('book')
    >>> cart = cart.returns({'contents': ['book']})
    >>> cart = cart.next_call().with_args('dvd').returns({'contents': ['book','dvd']})
    
    >>> cart.add('book')
    {'contents': ['book']}
    >>> cart.add('dvd')
    {'contents': ['book', 'dvd']}
    >>> cart.add('monkey')
    Traceback (most recent call last):
    ...
    AssertionError: This attribute of fake:cart can only be called 2 time(s).


.. _Nose: http://somethingaboutorange.com/mrl/projects/nose/
.. _py.test: http://codespeak.net/py/dist/test.html

That's it!  See the :ref:`fudge API <fudge-api>` for details.