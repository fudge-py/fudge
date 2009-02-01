
Copy ``javascript/fudge/`` to your webroot.  To use it in your tests all you need is a script tag like this::
    
    <script src="fudge/fudge.js" type="text/javascript"></script>

If you want to run Fudge's own tests, then cd into the ``javascript/`` directory, start a simple webserver::

    $ python fudge/testserver.py

and open http://localhost:8000/tests/test_fudge.html  Take note that while Fudge's *tests* require jQuery, Fudge itself does not require jQuery.