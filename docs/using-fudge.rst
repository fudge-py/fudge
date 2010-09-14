
.. _using-fudge:

===========
Using Fudge
===========

Fudging A Web Service
=====================

If you're testing code that uses a Web Service you wouldn't want to rely on the Internet because that would slow you down.  This is a good scenario in which to use mock objects.  Say you have a Twitter bot that looks something like this:

.. doctest::

    >>> import oauthtwitter
    >>> def post_msg_to_twitter(msg):
    ...     api = oauthtwitter.OAuthApi(
    ...         '<consumer_key>', '<consumer_secret>',
    ...         '<oauth_token>', '<oauth_token_secret>'
    ...     )
    ...     api.UpdateStatus(msg)
    ... 
    >>> 

Since the `oauthtwitter`_ module is maintained independently, you can probably trust that your code will work as long as it calls the right methods (*caveat emptor!*).  To set this up in Fudge you **declare an expectation** of how the OAuthApi class should be used like this:

.. _oauthtwitter: http://code.google.com/p/oauth-python-twitter/

.. doctest::
    
    >>> import fudge
    >>> FakeOAuthApi = (fudge.Fake('OAuthApi')
    ...                     .expects('__init__')
    ...                     .with_args(
    ...                         '<consumer_key>', '<consumer_secret>',
    ...                         '<oauth_token>', '<oauth_token_secret>'
    ...                     )
    ... )
    >>> 

This says that the class should be instantiated with four arguments having specific string values.  The returned value of ``__init__`` is a new object instance so you can declare the instance methods like this:

.. doctest::

    >>> fake_instance = FakeOAuthApi.returns_fake().expects('UpdateStatus').with_arg_count(1)

Fudge lets you declare expectations as loose or as tight as you want.  If you don't care about the exact arguments, you can leave off the call to :meth:`fudge.Fake.with_args`.  If you don't care if a method is actually called you can use :meth:`fudge.Fake.provides` instead of :meth:`fudge.Fake.expects`.  Likewise, :meth:`fudge.Fake.with_arg_count` can be used when you don't want to worry about the actual argument values.  There are `argument inspectors <working-with-arguments>`_ for checking values in other ways.

To activate the declarative mock created above, :func:`patch <fudge.patcher.patch_object>` the module temporarily with your fake:
    
.. doctest::
    
    >>> import oauthtwitter
    >>> patched_api = fudge.patch_object(oauthtwitter, "OAuthApi", FakeOAuthApi)

Now you can run code against the fake.  Begin each test with :func:`fudge.clear_calls` to reset call history from previous tests:

.. doctest::
    
    >>> fudge.clear_calls()

Run the code you want to test:

.. doctest::

    >>> post_msg_to_twitter("hey there fellow testing freaks!")

Call :func:`fudge.verify` to make sure all expectations were met.  You probably want this at the end of your test but not in a tearDown().

.. doctest::

    >>> fudge.verify()

Aha, no errors, which means it was successful.  Finally, revert the patched object like this:

.. doctest::

    >>> patched_api.restore()
    
A Simple Test Case
==================

The above code could also be written as a test function, compatible with `Nose`_ or `py.test`_.  To make things easier, you wrap your test in the :func:`fudge.with_fakes` decorator to ensure that :func:`fudge.clear_calls` and :func:`fudge.verify` are executed.

.. doctest::
    
    >>> import fudge
    >>> @fudge.with_fakes
    ... def test_post_msg_to_twitter():
    ...     with fudge.patched_context(oauthtwitter, "OAuthApi", FakeOAuthApi):
    ...         post_msg_to_twitter("mmm, fudge")
    ... 
    >>> test_post_msg_to_twitter()

In addition to the with statement, you can also use the :func:`fudge.patcher.with_patched_object` decorator.

A unittest.TestCase
===================

You can write the same exact test using a standard ``unittest.TestCase`` like this:

.. doctest::
    
    >>> import fudge
    >>> import unittest
    >>> class TestPostMsgToTwitter(unittest.TestCase):
    ... 
    ...     def setUp(self):
    ...         fudge.clear_expectations() # from previous tests
    ...         FakeOAuthApi = (fudge.Fake('OAuthApi')
    ...                             .expects('__init__')
    ...                             .with_args(
    ...                                 '<consumer_key>', '<consumer_secret>',
    ...                                 '<oauth_token>', '<oauth_token_secret>'
    ...                             )
    ...         )
    ...         fake_api = (FakeOAuthApi.returns_fake()
    ...                             .expects('UpdateStatus')
    ...                             .with_arg_count(1)
    ...         )
    ...
    ...         self.patched = fudge.patch_object(oauthtwitter, "OAuthApi", FakeOAuthApi)
    ...     
    ...     @fudge.with_fakes
    ...     def test_post_msg_to_twitter(self):
    ...         post_msg_to_twitter("mmm, fudge")
    ... 
    ...     def tearDown(self):
    ...         self.patched.restore()
    ... 
    >>> test = TestPostMsgToTwitter('test_post_msg_to_twitter')
    >>> test.run()

Be sure to apply the decorator :func:`fudge.with_fakes` to any test method that 
might use fake objects.  This will ensure that :func:`fudge.clear_calls` and :func:`fudge.verify` are executed.

Failed Expectations
===================

