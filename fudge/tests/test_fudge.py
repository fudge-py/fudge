
import thread
import unittest
import fudge
from nose.tools import eq_, raises
from fudge import ExpectedCall, Call, CallStack, FakeDeclarationError

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
        self.reg.clear_calls()
        self.reg.expect_call(ExpectedCall(self.fake, 'nothing'))
        self.reg.verify()
        
    def test_start_resets_calls(self):
        exp = ExpectedCall(self.fake, 'callMe')
        self.reg.expect_call(exp)
        exp()
        eq_(exp.was_called, True)
        
        self.reg.clear_calls()
        eq_(exp.was_called, False, "call was not reset by start()")
    
    def test_stop_resets_calls(self):
        exp = ExpectedCall(self.fake, 'callMe')
        exp()
        eq_(exp.was_called, True)
        eq_(len(self.reg.get_expected_calls()), 1)
        
        self.reg.verify()
        eq_(exp.was_called, False, "call was not reset by stop()")
        eq_(len(self.reg.get_expected_calls()), 1, "stop() should not reset expectations")
    
    def test_global_stop(self):
        exp = ExpectedCall(self.fake, 'callMe')
        exp()
        eq_(exp.was_called, True)
        eq_(len(self.reg.get_expected_calls()), 1)
        
        fudge.verify()
        
        eq_(exp.was_called, False, "call was not reset by stop()")
        eq_(len(self.reg.get_expected_calls()), 1, "stop() should not reset expectations")
    
    def test_global_clear_expectations(self):
        exp = ExpectedCall(self.fake, 'callMe')
        exp()
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
                    fudge.clear_calls()
                    # registered first time on __init__ :
                    exp = ExpectedCall(self.fake, 'callMe')
                    exp() 
                    reg.expect_call(exp)
                    reg.expect_call(exp)
                    reg.expect_call(exp)
                    eq_(len(reg.get_expected_calls()), 4)
                    fudge.verify()
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
    
    def test_attributes(self):
        my_obj = fudge.Fake().has_attr(vice='versa', beach='playa')
        eq_(my_obj.vice, 'versa')
        eq_(my_obj.beach, 'playa')
    
    def test_attributes_can_replace_internals(self):
        my_obj = fudge.Fake().has_attr(provides='hijacked')
        eq_(my_obj.provides, 'hijacked')

class TestFakeExpectations(unittest.TestCase):
    
    def setUp(self):
        self.fake = fudge.Fake()
    
    def tearDown(self):
        fudge.clear_expectations()
    
    @raises(AssertionError)
    def test_nocall(self):
        exp = self.fake.expects('something')
        fudge.verify()
    
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
        self.fake = fudge.Fake('SMTP')
    
    def test_repr(self):
        s = Call(self.fake)
        eq_(repr(s), "fake:SMTP()")
    
    def test_repr_with_args(self):
        s = Call(self.fake)
        s.expected_args = [1,"bad"]
        eq_(repr(s), "fake:SMTP(1, 'bad')")
    
    def test_repr_with_kwargs(self):
        s = Call(self.fake)
        s.expected_args = [1,"bad"]
        s.expected_kwargs = {'baz':'borzo'}
        eq_(repr(s), "fake:SMTP(1, 'bad', baz='borzo')")
    
    def test_named_repr_with_args(self):
        s = Call(self.fake, call_name='connect')
        s.expected_args = [1,"bad"]
        eq_(repr(s), "fake:SMTP.connect(1, 'bad')")
    
    def test_named_repr_with_index(self):
        s = Call(self.fake, call_name='connect')
        s.expected_args = [1,"bad"]
        s.index = 0
        eq_(repr(s), "fake:SMTP.connect(1, 'bad')[0]")
        s.index = 1
        eq_(repr(s), "fake:SMTP.connect(1, 'bad')[1]")
        

