import inspect
import unittest

import fudge


class Freddie(object):
    pass


class PatcherTest(unittest.TestCase):
    def test_patch_obj(self):
        class holder:
            exc = Exception()

        patched = fudge.patch_object(holder, "exc", Freddie())
        self.assertEqual(type(holder.exc), type(Freddie()))
        patched.restore()
        self.assertEqual(type(holder.exc), type(Exception()))


    def test_patch_path(self):
        from os.path import join as orig_join
        patched = fudge.patch_object("os.path", "join", Freddie())
        import os.path
        self.assertEqual(type(os.path.join), type(Freddie()))
        patched.restore()
        self.assertEqual(type(os.path.join), type(orig_join))


    def test_patch_builtin(self):
        import datetime
        orig_datetime = datetime.datetime
        now = datetime.datetime(2010, 11, 4, 8, 19, 11, 28778)
        fake = fudge.Fake('now').is_callable().returns(now)
        patched = fudge.patch_object(datetime.datetime, 'now', fake)
        try:
            self.assertEqual(datetime.datetime.now(), now)
        finally:
            patched.restore()
        self.assertEqual(datetime.datetime.now, orig_datetime.now)


    def test_patch_long_path(self):
        import fudge.tests.support._for_patch
        orig = fudge.tests.support._for_patch.some_object.inner
        long_path = 'fudge.tests.support._for_patch.some_object.inner'
        with fudge.patch(long_path) as fake:
            assert isinstance(fake, fudge.Fake)
        self.assertEqual(fudge.tests.support._for_patch.some_object.inner, orig)


    def test_patch_non_existant_path(self):
        with self.assertRaises(ImportError):
            with fudge.patch('__not_a_real_import_path.nested.one.two.three') as fake:
                pass


    def test_patch_non_existant_attribute(self):
        with self.assertRaises(AttributeError):
            with fudge.patch('fudge.tests.support._for_patch.does.not.exist') as fake:
                pass

    def test_patch_builtin_as_string(self):
        import datetime
        orig_datetime = datetime.datetime
        now = datetime.datetime(2006, 11, 4, 8, 19, 11, 28778)
        fake_dt = fudge.Fake('datetime').provides('now').returns(now)
        patched = fudge.patch_object('datetime', 'datetime', fake_dt)
        try:
            # timetuple is a workaround for strange Jython behavior!
            self.assertEqual(datetime.datetime.now().timetuple(), now.timetuple())
        finally:
            patched.restore()
        self.assertEqual(datetime.datetime.now, orig_datetime.now)


    def test_decorator_on_def(self):
        class holder:
            test_called = False
            exc = Exception()

        @fudge.with_patched_object(holder, "exc", Freddie())
        def some_test():
            holder.test_called = True
            self.assertEqual(type(holder.exc), type(Freddie()))

        self.assertEqual(some_test.__name__, 'some_test')
        some_test()
        self.assertEqual(holder.test_called, True)
        self.assertEqual(type(holder.exc), type(Exception()))


    def test_decorator_on_class(self):
        class holder:
            test_called = False
            exc = Exception()

        class SomeTest(object):

            @fudge.with_patched_object(holder, "exc", Freddie())
            def some_test(self):
                holder.test_called = True
                assert isinstance(holder.exc, Freddie)

        self.assertEqual(SomeTest.some_test.__name__, 'some_test')
        s = SomeTest()
        s.some_test()
        self.assertEqual(holder.test_called, True)
        self.assertEqual(type(holder.exc), type(Exception()))


    def test_patched_context(self):
        if not hasattr(fudge, "patched_context"):
            raise unittest.SkipTest("Cannot test with patched_context() because not in 2.5")

        class Boo:
            fargo = "is over there"

        ctx = fudge.patched_context(Boo, 'fargo', 'is right here')
        # simulate with fudge.patched_context():
        ctx.__enter__()
        self.assertEqual(Boo.fargo, "is right here")
        ctx.__exit__(None, None, None)
        self.assertEqual(Boo.fargo, "is over there")


    def test_base_class_attribute(self):
        class Base(object):
            foo = 'bar'
        class Main(Base):
            pass
        fake = fudge.Fake()
        p = fudge.patch_object(Main, 'foo', fake)
        self.assertEqual(Main.foo, fake)
        self.assertEqual(Base.foo, 'bar')
        p.restore()
        self.assertEqual(Main.foo, 'bar')
        assert 'foo' not in Main.__dict__, ('Main.foo was not restored correctly')


    def test_bound_methods(self):
        class Klass(object):
            def method(self):
                return 'foozilate'
        instance = Klass()
        fake = fudge.Fake()
        p = fudge.patch_object(instance, 'method', fake)
        self.assertEqual(instance.method, fake)
        p.restore()
        self.assertEqual(instance.method(), Klass().method())
        assert inspect.ismethod(instance.method)
        assert 'method' not in instance.__dict__, (
                                'instance.method was not restored correctly')


    def test_staticmethod_descriptor(self):
        class Klass(object):
            @staticmethod
            def static():
                return 'OK'
        fake = fudge.Fake()
        p = fudge.patch_object(Klass, 'static', fake)
        self.assertEqual(Klass.static, fake)
        p.restore()
        self.assertEqual(Klass.static(), 'OK')


    def test_property(self):
        class Klass(object):
            @property
            def prop(self):
                return 'OK'
        exact_prop = Klass.prop
        instance = Klass()
        fake = fudge.Fake()
        p = fudge.patch_object(instance, 'prop', fake)
        self.assertEqual(instance.prop, fake)
        p.restore()
        self.assertEqual(instance.prop, 'OK')
        self.assertEqual(Klass.prop, exact_prop)


    def test_inherited_property(self):
        class SubKlass(object):
            @property
            def prop(self):
                return 'OK'
        class Klass(SubKlass):
            pass
        exact_prop = SubKlass.prop
        instance = Klass()
        fake = fudge.Fake()
        p = fudge.patch_object(instance, 'prop', fake)
        self.assertEqual(instance.prop, fake)
        p.restore()
        self.assertEqual(instance.prop, 'OK')
        assert 'prop' not in Klass.__dict__, (
                                    'Klass.prop was not restored properly')
        self.assertEqual(SubKlass.prop, exact_prop)


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
            self.assertEqual(copy, shutil.copy)

        self.assertEqual(some_test.__name__, 'some_test')
        some_test()
        self.assertEqual(holder.test_called, True)
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
                assert copy == shutil.copy

        self.assertEqual(MyTest.some_test.__name__, 'some_test')
        m = MyTest()
        m.some_test()
        self.assertEqual(holder.test_called, True)
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
            self.assertEqual(copy, shutil.copy)
            self.assertEqual(remove, os.remove)

        self.assertEqual(some_test.__name__, 'some_test')
        some_test()
        self.assertEqual(holder.test_called, True)
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
                self.assertEqual(copy, shutil.copy)
                holder.test_called = True

        run_test()
        self.assertEqual(holder.test_called, True)
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
                self.assertEqual(copy, shutil.copy)
                self.assertEqual(remove, os.remove)
                holder.test_called = True

        run_test()
        self.assertEqual(holder.test_called, True)
        import shutil
        assert not isinstance(shutil.copy, fudge.Fake)
        import os
        assert not isinstance(os.remove, fudge.Fake)

    def test_class_method_path(self):
        class ctx:
            sendmail = None

        @fudge.patch('smtplib.SMTP.sendmail')
        def test(fake_sendmail):
            import smtplib
            s = smtplib.SMTP()
            ctx.sendmail = s.sendmail

        test()
        assert isinstance(ctx.sendmail, fudge.Fake)
        import smtplib
        s = smtplib.SMTP()
        assert not isinstance(s.sendmail, fudge.Fake)
