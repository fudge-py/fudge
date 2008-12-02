===================
Fudge Documentation
===================

Fudge is a Python module for using fake objects (mocks, stubs, etc) to test real ones.

The module is designed for two specific situations:

- Replace an object
  
  - Temporarily return a canned value for a 
    method or call a method without executing real code.

- Make sure your code uses an object correctly

  - Declare expectations about what methods should be 
    called and what arguments should be sent.

Example: Fudging Email
======================

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
    >>> SMTP = fudge.Fake()
    >>> SMTP = SMTP.expects('__init__')
    >>> SMTP = SMTP.expects('connect')
    >>> SMTP = SMTP.expects('sendmail').with_arg_count(3)
    >>> SMTP = SMTP.expects('close')

Instead of using ``with_arg_count()`` you'd probably want to check that the first argument is the intended sender and the second is the intended recipient (important to not to mix these up).  I'll show you how to do something like that in an upcoming example.

Next, patch the module temporarily with your fake:
    
.. doctest::

    >>> patched_smtplib = fudge.patch_object("smtplib", "SMTP", SMTP)

Now you can run the code with the fake object:

.. doctest::
    
    >>> fudge.start()
    >>> send_email( "kumar.mcmillan@gmail.com", "you@yourhouse.com", 
    ...                                 "hi, I'm reading about Fudge!")
    ... 
    Sent an email to kumar.mcmillan@gmail.com
    >>> fudge.stop()
    >>> patched_smtplib.restore()

A Simple Test Case
==================

The above code could also be written as a test case:

.. doctest::
    
    >>> @fudge.with_fakes
    ... @fudge.with_patched_object("smtplib", "SMTP", SMTP)
    ... def test_email():
    ...     send_email( "kumar.mcmillan@gmail.com", 
    ...                 "you@yourhouse.com", 
    ...                 "Mmmm, fudge")
    ... 
    >>> test_email()
    Sent an email to kumar.mcmillan@gmail.com

You could also apply these decorators to a method on a class 
descending from ``unittest.TestCase``

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
    AssertionError: fake:unnamed.sendmail() was called with 1 arg(s) but expected 3

Clearing Expectations
=====================

Fudge assumes that when you declare expectations on a Fake, 
you will use the Fake in more than one test.  For this reason, 
you'll need to tear down queued up expectations explicitly if you 
want to start testing with new fake objects:

.. doctest::

    >>> fudge.clear_expectations()

A Complete Test Module Using Nose
=================================

If you're using a test framework like Nose that supports module level 
setup / teardown hooks, one strategy is to declare all Fake objects at the 
top of your test module and clear expectations after all tests are run on 
your Fake objects.  Here is an example of how you could lay out your test 
module:

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

The Nose framework executes the above test module as follows:
    
.. doctest::

    >>> try:
    ...     test_email()
    ... finally:
    ...     teardown()
    Sent an email to kumar.mcmillan@gmail.com

Example: Stubs Without Expectations
===================================

If you want a fake object where the methods can be called but are not 
expected to be called, the code is just the same but instead of 
expects() you use provides().  Here is an example of always returning True 
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
    
    >>> fudge.start()
    >>> show_secret_word(auth)
    Bird is the word
    >>> fudge.stop()

Note that if user.is_logged_in() is not called then no error will be raised.

Example: Fudging A Callable
===========================

Sometimes you might only need to replace a single function, not an entire object.  
You can do this with the keyword argument callable=True.  For example:

.. doctest::
    
    >>> login = fudge.Fake(callable=True).with_args("eziekel", "pazzword").returns(True)
    
    >>> def show_secret_word(username, password):
    ...     import auth
    ...     logged_in = auth.login(username, password)
    ...     if logged_in:
    ...         print "Bird is the word"
    ...     else:
    ...         print "Access Denied"
    ... 
    >>> @fudge.with_fakes
    ... @fudge.with_patched_object("auth", "login", login)
    ... def test_show_secret_word():
    ...     show_secret_word("eziekel", "pazzword")
    ... 
    >>> test_show_secret_word()
    Bird is the word
    
Example: Fudging An API
=======================

Let's say you have some code that interacts with `Google's AdWords API <http://code.google.com/apis/adwords/>`_, a SOAP web service for managing search engine ad campaigns.  If your automated tests run code that use this API, you have a couple options:

