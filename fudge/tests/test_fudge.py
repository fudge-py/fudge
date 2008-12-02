
import thread
import unittest
import fudge
from nose.tools import eq_, raises
from fudge import ExpectedCall, Call

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
        eq_(repr(_some_fake), "fake:_some_fake")
        
    def test_guess_name_deref(self):
        my_obj = 44
        my_obj = fudge.Fake()
        eq_(repr(my_obj), "fake:my_obj")

class TestFakeExpectations(unittest.TestCase):
    
    def setUp(self):
        self.fake = fudge.Fake()
    
    def tearDown(self):
        fudge.clear_expectations()
    
    @raises(AssertionError)
    def test_nocall(self):
        exp = self.fake.expects('something')
        fudge.stop()
    
    @raises(AssertionError)
    def test_wrong_args(self):
        exp = self.fake.expects('theCall').with_args(
                        1, 
                        "ho ho ho ho ho ho ho, it's Santa", 
                        {'ditto':False})
        exp.theCall()
        
    @raises(AssertionError)
    def test_wrong_kwargs(self):
        exp = self.fake.expects('other').with_args(one="twozy", items=[1,2,3,4])
        exp.other(nice="NOT NICE")
        
    @raises(AssertionError)
    def test_arg_count(self):
        exp = self.fake.expects('one').with_arg_count(3)
        exp.one('no', 'maybe')
        
    @raises(AssertionError)
    def test_kwarg_count(self):
        exp = self.fake.expects('__init__').with_kwarg_count(2)
        exp(maybe="yes, maybe")

class TestCall(unittest.TestCase):
    
    def setUp(self):
        self.fake = fudge.Fake()
    
    def test_repr(self):
        s = Call(self.fake)
        eq_(repr(s), "Fake()")
    
    def test_repr_with_args(self):
        s = Call(self.fake)
        s.expected_args = [1,"bad"]
        eq_(repr(s), "Fake(1, 'bad')")
        
class TestFakeCallables(unittest.TestCase):
    
    def setUp(self):
        self.fake = fudge.Fake()
    
    def tearDown(self):
        fudge.clear_expectations()
    
    def test_callable(self):
        self.fake = fudge.Fake(callable=True)
        self.fake() # allow the call
        fudge.stop() # no error
    
    @raises(AttributeError)
    def test_cannot_stub_any_call_by_default(self):
        self.fake.Anything() # must define this first
    
    def test_can_stub_any_call(self):
        self.fake = fudge.Fake(allows_any_call=True)
        self.fake.Anything()
        self.fake.something_else(blazz='Blaz', kudoz='Klazzed')
    
    @raises(AssertionError)
    def test_stub_with_args(self):
        self.fake = fudge.Fake(callable=True).with_args(1,2)
        self.fake(1)
    
    @raises(AssertionError)
    def test_stub_with_arg_count(self):
        self.fake = fudge.Fake(callable=True).with_arg_count(3)
        self.fake('bah')
    
    @raises(AssertionError)
    def test_stub_with_kwarg_count(self):
        self.fake = fudge.Fake(callable=True).with_kwarg_count(3)
        self.fake(two=1)
    
    def test_stub_with_provides(self):
        self.fake = fudge.Fake().provides("something")
        self.fake.something()
    
    @raises(AssertionError)
    def test_stub_with_provides_and_args(self):
        self.fake = fudge.Fake().provides("something").with_args(1,2)
        self.fake.something()
    
    def test_stub_is_not_registered(self):
        self.fake = fudge.Fake().provides("something")
        exp = self.fake._get_current_call()
        eq_(exp.call_name, "something")
        assert exp not in fudge.registry
    
    def test_replace_call(self):
        class holder:
            called = False
            
        def something():
            holder.called = True
            return "hijacked"
            
        self.fake = fudge.Fake().provides("something").calls(something)
        eq_(self.fake.something(), "hijacked")
        