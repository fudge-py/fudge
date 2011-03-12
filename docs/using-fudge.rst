
.. _using-fudge:

===========
Using Fudge
===========

Fudging A Web Service
=====================

When testing code that uses a web service you probably want a fast set of tests that don't depend on an actual web service on the Internet.  This is a good scenario in which to use mock objects.  Say you have a Twitter bot that looks something like this:

.. doctest::

    >>> import oauthtwitter
    >>> def post_msg_to_twitter(msg):
    ...     api = oauthtwitter.OAuthApi(
    ...         '<consumer_key>', '<consumer_secret>',
    ...         '<oauth_token>', '<oauth_token_secret>'
    ...     )
    ...     api.UpdateStatus(msg)
    ...     print "Sent: %s" % msg
    >>> 

Since the `oauthtwitter`_ module is maintained independently, your code should work as long as it calls the right methods.
    
A Simple Test Case
==================

You can use Fudge to replace the OAuthApi class with a fake and **declare an expectation** of how it should be used:

.. _oauthtwitter: http://code.google.com/p/oauth-python-twitter/

.. doctest::
    
    >>> import fudge
    >>> @fudge.patch('oauthtwitter.OAuthApi')
    ... def test(FakeOAuthApi):
    ...     (FakeOAuthApi.expects_call()
    ...                  .with_args('<consumer_key>', '<consumer_secret>',
    ...                             '<oauth_token>', '<oauth_token_secret>')
    ...                  .returns_fake()
    ...                  .expects('UpdateStatus').with_arg_count(1))
    ... 
    ...     post_msg_to_twitter("hey there fellow testing freaks!")
    >>> 

Let's break this down:

1. The :func:`patch <fudge.patch>` decorator will temporarily patch in a fake
   object for the duration of the test and expose it as an argument to
   the test.  This allows you to add expectations or stubs.
2. The :class:`fake <fudge.Fake>` object you see here expects a call (class 
   instantiation) with four arguments having specific string values.  The 
   returned value is an object instance (a new fake) that expects you to call 
   ``fake_oauth.UpdateStatus()`` with one argument.
3. Finally, ``post_msg_to_twitter()`` is called.

Let's run the test!

.. doctest::
  
  >>> test()
  Sent: hey there fellow testing freaks!

Sweet, it passed.

Fudge lets you declare expectations as loose or as tight as you want.  If you don't care about the exact arguments, you can leave off the call to :meth:`fudge.Fake.with_args`.  If you don't care if a method is actually called you can use :meth:`fudge.Fake.provides` instead of :meth:`fudge.Fake.expects`.  Likewise, :meth:`fudge.Fake.with_arg_count` can be used when you don't want to worry about the actual argument values.  There are `argument inspectors <working-with-arguments>`_ for checking values in other ways.

Fake objects without patches (dependency injection)
===================================================

If you don't need to patch anything, you can use the :func:`fudge.test` 
decorator instead.  This will ensure an exception is raised in case any 
expectations aren't met.  Here's an example:

.. doctest::
    
    >>> def send_msg(api):
    ...     if False: # a mistake
    ...         api.UpdateStatus('hello')
    ... 
    >>> @fudge.test
    ... def test_msg():
    ...     FakeOAuthApi = (fudge.Fake('OAuthApi')
    ...                          .is_callable()
    ...                          .expects('UpdateStatus'))
    ...     api = FakeOAuthApi()
    ...     send_msg(api)
    ... 
    >>> test_msg()
    Traceback (most recent call last):
    ...
    AssertionError: fake:OAuthApi.UpdateStatus() was not called

.. doctest::
    :hide:
    
    >>> fudge.clear_expectations()

Stubs Without Expectations
==========================

If you want a fake object where the methods can be called but are not 
expected to be called, the code is just the same but instead of 
:meth:`Fake.expects() <fudge.Fake.expects>` you use :meth:`Fake.provides() <fudge.Fake.provides>`.  Here is an example of always returning True 
for the method is_logged_in():

.. doctest::
    :hide:
    
    >>> import fudge

.. doctest::

    >>> def show_secret_word():
    ...     import auth
    ...     user = auth.current_user()
    ...     if user.is_logged_in():
    ...         print "Bird is the word"
    ...     else:
    ...         print "Access denied"
    ... 
    >>> @fudge.patch('auth.current_user')
    ... def test_secret_word(current_user):
    ...     user = current_user.expects_call().returns_fake()
    ...     user = user.provides('is_logged_in').returns(True)
    ...     show_secret_word()
    ... 
    >>> test_secret_word()
    Bird is the word

Note that if ``user.is_logged_in()`` is not called then no error will be raised because it's provided, not expected:

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
    >>> # Now, the check_user function gets called instead:
    >>> auth.show_secret_word_for_user("bert")
    Bird is the word
    >>> auth.show_secret_word_for_user("ernie")
    Access denied

Cascading Objects
=================