class TestCallStack(unittest.TestCase):
    
    def setUp(self):
        self.fake = fudge.Fake('SMTP')
    
    def test_calls(self):
        call_stack = CallStack(self.fake)
        
        c = Call(self.fake)
        c.return_val = 1
        call_stack.add_call(c)
        
        c = Call(self.fake)
        c.return_val = 2
        call_stack.add_call(c)
        
        eq_(call_stack(), 1)
        eq_(call_stack(), 2)
    
    @raises(AssertionError)
    def test_no_calls(self):
        call_stack = CallStack(self.fake)
        call_stack()
    
    @raises(AssertionError)
    def test_end_of_calls(self):
        call_stack = CallStack(self.fake)
        
        c = Call(self.fake)
        c.return_val = 1
        call_stack.add_call(c)
        
        eq_(call_stack(), 1)
        call_stack()
    
    def test_get_call_object(self):
        call_stack = CallStack(self.fake)
        
        c = Call(self.fake)
        call_stack.add_call(c)
        
        assert call_stack.get_call_object() is c
        
        d = Call(self.fake)
        call_stack.add_call(d)
        
        assert call_stack.get_call_object() is d
    
    def test_with_initial_calls(self):
        c = Call(self.fake)
        c.return_val = 1
        call_stack = CallStack(self.fake, initial_calls=[c])
        
        eq_(call_stack(), 1)
    
    def test_reset(self):
        call_stack = CallStack(self.fake)
        
        c = Call(self.fake)
        c.return_val = 1
        call_stack.add_call(c)
        
        c = Call(self.fake)
        c.return_val = 2
        call_stack.add_call(c)
        
        eq_(call_stack(), 1)
        eq_(call_stack(), 2)
        
        call_stack.reset()
        
        eq_(call_stack(), 1)
        eq_(call_stack(), 2)
        
class TestFakeCallables(unittest.TestCase):
    
    def tearDown(self):
        fudge.clear_expectations()
    
    @raises(RuntimeError)
    def test_not_callable_by_default(self):
        self.fake = fudge.Fake()
        self.fake()
    
    def test_callable(self):
        self.fake = fudge.Fake(callable=True)
        self.fake() # allow the call
        fudge.verify() # no error
    
    @raises(AttributeError)
    def test_cannot_stub_any_call_by_default(self):
        self.fake.Anything() # must define this first
    
    def test_can_stub_any_call(self):
        self.fake = fudge.Fake(allows_any_call=True)
        self.fake.Anything()
        self.fake.something_else(blazz='Blaz', kudoz='Klazzed')
        self.fake()
    
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
    
    def test_fake_can_sabotage_itself(self):
        # I'm not sure if there should be a warning 
        # for this but it seems that it should be 
        # possible for maximum flexibility:
        
        # replace Fake.with_args()
        self.fake = fudge.Fake().provides("with_args").returns(1)
        eq_(self.fake.with_args(), 1)
    
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
        
        def something():
            return "hijacked"
            
        self.fake = fudge.Fake().provides("something").calls(something)
        eq_(self.fake.something(), "hijacked")
        
class TestFakeTimesCalled(unittest.TestCase):
    
    def tearDown(self):
        fudge.clear_expectations()
        
    def test_when_provided(self):
        self.fake = fudge.Fake().provides("something").times_called(2)
        # this should not raise an error because the call was provided not expected
        fudge.verify()
        
    @raises(AssertionError)
    def test_when_provided_raises_on_too_many_calls(self):
        self.fake = fudge.Fake().provides("something").times_called(2)
        self.fake.something()
        self.fake.something()
        self.fake.something() # too many
    
    @raises(AssertionError)
    def test_when_expected(self):
        self.fake = fudge.Fake().expects("something").times_called(2)
        self.fake.something()
        fudge.verify()
    
    @raises(AssertionError)
    def test_when_expected_raises_on_too_many_calls(self):
        self.fake = fudge.Fake().expects("something").times_called(2)
        self.fake.something()
        self.fake.something()
        self.fake.something() # too many
        fudge.verify()
        
    @raises(AssertionError)
    def test_expected_callable(self):
        login = fudge.Fake('login',expect_call=True).times_called(2)
        login()
        fudge.verify()
        
    def test_callable_ok(self):
        self.fake = fudge.Fake(callable=True).times_called(2)
        self.fake()
        self.fake()
        fudge.verify()
        
    def test_when_provided_ok(self):
        self.fake = fudge.Fake().provides("something").times_called(2)
        self.fake.something()
        self.fake.something()
        fudge.verify()
        
    def test_when_expected_ok(self):
        self.fake = fudge.Fake().expects("something").times_called(2)
        self.fake.something()
        self.fake.something()
        fudge.verify()
    
    @raises(FakeDeclarationError)
    def test_next_call_then_times_called_is_error(self):
        self.fake = fudge.Fake().expects("hi").returns("goodday").next_call().times_called(4)
        self.fake.hi()
        self.fake.hi()
        fudge.verify()
    
    @raises(FakeDeclarationError)
    def test_times_called_then_next_call_is_error(self):
        self.fake = fudge.Fake().expects("hi").times_called(4).next_call()
        self.fake.hi()
        self.fake.hi()
        fudge.verify()

