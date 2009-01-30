
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
    description="",
    long_description="",
    author='Kumar McMillan',
    author_email='kumar.mcmillan@gmail.com',
    packages=find_packages(exclude=['ez_setup']),
    install_requires=[],
    tests_require=['nose'],
    #url='',
    include_package_data=True,
    )
