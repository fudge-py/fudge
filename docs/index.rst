===================
Fudge Documentation
===================

Fudge is a Python module for mocks, stubs, and fakes.

A Quick Example: Testing Something That Sends Email
===================================================

Say you have a method that uses Python's standard `smtplib <http://docs.python.org/library/smtplib.html#module-smtplib>`_ module 
to send email:

.. doctest::

    >>> def send_email(recipient, sender, msg):
    ...     from smtplib import SMTP
    ...     msg = ("From: %s\r\nTo: %s\r\n\r\n%s" % (
    ...             sender, ", ".join(recipient), msg))
    ...     s = SMTP()
    ...     s.connect()
    ...     s.sendmail(sender, recipient, msg)
    ...     s.close()
    ...     print "Sent an email to %s" % recipient
    ... 
    >>> 

You can use Fudge to test this method without actually executing the email 
sending code.  Instead, since you trust that smtplib works, you can expect 
that it is used according to its interface.  

First set up a fake expectation of how the SMTP class should be used:

.. doctest::
    
    >>> import fudge
    >>> SMTP = fudge.Fake()
    >>> SMTP = SMTP.expects('__init__') # s = SMTP()
    >>> SMTP = SMTP.expects('connect') # s.connect()
    >>> SMTP = SMTP.expects('sendmail').with_arg_count(3) # s.sendmail(sender, recipient, msg)
    >>> SMTP = SMTP.expects('close') # s.close()

Next, patch the module temporarily while you test:
    
.. doctest::

    >>> import smtplib
    >>> patched_smtplib = fudge.patch_object(smtplib, "SMTP", SMTP)

Now you can run the code with the fake object:

.. doctest::
    
    >>> fudge.start()
    >>> send_email( "kumar.mcmillan@gmail.com", "you@yourhouse.com", 
    ...                                 "hi, I'm reading about Fudge!")
    ... 
    Sent an email to kumar.mcmillan@gmail.com
    >>> fudge.stop()
    >>> patched_smtplib.restore()

Instead of using ``with_arg_count()`` you'd probably want to check that the first argument is the intended sender and the second is the intended recipient (important to not to mix these up).  I'll show you how to do something like that in the next example.
    
Another Example: Fudging The Google AdWords API
===============================================

Let's say you have some code that interacts with `Google's AdWords API <http://code.google.com/apis/adwords/>`_, a SOAP web service for managing search engine ad campaigns.  If your automated tests run code that use this API, you have a couple options:

1. Always test against the AdWords Sandbox.  
   
   - Downsides: This would slow down your tests and you might go over your usage quota.  You'd also end up with a lot of redundant test code since each connection would need to be setup correctly with campaign data.
   - Upsides: You'd be pretty confident that your code will work against the production version of the Ad Words service.
   
2. Fabricate a fake SOAP server.  

   - *Shudder*.  Nevermind
   
3. **Use the Fudge module to replace your AdWords API object with a fake object that behaves the same.**  
   
   - Downsides: In case the AdWords API ever changes, your code would still work in your test environment giving you false positives.  
   - Upsides: You no longer depend on the Internet or the AdWords sandbox service and your tests will run a lot faster.

As you can see, there are pros and cons to using fake objects in place of real ones.  As a general rule of thumb you should use fake objects sparingly.  First and foremost, ask yourself, *what* am I testing?  If you're using something like the `awapi <http://code.google.com/p/google-api-adwords-python-lib>`_ Python module to connect to the AdWords API then you do not need to test awapi itself; it already has unit tests of its own.  Plus, it calls an external web service.  What if the service is down?  What if it doesn't have the data you're expecting?  Fudge eliminates the Internet from this problem entirely.

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
    >>> Client = fudge.Fake()
    >>> Client = Client.expects('__init__').with_args(headers=dict(email="some-google-id@wherever.com",
    ...                                                            password="xxxxxx"))
    ... 

Next, replace the real ``awapi.lib.Client.Client`` object temporarily during your test:

.. doctest::

    >>> import awapi.lib.Client
    >>> patched_awapi = fudge.patch_object(awapi.lib.Client, "Client", Client)

Now, run the get_client() method against your fake objects:

.. doctest::

    >>> fudge.start()
    >>> client = get_client(email="some-google-id@wherever.com", password="xxxxxx")
    >>> client # doctest: +ELLIPSIS
    <fudge.Fake object at ...>
    >>> fudge.stop()

Finally, restore the real Client object:

.. doctest::

    >>> patched_awapi.restore()

Fudging An Object That Returns an Object
----------------------------------------

Next, consider this method to create a campaign.  Because SOAP is so amazing, you 
have to first obtain the campaign_service object from the client object then you can 
make a call on the campaign_service to create a simple campaign:

.. doctest::
    
    >>> def create_campaign(client, name=None, dailyBudget=0, status='Active'):
    ...     campaign_service = client.GetCampaignService('https://sandbox.google.com')
    ...     campaign = dict(name=name, 
    ...                     dailyBudget=dailyBudget, 
    ...                     status=status)
    ...     return campaign_service.AddCampaign(campaign)
    ... 
    >>> 

This is how to set this with Fudge:

.. doctest::

    >>> import fudge
    >>> client = fudge.Fake().expects('GetCampaignService').with_args(
    ...                                             'https://sandbox.google.com')
    >>> service = client.returns_fake() # set the return to a new fake object
    >>> service = service.expects('AddCampaign').with_args(
    ...                     name="Thanksgiving Day Sale",
    ...                     dailyBudget=10000,
    ...                     status='Paused')
    >>> service = service.returns("Campaign created successfully")

Since the method doesn't import anything you don't 
have to use a patcher, just start testing:

.. doctest::
    
    >>> fudge.start()
    >>> result = create_campaign( client,
    ...                     name="Thanksgiving Day Sale", 
    ...                     dailyBudget=10000, 
    ...                     status='Paused')
    ... 
    >>> result
    'Campaign created successfully'




