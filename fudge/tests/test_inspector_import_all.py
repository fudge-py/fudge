
from __future__ import absolute_import
from fudge.inspector import *

def test_import_all():
    assert "arg" in globals()