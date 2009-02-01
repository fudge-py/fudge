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

Download / Install
==================

Just type::

    $ sudo easy_install fudge

If you don't have ``easy_install`` for Python you can get it like this::

    $ wget http://peak.telecommunity.com/dist/ez_setup.py
    $ sudo python ez_setup.py


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

Instead of using ``with_arg_count()`` you'd probably want to check that the first argument is the intended sender and the second is the intended recipient (important to not to mix these up).  I'll show you how to do something like that in an upcoming example.

Next, patch the module temporarily with your fake:
    
.. doctest::

    >>> patched_smtplib = fudge.patch_object("smtplib", "SMTP", SMTP)

Now you can run the code with the fake object:

.. doctest::
    
    >>> fudge.start()
    >>> send_email( "kumar@hishouse.com", "you@yourhouse.com", 
    ...                                   "hi, I'm reading about Fudge!")
    ... 
    Sent an email to kumar@hishouse.com
    >>> fudge.stop()
    >>> patched_smtplib.restore()

More Examples
=============

.. toctree::
   :maxdepth: 2
   
   examples

API Reference
=============

.. toctree::
    :glob:
    
    api/*
