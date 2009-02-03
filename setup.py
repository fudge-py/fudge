
from setuptools import setup, find_packages
import re
version = None
for line in open("./fudge/__init__.py"):
    m = re.search("__version__\s+=\s+(.*)", line)
    if m:
        version = m.group(1).strip()
        version = version[1:-1] # quotes
        break
assert version

setup(
    name='fudge',
    version=version,
    description="Replace real objects with fakes (mocks, stubs, etc) while testing.",
    long_description="""
Complete documentation is available at http://farmdev.com/projects/fudge/

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
    license=open("./LICENSE.txt").read(),
    packages=find_packages(exclude=['ez_setup']),
    install_requires=[],
    tests_require=['nose', 'Sphinx'],
    url='http://farmdev.com/projects/fudge/',
    include_package_data=True,
    )
