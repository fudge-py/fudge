from __future__ import with_statement
import unittest

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


def test_patch_builtin():
    import datetime
    orig_datetime = datetime.datetime
    now = datetime.datetime(2010, 11, 4, 8, 19, 11, 28778)
    fake = fudge.Fake('now', callable=True).returns(now)
    patched = fudge.patch_object(datetime.datetime, 'now', fake)
    try:
        eq_(datetime.datetime.now(), now)
    finally:
        patched.restore()
    eq_(datetime.datetime.now, orig_datetime.now)


def test_patch_builtin_as_string():
    import datetime
    orig_datetime = datetime.datetime
    now = datetime.datetime(2006, 11, 4, 8, 19, 11, 28778)
    fake_dt = fudge.Fake('datetime').provides('now').returns(now)
    patched = fudge.patch_object('datetime', 'datetime', fake_dt)
    try:
        # timetuple is a workaround for strange Jython behavior!
        eq_(datetime.datetime.now().timetuple(), now.timetuple())
    finally:
        patched.restore()
    eq_(datetime.datetime.now, orig_datetime.now)


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


class TestPatch(unittest.TestCase):

    def setUp(self):
        fudge.clear_expectations()

    def test_decorator_on_def(self):

        class holder:
            test_called = False
        
        @fudge.patch('shutil.copy')
        def some_test(copy):
            import shutil
            holder.test_called = True
            assert isinstance(copy, fudge.Fake)
            eq_(copy, shutil.copy)
    
        eq_(some_test.__name__, 'some_test')
        some_test()
        eq_(holder.test_called, True)
        import shutil
        assert not isinstance(shutil.copy, fudge.Fake)


    def test_decorator_on_class(self):

        class holder:
            test_called = False
    
        class MyTest(object):

            @fudge.patch('shutil.copy')
            def some_test(self, copy):
                import shutil
                holder.test_called = True
                assert isinstance(copy, fudge.Fake)
                eq_(copy, shutil.copy)
    
        eq_(MyTest.some_test.__name__, 'some_test')
        m = MyTest()
        m.some_test()
        eq_(holder.test_called, True)
        import shutil
        assert not isinstance(shutil.copy, fudge.Fake)

    def test_patch_many(self):

        class holder:
            test_called = False
        
        @fudge.patch('shutil.copy',
                     'os.remove')
        def some_test(copy, remove):
            import shutil
            import os
            holder.test_called = True
            assert isinstance(copy, fudge.Fake)
            assert isinstance(remove, fudge.Fake)
            eq_(copy, shutil.copy)
            eq_(remove, os.remove)
    
        eq_(some_test.__name__, 'some_test')
        some_test()
        eq_(holder.test_called, True)
        import shutil
        assert not isinstance(shutil.copy, fudge.Fake)
        import os
        assert not isinstance(os.remove, fudge.Fake)

    def test_with_patch(self):

        class holder:
            test_called = False

        def run_test():
            with fudge.patch('shutil.copy') as copy:
                import shutil
                assert isinstance(copy, fudge.Fake)
                eq_(copy, shutil.copy)
                holder.test_called = True
        
        run_test()
        eq_(holder.test_called, True)
        import shutil
        assert not isinstance(shutil.copy, fudge.Fake)

    def test_with_multiple_patches(self):

        class holder:
            test_called = False

        def run_test():
            with fudge.patch('shutil.copy', 'os.remove') as fakes:
                copy, remove = fakes
                import shutil
                import os
                assert isinstance(copy, fudge.Fake)
                assert isinstance(remove, fudge.Fake)
                eq_(copy, shutil.copy)
                eq_(remove, os.remove)
                holder.test_called = True
        
        run_test()
        eq_(holder.test_called, True)
        import shutil
        assert not isinstance(shutil.copy, fudge.Fake)
        import os
        assert not isinstance(os.remove, fudge.Fake)
