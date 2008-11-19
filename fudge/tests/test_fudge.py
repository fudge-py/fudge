
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
    
    def tearDown(self):
        # in case of error, clear this out:
        self.reg.finish()
    
    @raises(AssertionError)
    def test_expected_calls(self):
        self.reg.expect_call(ExpectedCall(self.fake, 'nothing'))
        self.reg.finish()
        
    @raises(AssertionError)
    def test_more_expected_calls(self):
        exp = ExpectedCall(self.fake, 'elsewhere')
        self.reg.expect_call(exp)
        exp()
        self.reg.expect_call(ExpectedCall(self.fake, 'nothing'))
        self.reg.finish()
    
    def test_finish(self):
        exp = ExpectedCall(self.fake, 'callMe')
        self.reg.expect_call(exp)
        exp()
        eq_(exp.was_called, True)
        eq_(len(self.reg.get_expected_calls()), 1)
        self.reg.finish()
        eq_(exp.was_called, False, "expected call was not reset by finish()")
        eq_(len(self.reg.get_expected_calls()), 0)
    
    def test_global_finish(self):
        exp = ExpectedCall(self.fake, 'callMe')
        exp()
        self.reg.expect_call(exp)
        eq_(len(self.reg.get_expected_calls()), 1)
        fudge.finish()
        eq_(len(self.reg.get_expected_calls()), 0)
    
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
                    exp = ExpectedCall(self.fake, 'callMe')
                    exp()
                    reg.expect_call(exp)
                    reg.expect_call(exp)
                    reg.expect_call(exp)
                    reg.expect_call(exp)
                    eq_(len(reg.get_expected_calls()), 4)
                    fudge.finish()
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
        
        