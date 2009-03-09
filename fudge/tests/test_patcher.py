
from nose.exc import SkipTest
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

def test_decorator_on_def():
    class holder:
        test_called = False
        exc = Exception()
        
    @fudge.with_patched_object(holder, "exc", Freddie())
    def some_test():
        holder.test_called = True
        eq_(type(holder.exc), type(Freddie()))
    
    eq_(some_test.__name__, 'some_test')
    some_test()
    eq_(holder.test_called, True)
    eq_(type(holder.exc), type(Exception()))

def test_decorator_on_class():
    class holder:
        test_called = False
        exc = Exception()
    
    class SomeTest(object):
        
        @fudge.with_patched_object(holder, "exc", Freddie())
        def some_test(self):
            holder.test_called = True
            eq_(type(holder.exc), type(Freddie()))
    
    eq_(SomeTest.some_test.__name__, 'some_test')
    s = SomeTest()
    s.some_test()
    eq_(holder.test_called, True)
    eq_(type(holder.exc), type(Exception()))

def test_patched_context():
    if not hasattr(fudge, "patched_context"):
        raise SkipTest("Cannot test with patched_context() because not in 2.5")
    
    class Boo:
        fargo = "is over there"
    
    ctx = fudge.patched_context(Boo, 'fargo', 'is right here')
    # simulate with fudge.patched_context():
    ctx.__enter__()
    eq_(Boo.fargo, "is right here")
    ctx.__exit__(None, None, None)
    eq_(Boo.fargo, "is over there")
    