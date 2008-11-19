
from nose.tools import eq_
import fudge

class Freddie(object):
    pass
        
def test_patch_obj():
    class holder:
        exc = Exception()
    
    patched = fudge.patch_object(holder, "exc", Freddie())
    eq_(type(holder.exc), type(Freddie()))
    patched.restore()
    eq_(type(holder.exc), type(Exception()))
    
def test_patch_path():
    from os.path import join as orig_join
    patched = fudge.patch_object("os.path", "join", Freddie())
    import os.path
    eq_(type(os.path.join), type(Freddie()))
    patched.restore()
    eq_(type(os.path.join), type(orig_join))