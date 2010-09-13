
import re
import sys

from setuptools import setup, find_packages

version = None
for line in open("./fudge/__init__.py"):
    m = re.search("__version__\s*=\s*(.*)", line)
    if m:
        version = m.group(1).strip()[1:-1] # quotes
        break
assert version

extra_setup = {}
if sys.version_info >= (3,):
    extra_setup['use_2to3'] = True
    # extra_setup['use_2to3_fixers'] = ['your.fixers']

setup(
    name='fudge',
    version=version,
    description="Replace real objects with fakes (mocks, stubs, etc) while testing.",
    long_description="""
Complete documentation is available at http://farmdev.com/projects/fudge/

This module is designed for two specific situations:

- Replace an object
  
  - Temporarily return a canned value for a 
    method or allow a method to be called without affect.

- Ensure an object is used correctly

  - Declare expectations about what methods should be 
    called and what arguments should be sent.

Here is a quick preview of how you can test code that sends email without actually sending email::
    
    >>> import fudge
    >>> SMTP = fudge.Fake('SMTP')
    >>> SMTP = SMTP.expects('__init__')
    >>> SMTP = SMTP.expects('connect')
    >>> SMTP = SMTP.expects('sendmail').with_arg_count(3)
    >>> SMTP = SMTP.expects('close')
    
""",
    author='Kumar McMillan',
    author_email='kumar.mcmillan@gmail.com',
    license="The MIT License",
    packages=find_packages(exclude=['ez_setup']),
    install_requires=[],
    tests_require=['nose', 'NoseJS', 'Sphinx'],
    url='http://farmdev.com/projects/fudge/',
    include_package_data=True,
    classifiers = [
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Testing'
        ],
    **extra_setup
    )
