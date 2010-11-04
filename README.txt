
Fudge is a module for replacing real objects with fakes (mocks, stubs, etc) while testing.

Documentation is available at http://farmdev.com/projects/fudge/ or else, you can build it from source like this::
    
    $ easy_install Sphinx
    $ cd docs
    $ make html

then open _build/html/index.html in your web browser.

To run tests, you can use tox for all supported versions of Python.
You can install it with pip::
    
    $ pip install tox

Then execute::
    
    $ ./run_tests.sh

Or simply::
    
    $ tox

