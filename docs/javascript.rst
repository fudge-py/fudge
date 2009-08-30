
.. _javascript-fudge:

====================
Fudge For JavaScript
====================

Although `Ersatz <http://github.com/centro/ersatz/tree/master>`_ is a port of `Mocha <http://mocha.rubyforge.org/>`_ to JavaScript and that's pretty much what :ref:`Fudge <using-fudge>` is, I couldn't get Ersatz to work with one of my libraries because it uses Prototype.  So I started porting Fudge to JavaScript.  As of this writing it has only been partially implemented.

Install
=======

Download the :ref:`Fudge source distribution <fudge-source>` and copy ``javascript/fudge/`` to your webroot.  To use it in your tests all you need is a script tag like this:

.. code-block:: html
    
    <script src="fudge/fudge.js" type="text/javascript"></script>

If you want to run Fudge's own tests, then cd into the ``javascript/`` directory, start a simple webserver::

    $ python fudge/testserver.py

and open http://localhost:8000/tests/test_fudge.html  Take note that while Fudge's *tests* require jQuery, Fudge itself does not require jQuery.

Usage
=====

Refer to :ref:`using-fudge` in Python to get an idea for how to use the JavaScript version.  As mentioned before, the JavaScript port is not yet fully implemented.

Here is a quick example:

.. code-block:: javascript
    
    // if you had e.g. a session object that looked something like:
    yourapp = {};
    yourapp.session = {
        set: function(key, value) {
            // ...
        }
    }
    yourapp.startup = function() {
        yourapp.session.set('saw_landing_page',true);
    };
    
    // and if you wanted to test the startup() method above, then you could 
    // declare a fake object for a test:
    var fake_session = new fudge.Fake('session').expects('set').with_args('saw_landing_page',true);
    
    // patch your production code:
    yourapp.session = fake_session;
    
    // and run a test:
    fudge.clear_calls();
    yourapp.startup();
    fudge.verify();
    