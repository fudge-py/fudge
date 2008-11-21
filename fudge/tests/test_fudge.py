
import thread
import unittest
import fudge
from nose.tools import eq_, raises
from fudge import ExpectedCall

class TestExpectedCall(unittest.TestCase):
    
    def setUp(self):
        self.fake = fudge.Fake()
    
    @raises(AssertionError)
    def test_nocall(self):
        exp = ExpectedCall(self.fake, 'something')
        exp.assert_called()
    
    @raises(AssertionError)
    def test_wrong_args(self):
        exp = ExpectedCall(self.fake, 'theCall')
        exp.expected_args = [1, "ho ho ho ho ho ho ho, it's Santa", {'ditto':False}]
        exp()
        
    @raises(AssertionError)
    def test_wrong_kwargs(self):
        exp = ExpectedCall(self.fake, 'other')
        exp.expected_kwargs = dict(one="twozy", items=[1,2,3,4])
        exp(nice="NOT NICE")
        
    @raises(AssertionError)
    def test_arg_count(self):
        exp = ExpectedCall(self.fake, 'one')
        exp.expected_arg_count = 3
        exp('no', 'maybe')
        
    @raises(AssertionError)
    def test_kwarg_count(self):
        exp = ExpectedCall(self.fake, '__init__')
        exp.expected_kwarg_count = 2
        exp(maybe="yes, maybe")

class TestRegistry(unittest.TestCase):
    
    def setUp(self):
        self.fake = fudge.Fake()
        self.reg = fudge.registry
        # in case of error, clear out everything:
        self.reg.clear_all()
    
    def tearDown(self):
        pass
    
    @raises(AssertionError)
    def test_expected_call_not_called(self):
        self.reg.start()
        self.reg.expect_call(ExpectedCall(self.fake, 'nothing'))
        self.reg.stop()
        
    def test_start_resets_calls(self):
        exp = ExpectedCall(self.fake, 'callMe')
        self.reg.expect_call(exp)
        exp()
        eq_(exp.was_called, True)
        
        self.reg.start()
        eq_(exp.was_called, False, "call was not reset by start()")
    
    def test_stop_resets_calls(self):
        exp = ExpectedCall(self.fake, 'callMe')
        self.reg.expect_call(exp)
        exp()
        eq_(exp.was_called, True)
        eq_(len(self.reg.get_expected_calls()), 1)
        
        self.reg.stop()
        eq_(exp.was_called, False, "call was not reset by stop()")
        eq_(len(self.reg.get_expected_calls()), 1, "stop() should not reset expectations")
    
    def test_global_stop(self):
        exp = ExpectedCall(self.fake, 'callMe')
        exp()
        self.reg.expect_call(exp)
        eq_(exp.was_called, True)
        eq_(len(self.reg.get_expected_calls()), 1)
        
        fudge.stop()
        
        eq_(exp.was_called, False, "call was not reset by stop()")
        eq_(len(self.reg.get_expected_calls()), 1, "stop() should not reset expectations")
    
    def test_global_clear_expectations(self):
        exp = ExpectedCall(self.fake, 'callMe')
        exp()
        self.reg.expect_call(exp)
        eq_(len(self.reg.get_expected_calls()), 1)
        
        fudge.clear_expectations()
        
        eq_(len(self.reg.get_expected_calls()), 0, 
            "clear_expectations() should reset expectations")
    
    def test_multithreading(self):
        
        reg = fudge.registry
        
        class thread_run:
            waiting = 5
            errors = []
        
        # while this barely catches collisions
        # it ensures that each thread can use the registry ok
        def registry(num):
            try:
                try:
                    fudge.start()
                    exp = ExpectedCall(self.fake, 'callMe')
                    exp()
                    reg.expect_call(exp)
                    reg.expect_call(exp)
                    reg.expect_call(exp)
                    reg.expect_call(exp)
                    eq_(len(reg.get_expected_calls()), 4)
                    fudge.stop()
                    fudge.clear_expectations()
                except Exception, er:
                    thread_run.errors.append(er)
                    raise
            finally:
                thread_run.waiting -= 1
                
        thread.start_new_thread(registry, (1,))
        thread.start_new_thread(registry, (2,))
        thread.start_new_thread(registry, (3,))
        thread.start_new_thread(registry, (4,))
        thread.start_new_thread(registry, (5,))

        count = 0
        while thread_run.waiting > 0:
            count += 1
            import time
            time.sleep(0.25)
            if count == 60:
                raise RuntimeError("timed out waiting for thread")
        if len(thread_run.errors):
            raise RuntimeError(
                "Error(s) in thread: %s" % ["%s: %s" % (
                    e.__class__.__name__, e) for e in thread_run.errors])

def test_decorator_on_def():
    class holder:
        test_called = False
    
    bobby = fudge.Fake()
    bobby.expects("suzie_called")
    
    @raises(AssertionError)
    @fudge.with_fakes
    def some_test():
        holder.test_called = True
    
    eq_(some_test.__name__, 'some_test')
    some_test()
    
    eq_(holder.test_called, True)

# for a test below
_some_fake = fudge.Fake()

class TestFake(unittest.TestCase):
    
    def test_guess_name(self):
        my_obj = fudge.Fake()
        eq_(repr(my_obj), "fake:my_obj")
        
    def test_guess_name_globals(self):
        # eq_(repr(_some_fake), "fake:_some_fake")
        eq_(repr(_some_fake), "fake:unnamed")
        
    def test_guess_name_deref(self):
        my_obj = 44
        my_obj = fudge.Fake()
        # eq_(repr(my_obj), "fake:my_obj")
        eq_(repr(my_obj), "fake:unnamed")
        