1. Always test against the AdWords Sandbox.  
   
   - Downsides: This would slow down your tests and you might go over your usage quota.  You'd also end up with a lot of redundant test code since each connection would need to be setup correctly with campaign data.
   - Upsides: You'd be pretty confident that your code will work against the production version of the Ad Words service.
   
2. Fabricate a fake SOAP server.  

   - *Shudder*.  Nevermind
   
3. **Use the Fudge module to replace your AdWords API object with a fake object that behaves the same.**  
   
   - Downsides: In case the AdWords API ever changes, your code would still work in your test environment giving you false positives.  
   - Upsides: You no longer depend on the Internet or the AdWords sandbox service and your tests will run a lot faster.

As you can see, there are pros and cons to using fake objects in place of real ones.  As a general rule of thumb you should use fake objects sparingly.  First and foremost, ask yourself, *what* am I testing?  If you're using something like the `awapi <http://code.google.com/p/google-api-adwords-python-lib>`_ Python module to connect to the AdWords API then you do not need to test awapi itself; it already has unit tests of its own.  Plus, it calls an external web service.  What if the service is down?  What if it doesn't have the data you're expecting?  Fudge eliminates these problem entirely.

Here's some code you might want to test.  This method creates and returns a new AdWords client:

.. doctest::

    >>> def get_client(**auth_kwargs):
    ...     from awapi.lib.Client import Client
    ...     client = Client(headers=auth_kwargs)
    ...     return client
    >>> 

How would you unit test this methods without touching the real server?  Here's how to do it with Fudge.  First set up a fake Client object with an expectation that it will be called the same way that the real one gets called:

.. doctest::

    >>> import fudge
    >>> Client = fudge.Fake('Client')
    >>> Client = Client.expects('__init__').with_args(headers=dict(email="some-google-id@wherever.com",
    ...                                                            password="xxxxxx"))
    ... 

Next, replace the real ``awapi.lib.Client.Client`` object temporarily during your test:

.. doctest::

    >>> patched_awapi = fudge.patch_object("awapi.lib.Client", "Client", Client)

Now, run the get_client() method against your fake objects:

.. doctest::
    
    >>> fudge.start()
    >>> client = get_client(email="some-google-id@wherever.com", password="xxxxxx")
    >>> repr(client)
    'fake:Client'
    >>> fudge.stop()

Finally, restore the real Client object:

.. doctest::

    >>> patched_awapi.restore()

Because we are done testing with the Fake object above, 
clear all its expectations:

.. doctest::
    
    >>> fudge.clear_expectations()

Example: Fudging Chained Objects
================================

Consider this method to create a campaign.  Because SOAP is so amazing, you 
have to first obtain the campaign_service object from the client object then you can 
make a call on the campaign_service to create a new campaign:

.. doctest::
    
    >>> def create_campaign(client, name=None, dailyBudget=0, status='Active'):
    ...     campaign_service = client.GetCampaignService('https://sandbox.google.com')
    ...     campaign = dict(name=name, 
    ...                     dailyBudget=dailyBudget, 
    ...                     status=status)
    ...     result = campaign_service.AddCampaign(campaign)
    ...     print "Created new campaign with ID %s" % result[0]['id']
    ... 
    >>> 

This is how to set it up with Fudge:

.. doctest::

    >>> import fudge
    >>> client = fudge.Fake().expects('GetCampaignService').with_args('https://sandbox.google.com')
    >>> service = client.returns_fake()
    >>> service = service.expects('AddCampaign').with_args({'name': "Thanksgiving Day Sale",
    ...                                                     'dailyBudget': 10000,
    ...                                                     'status': 'Paused'})
    >>> service = service.returns([{'id':12345}])

Since the method doesn't import anything you don't 
have to use a patcher, just pass in the fake instance while testing:

.. doctest::
    
    >>> fudge.start()
    >>> create_campaign( client,
    ...                 name="Thanksgiving Day Sale", 
    ...                 dailyBudget=10000, 
    ...                 status='Paused')
    ... 
    Created new campaign with ID 12345
    >>> fudge.stop()


API Reference
=============

.. toctree::
    :glob:
    
    api/*