Some objects you might want to work with will spawn a long chain of objects.  Here is an example of fudging a cascading `SQLAlchemy query <http://www.sqlalchemy.org/docs/05/ormtutorial.html#querying>`_.  Notice that :meth:`Fake.returns_fake() <fudge.Fake.returns_fake>` is used to specify that ``session.query(User)`` should return a new object.  Notice also that because query() should be iterable, it is set to return a list of fake User objects.

.. doctest::
    
    >>> import fudge
    >>> session = fudge.Fake('session')
    >>> query = (session.provides('query')
    ...                 .returns_fake()
    ...                 .provides('order_by')
    ...                 .returns(
    ...                     [fudge.Fake('User').has_attr(name='Al', lastname='Capone')]
    ...                 )
    ... )
    >>> from models import User
    >>> for instance in session.query(User).order_by(User.id):
    ...     print instance.name, instance.lastname
    ... 
    Al Capone

Multiple Return Values
======================

Let's say you want to test code that needs to call a function multiple times and get back multiple values.  Up until now, you've just seen the :meth:`Fake.returns() <fudge.Fake.returns>` method which will return a value infinitely.  To change that, call :meth:`Fake.next_call() <fudge.Fake.next_call>` to advance the call sequence.  Here is an example using a shopping cart scenario:

.. doctest::
    
    >>> cart = (fudge.Fake('cart')
    ...              .provides('add')
    ...              .with_args('book')
    ...              .returns({'contents': ['book']})
    ...              .next_call()
    ...              .with_args('dvd')
    ...              .returns({'contents': ['book', 'dvd']}))
    >>> cart.add('book')
    {'contents': ['book']}
    >>> cart.add('dvd')
    {'contents': ['book', 'dvd']}
    >>> cart.add('monkey')
    Traceback (most recent call last):
    ...
    AssertionError: This attribute of fake:cart can only be called 2 time(s).

Expecting A Specific Call Order
===============================

You may need to test an object that expects its methods to be called in a specific order. 
Just preface any calls to :func:`fudge.Fake.expects` with :func:`fudge.Fake.remember_order` like this:

.. doctest::
    
    >>> import fudge
    >>> session = (fudge.Fake("session").remember_order()
    ...                                 .expects("get_count").returns(0)
    ...                                 .expects("set_count").with_args(5)
    ...                                 .expects("get_count").returns(5))
    ... 
    >>> session.get_count()
    0
    >>> session.set_count(5)
    >>> session.get_count()
    5
    >>> fudge.verify()

A descriptive error is printed if you call things out of order:

.. doctest::
    :hide:
    
    >>> fudge.clear_calls()

.. doctest::

    >>> session.set_count(5)
    Traceback (most recent call last):
    ...
    AssertionError: Call #1 was fake:session.set_count(5); Expected: #1 fake:session.get_count()[0], #2 fake:session.set_count(5), #3 fake:session.get_count()[1], end

.. doctest::
    :hide:
    
    >>> fudge.clear_expectations()

.. _creating-a-stub:

Allowing any call or attribute (a complete stub)
================================================

If you need an object that lazily provides any call or any attribute then
you can declare :func:`fudge.Fake.is_a_stub`.  Any requested method or
attribute will always return a new :class:`fudge.Fake` instance making it
easier to work complex objects.  Here is an example:

.. doctest::
  
  >>> Server = fudge.Fake('xmlrpclib.Server').is_a_stub()
  >>> pypi = Server('http://pypi.python.org/pypi')
  >>> pypi.list_packages()
  fake:xmlrpclib.Server().list_packages()
  >>> pypi.package_releases()
  fake:xmlrpclib.Server().package_releases()

Stubs like this carry on infinitely:

.. doctest::

  >>> f = fudge.Fake('base').is_a_stub()
  >>> f.one.two.three().four
  fake:base.one.two.three().four

.. note::
  
  When using :func:`fudge.Fake.is_a_stub` you can't lazily access any
  attributes or methods if they have the same name as a Fake method,
  like ``returns()`` or ``with_args()``.  You would need to declare
  expectations for those directly using :func:`fudge.expects`, etc.

.. _working-with-arguments:

Working with Arguments
======================

The :func:`fudge.Fake.with_args` method optionally allows you to declare expectations of 
how arguments should be sent to your object.  It's usually sufficient to expect an exact 
argument value but sometimes you need to use :mod:`fudge.inspector` functions for dynamic values.

Here is a short example:

.. doctest::
    
    >>> import fudge
    >>> from fudge.inspector import arg
    >>> image = (fudge.Fake("image")
    ...               .expects("save")
    ...               .with_args("JPEG", arg.endswith(".jpg"), resolution=arg.any())
    ... )

This declaration is very flexible; it allows the following calls:

.. doctest::

    >>> image.save("JPEG", "/tmp/unicorns-and-rainbows.jpg", resolution=72)
    >>> image.save("JPEG", "/tmp/me-being-serious.jpg", resolution=96)

.. doctest::
    :hide:
    
    >>> fudge.verify()
    >>> fudge.clear_expectations()
    
.. _Nose: http://somethingaboutorange.com/mrl/projects/nose/
.. _py.test: http://codespeak.net/py/dist/test.html

That's it!  See the fudge API for details:

.. toctree::
    :glob:
    
    api/*