class TestStackedCallables(unittest.TestCase):
            
    def test_stacked_returns(self):
        fake = fudge.Fake().provides("something")
        fake = fake.returns(1)
        fake = fake.next_call()
        fake = fake.returns(2)
        fake = fake.next_call()
        fake = fake.returns(3)
        
        eq_(fake.something(), 1)
        eq_(fake.something(), 2)
        eq_(fake.something(), 3)
    
    @raises(AssertionError)
    def test_stacked_calls_are_finite(self):
        self.fake = fudge.Fake().provides("something")
        self.fake = self.fake.returns(1)
        self.fake = self.fake.next_call()
        self.fake = self.fake.returns(2)
        
        eq_(self.fake.something(), 1)
        eq_(self.fake.something(), 2)
        self.fake.something()
        
    def test_stack_is_reset_when_name_changes(self):
        self.fake = fudge.Fake().provides("something")
        self.fake = self.fake.returns(1)
        self.fake = self.fake.next_call()
        self.fake = self.fake.returns(2)
        self.fake = self.fake.provides("other")
        self.fake = self.fake.returns(3)
        
        eq_(self.fake.something(), 1)
        eq_(self.fake.something(), 2)
        eq_(self.fake.other(), 3)
        eq_(self.fake.other(), 3)
        eq_(self.fake.other(), 3)
        eq_(self.fake.other(), 3)
        eq_(self.fake.other(), 3)
        
    def test_next_call_with_multiple_returns(self):
        self.fake = fudge.Fake().provides("something")
        self.fake = self.fake.returns(1)
        self.fake = self.fake.next_call()
        self.fake = self.fake.returns(2)
        self.fake = self.fake.provides("other")
        self.fake = self.fake.returns(3)
        self.fake = self.fake.next_call()
        self.fake = self.fake.returns(4)
        
        eq_(self.fake.something(), 1)
        eq_(self.fake.something(), 2)
        eq_(self.fake.other(), 3)
        eq_(self.fake.other(), 4)
        
    def test_stacked_calls_do_not_collide(self):
        self.fake = fudge.Fake().provides("something")
        self.fake = self.fake.returns(1)
        self.fake = self.fake.next_call()
        self.fake = self.fake.returns(2)
        self.fake = self.fake.provides("other")
        self.fake = self.fake.returns(3)
        self.fake = self.fake.next_call()
        self.fake = self.fake.returns(4)
        
        eq_(self.fake.something(), 1)
        eq_(self.fake.other(), 3)
        eq_(self.fake.something(), 2)
        eq_(self.fake.other(), 4)
    
    def test_returns_are_infinite(self):
        self.fake = fudge.Fake().provides("something").returns(1)
        
        eq_(self.fake.something(), 1)
        eq_(self.fake.something(), 1)
        eq_(self.fake.something(), 1)
        eq_(self.fake.something(), 1)
        eq_(self.fake.something(), 1)
        eq_(self.fake.something(), 1)
        eq_(self.fake.something(), 1)
        eq_(self.fake.something(), 1)
        
    def test_stacked_does_not_copy_expectations(self):
        
        fake = fudge.Fake().expects("add")
        fake = fake.with_args(1,2).returns(3)
        
        fake = fake.next_call()
        fake = fake.returns(-1)
        
        eq_(fake.add(1,2), 3)
        eq_(fake.add(), -1)
        
    def test_stacked_calls_are_in_registry(self):
        fake = fudge.Fake().expects("count").with_args(1)
        fake = fake.next_call().with_args(2)
        fake = fake.next_call().with_args(3)
        fake = fake.next_call().with_args(4)
        
        # hmm
        call_stack = fake._declared_calls[fake._last_declared_call_name]
        calls = [c for c in call_stack]
        assert calls[0] in fudge.registry
        assert calls[1] in fudge.registry
        assert calls[2] in fudge.registry
        assert calls[3] in fudge.registry
        
    def test_stacked_calls_are_indexed(self):
        fake = fudge.Fake().expects("count").with_args(1)
        fake = fake.next_call().with_args(2)
        fake = fake.next_call().with_args(3)
        fake = fake.next_call().with_args(4)
        
        # hmm
        call_stack = fake._declared_calls[fake._last_declared_call_name]
        calls = [c for c in call_stack]
        eq_(calls[0].index, 0)
        eq_(calls[1].index, 1)
        eq_(calls[2].index, 2)
        eq_(calls[3].index, 3)
    
    def test_start_stop_resets_stack(self):
        fudge.clear_expectations()
        fake = fudge.Fake().provides("something")
        fake = fake.returns(1)
        fake = fake.next_call()
        fake = fake.returns(2)
        
        eq_(fake.something(), 1)
        eq_(fake.something(), 2)
        
        fudge.clear_calls()
        
        eq_(fake.something(), 1)
        eq_(fake.something(), 2)
        
        fudge.verify()
        
        eq_(fake.something(), 1)
        eq_(fake.something(), 2)
        
        
        