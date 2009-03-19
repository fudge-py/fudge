
===========================
Why Another Mock Framework?
===========================

Can't you do most of this in plain old Python?  If you're just replacing methods then yes but when you need to manage expectations, it's not so easy.

Fudge started when a co-worker showed me `Mocha <http://mocha.rubyforge.org/>`_ for Ruby.  I liked it because it was a much simpler version of `jMock`_ and jMock allows you to do two things at once: 1) build a fake version of a real object and 2) inspect that your code uses it correctly (post mortem).  Up until now, I've built all my mock logic in plain Python and noticed that I spent gobs of code doing these two things in separate places.  The jMock approach gets rid of the need for a post mortem and the expectation code is very readable.

What about all the other mock frameworks for Python?  I *really* didn't want to build another mock framework, honestly.  Here were my observations of the scenery:

- `pMock <http://pmock.sourceforge.net/>`_ (based on `jMock`_)

  - This of course is based on the same jMock interface that I like.  However, its site claims it has not been maintained since 2004 and besides that jMock is too over engineered for my tastes and pMock does not attempt to fix that.

- `minimock <http://pypi.python.org/pypi/MiniMock>`_

  - As far as I can tell, there is no easy, out-of-the-box way to use minimock in anything other than a doctest.
  - It doesn't really deal with expectations, just replacements (stubbing).

- `mock <http://www.voidspace.org.uk/python/mock.html>`_

  - I didn't like how mock focused on post mortem inspection.

- `pyMock <http://theblobshop.com/pymock/>`_ (based on `EasyMock`_)

  - This uses a record / playback technique whereby you act upon your real objects then flip a switch and they become fake.  This seems like it has some benefits for maintenance but I'm not sure that the overhead of recording with real objects is worth it.  I suppose you'd need a real database, a real web service, etc.

- `Mox <http://code.google.com/p/pymox/>`_ (based on `EasyMock`_)
  
  - This also uses the record / playback technique but with a DSL (domain specific language).  It was brought to my attention after creating Fudge but thought it was worth mentioning.

- `mocker <http://labix.org/mocker>`_ (based on `EasyMock`_ and others)
  
  - This was also `pointed out to me <http://farmdev.com/thoughts/70/fudge-another-python-mock-framework/>`_ after developing Fudge.
  - Mocker is another record / playback implementation but seems to have a cleaner interface than most.  I still do not see the practicality of record / playback.  How do you write tests in record mode?  I am probably missing it but nowhere in the docs do I see practical examples for creating test code.  Instead the examples are interactive sessions which is not how I typically write tests.
  - The docs for mocker, like docs for other tools, do not focus on any real-world problem that a mock framework can solve.  This is hard for my brain.  It is hard for me to look at code such as obj.hello() and imagine that this would be useful for, say, mocking out sendmail(). 
  - However, mocker certainly looks like it has more features than Fudge so it is worth checking out.
  

.. _jMock: http://www.jmock.org/
.. _EasyMock: http://www.easymock.org/