Since the previous code declared expectations for how the 
oauthtwitter module should be used, your test will raise an 
AssertionError when those expectations are not met.  For example:

.. doctest::
    :hide:
    
    >>> fudge.clear_expectations()
    >>> FakeOAuthApi = (fudge.Fake('OAuthApi')
    ...                     .expects('__init__')
    ...                     .with_args(
    ...                         '<consumer_key>', '<consumer_secret>',
    ...                         '<oauth_token>', '<oauth_token_secret>'
    ...                     )
    ... )
    >>> fake_api = (FakeOAuthApi.returns_fake()
    ...                       .expects('UpdateStatus')
    ... )
    >>> patched_api = fudge.patch_object(oauthtwitter, "OAuthApi", FakeOAuthApi)
    
.. doctest::
    
    >>> api = oauthtwitter.OAuthApi('<nope>', '<wrong>')
    Traceback (most recent call last):
    ...
    AssertionError: fake:OAuthApi.__init__(...) was called unexpectedly with args ('<nope>', '<wrong>')

If your code forgets to call an important method, that would raise an error at verification time:

.. doctest::
    :hide:
    
    >>> fudge.clear_calls()
    
.. doctest::
    
    >>> api = oauthtwitter.OAuthApi(
    ...     '<consumer_key>', '<consumer_secret>', '<oauth_token>', '<oauth_token_secret>'
    ... )
    >>> fudge.verify()
    Traceback (most recent call last):
    ...
    AssertionError: fake:__init__.UpdateStatus() was not called

.. doctest::
    :hide:
    
    >>> patched_api.restore()

Fudge is designed to report the best possible exception messages in your tests.
    
Clearing Expectations
=====================

Fudge assumes that when you declare expectations on a Fake, 
you will use the Fake object in more than one test.  For this reason, 
you'll need to clear the expectation registry explicitly if you 
want to start testing with another fake object.

In other words, if one test uses a fake Twitter API but some test later on 
uses a fake database and has nothing to do with email then you'll need 
to clear the Twitter API expectations before testing with the fake database.

.. doctest::

    >>> fudge.clear_expectations()

This is different from :func:`fudge.clear_calls`, which only 
clears the actual calls made to your objects during a test.

Typically, this would be done at a module level setup() hook supported by `Nose`_ or `py.test`_.

Stubs Without Expectations
==========================

If you want a fake object where the methods can be called but are not 
expected to be called, the code is just the same but instead of 
:meth:`Fake.expects() <fudge.Fake.expects>` you use :meth:`Fake.provides() <fudge.Fake.provides>`.  Here is an example of always returning True 
for the method is_logged_in():

.. doctest::
    
    >>> import fudge
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

Note that if ``user.is_logged_in()`` is not called then no error will be raised.

Replacing A Method
==================

Sometimes returning a static value isn't good enough, you actually need to run some code.  
You can do this using :meth:`Fake.calls() <fudge.Fake.calls>` like this:

.. doctest::
    
    >>> import fudge
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
    
    >>> import auth
    >>> import fudge
    >>> @fudge.with_fakes
    ... def test_login():
    ...     login = (fudge.Fake(callable=True)
    ...                     .with_args("eziekel", "pazzword")
    ...                     .returns(True)
    ...     )
    ...     with fudge.patched_context("auth", "login", login):
    ...         logged_in = auth.login("eziekel", "pazzword")
    ...         if logged_in:
    ...             print "Welcome!"
    ...         else:
    ...             print "Access Denied"
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

.. doctest::
    :hide:
    
    >>> fudge.clear_expectations()

Cascading Objects
=================

Some objects you might want to work with will support *cascading* which means each method returns an object.  Here is an example of fudging a cascading `SQLAlchemy query <http://www.sqlalchemy.org/docs/05/ormtutorial.html#querying>`_.  Notice that :meth:`Fake.returns_fake() <fudge.Fake.returns_fake>` is used to specify that ``session.query(User)`` should return a new object.  Notice also that because query() should be iterable, it is set to return a list of fake User objects.

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
    
    >>> import fudge
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

Expecting A Specific Call Order
===============================

You may need to test an object that expects its methods to be called in a specific order. 
Just preface any calls to :func:`fudge.Fake.expects` with :func:`fudge.Fake.remember_order` like this:

.. doctest::
    
    >>> import fudge
    >>> session = (fudge.Fake("session").remember_order()
    ...                                 .expects("get_count").returns(0)
    ...                                 .expects("set_count").with_args(5)
    ...                                 .next_call(for_method="get_count").returns(5))
    ... 
    >>> session.get_count()
    0
    >>> session.set_count(5)
    >>> session.get_count()
    5
    >>> fudge.verify()

A descriptive error is printed if you call things out of order:

.. doctest::

    >>> fudge.clear_calls()
    >>> session.set_count(5)
    Traceback (most recent call last):
    ...
    AssertionError: Call #1 was fake:session.set_count(5); Expected: #1 fake:session.get_count()[0], #2 fake:session.set_count(5), #3 fake:session.get_count()[1], end

.. doctest::
    :hide:
    
    >>> fudge.clear_expectations()

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
    ...               .with_args("JPEG", arg.endswith(".jpg"), resolution=arg.any_value())
    ... )

This declaration is very flexible; it allow the following arguments to be sent :

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