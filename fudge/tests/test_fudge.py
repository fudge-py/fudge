
import unittest
import fudge
from nose.tools import eq_, raises
from fudge import (
    Fake, Registry, ExpectedCall, ExpectedCallOrder, Call, CallStack, FakeDeclarationError)

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
    
    def test_repr_shortens_long_values(self):
        fake = Fake("widget").provides("set_bits").with_args(
            "12345678910111213141516171819202122232425262728293031"
        )
        try:
            fake.set_bits()
        except AssertionError, exc:
            eq_(str(exc),
            "fake:widget.set_bits('123456789101112131415161718192021222324252627...') "
            "was called unexpectedly with args ()")
        else:
            raise RuntimeError("expected AssertionError")

class TestLongArgValues(unittest.TestCase):
    
    def test_arg_diffs_are_not_shortened(self):
        fake = Fake("widget").provides("set_bits").with_args(
            "12345678910111213141516171819202122232425262728293031"
        )
        try:
            # this should not be shortened but the above arg spec should:
            fake.set_bits("99999999999999999999999999999999999999999999999999999999")
        except AssertionError, exc:
            eq_(str(exc),
            "fake:widget.set_bits('123456789101112131415161718192021222324252627...') "
            "was called unexpectedly with args "
            "('99999999999999999999999999999999999999999999999999999999')")
        else:
            raise RuntimeError("expected AssertionError")
    
    def test_kwarg_diffs_are_not_shortened(self):
        fake = Fake("widget").provides("set_bits").with_args(
            newbits="12345678910111213141516171819202122232425262728293031"
        )
        try:
            # this should not be shortened but the above arg spec should:
            fake.set_bits(newbits="99999999999999999999999999999999999999999999999999999999")
        except AssertionError, exc:
            eq_(str(exc),
            "fake:widget.set_bits(newbits='123456789101112131415161718192021222324252627...') "
            "was called unexpectedly with args "
            "(newbits='99999999999999999999999999999999999999999999999999999999')")
        else:
            raise RuntimeError("expected AssertionError")

class TestReturnsFake(unittest.TestCase):
    
    def test_returns_fake_has_name(self):
        f = Fake().provides("get_widget").returns_fake()
        eq_(f._name, "get_widget")

class TestArguments(unittest.TestCase):
    
    def setUp(self):
        self.fake = fudge.Fake()
    
    def tearDown(self):
        fudge.clear_expectations()
    
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
    
    @raises(FakeDeclarationError)
    def test_with_args_requires_a_method(self):
        self.fake.with_args('something')
    
    @raises(AssertionError)
    def test_with_args_can_operate_on_provision(self):
        self.fake.provides("not_expected").with_args('something')
        self.fake.not_expected() # should still raise arg error
    
    @raises(AssertionError)
    def test_with_args_checks_args(self):
        self.fake.expects('count').with_args('one', two='two')
        self.fake.count(two='two')
        
    @raises(AssertionError)
    def test_with_args_checks_kwargs(self):
        self.fake.expects('count').with_args('one', two='two')
        self.fake.count('one')
    
    @raises(AssertionError)
    def test_too_many_args(self):
        db = Fake("db").expects("execute").with_args(bind={'one':1})
        db.execute("select foozilate()", bind={'one':1}) # unexpected statement arg
    
    def test_zero_keywords_ok(self):
        mail = fudge.Fake('mail').expects('send').with_arg_count(3) 
        mail.send("you", "me", "hi") # no kw args should be ok
    
    def test_zero_args_ok(self):
        mail = fudge.Fake('mail').expects('send').with_kwarg_count(3) 
        mail.send(to="you", from_="me", msg="hi") # no args should be ok

## hmm, arg diffing needs more thought

# class TestArgDiff(unittest.TestCase):
#     
#     def setUp(self):
#         self.fake = Fake("foo")
#         self.call = Call(self.fake)
#     
#     def test_empty(self):
#         eq_(self.call._arg_diff(tuple(), tuple()), "")
#     
#     def test_one_unexpected(self):
#         eq_(self.call._arg_diff(('one',), tuple()), "arg #1 was unexpected")
#     
#     def test_one_missing(self):
#         eq_(self.call._arg_diff(tuple(), ('one',)), "arg #1 never showed up")
#     
#     def test_four_unexpected(self):
#         eq_(self.call._arg_diff(
#             ('one','two','three','four'),
#             ('one','two','three')), "arg #4 was unexpected")
#     
#     def test_four_missing(self):
#         eq_(self.call._arg_diff(
#             ('one','two','three'), 
#             ('one','two','three','four')), "arg #4 never showed up")
#     
#     def test_one_mismatch(self):
#         eq_(self.call._arg_diff(('won',), ('one',)), "arg #1 'won' != 'one'")
#     
#     def test_four_mismatch(self):
#         eq_(self.call._arg_diff(
#             ('one','two','three','not four'), 
#             ('one','two','three','four')), "arg #4 'not four' != 'four'")

# class TestKeywordArgDiff(unittest.TestCase):
#     
#     def setUp(self):
#         self.fake = Fake("foo")
#         self.call = Call(self.fake)
#     
#     def test_empty(self):
#         eq_(self.call._keyword_diff({}, {}), (True, ""))
#     
#     def test_one_empty(self):
#         eq_(self.call._keyword_diff({}, 
#             {'something':'here','another':'there'}), 
#             (False, "these keywords never showed up: ('something', 'another')"))
#     
#     def test_complex_match_yields_no_reason(self):
#         actual = {'num':1, 'two':2, 'three':3}
#         expected = {'num':1, 'two':2, 'three':3}
#         eq_(self.call._keyword_diff(actual, expected), (True, ""))
#     
#     def test_simple_mismatch_yields_no_reason(self):
#         actual = {'num':1}
#         expected = {'num':2}
#         eq_(self.call._keyword_diff(actual, expected), (False, ""))
#     
#     def test_simple_match_yields_no_reason(self):
#         actual = {'num':1}
#         expected = {'num':1}
#         eq_(self.call._keyword_diff(actual, expected), (True, ""))
#     
#     def test_actual_kw_extra_key(self):
#         actual = {'one':1, 'two':2}
#         expected = {'one':1}
#         eq_(self.call._keyword_diff(actual, expected), 
#             (False, "keyword 'two' was not expected"))
#     
#     def test_actual_kw_value_inequal(self):
#         actual = {'one':1, 'two':2}
#         expected = {'one':1, 'two':3}
#         eq_(self.call._keyword_diff(actual, expected), 
#             (False, "two=2 != two=3"))
#     
#     def test_expected_kw_extra_key(self):
#         actual = {'one':1}
#         expected = {'one':1, 'two':2}
#         eq_(self.call._keyword_diff(actual, expected), 
#             (False, "this keyword never showed up: ('two',)"))
#     
#     def test_expected_kw_value_inequal(self):
#         actual = {'one':1, 'two':'not two'}
#         expected = {'one':1, 'two':2}
#         eq_(self.call._keyword_diff(actual, expected), 
#             (False, "two='not two' != two=2"))

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
        fake = fudge.Fake(callable=True)
        fake() # allow the call
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
    
    @raises(RuntimeError)
    def test_raises_class(self):
        self.fake = fudge.Fake().provides("fail").raises(RuntimeError)
        self.fake.fail()
    
    @raises(RuntimeError)
    def test_raises_instance(self):
        self.fake = fudge.Fake().provides("fail").raises(RuntimeError("batteries ran out"))
        self.fake.fail()

class TestReplacementCalls(unittest.TestCase):
    
    def tearDown(self):
        fudge.clear_expectations()
    
    def test_replace_call(self):
        
        def something():
            return "hijacked"
            
        fake = fudge.Fake().provides("something").calls(something)
        eq_(fake.something(), "hijacked")
    
    def test_calls_mixed_with_returns(self):
        
        called = []
        def something():
            called.append(True)
            return "hijacked"
            
        fake = fudge.Fake().provides("something").calls(something).returns("other")
        eq_(fake.something(), "other")
        eq_(called, [True])
    
    @raises(AssertionError)
    def test_calls_mixed_with_expectations(self):
        
        def something():
            return "hijacked"
        
        # with_args() expectation should not get lost:
        fake = fudge.Fake().provides("something").calls(something).with_args(1,2)
        eq_(fake.something(), "hijacked")
        
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

class TestNextCall(unittest.TestCase):
    
    def tearDown(self):
        fudge.clear_expectations()
    
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
    
    def test_next_call_with_callables(self):
        login = fudge.Fake('login',callable=True)\
                                .returns("yes")\
                                .next_call()\
                                .returns("maybe")\
                                .next_call()\
                                .returns("no")
        eq_(login(), "yes")
        eq_(login(), "maybe")
        eq_(login(), "no")
    
    def test_returns(self):
        db = Fake("db")\
            .provides("get_id").returns(1)\
            .provides("set_id")\
            .next_call(for_method="get_id").returns(2)
        # print [c.return_val for c in db._declared_calls["get_id"]._calls]
        eq_(db.get_id(), 1)
        eq_(db.set_id(), None)
        eq_(db.get_id(), 2)
    
    def test_expectations_with_multiple_return_values(self):
        db = Fake("db")\
            .expects("get_id").returns(1)\
            .expects("set_id")\
            .next_call(for_method="get_id").returns(2)
        eq_(db.get_id(), 1)
        eq_(db.set_id(), None)
        eq_(db.get_id(), 2)
        
        fudge.verify()


class TestExpectsAndProvides(unittest.TestCase):
    
    def tearDown(self):
        fudge.clear_expectations()
    
    @raises(AssertionError)
    def test_nocall(self):
        fake = fudge.Fake()
        exp = fake.expects('something')
        fudge.verify()
    
    @raises(FakeDeclarationError)
    def test_multiple_provides_is_error(self):
        db = Fake("db").provides("insert").provides("insert")
        
    def test_multiple_provides_on_chained_fakes_ok(self):
        db = Fake("db").provides("insert").returns_fake().provides("insert")
        
    @raises(FakeDeclarationError)
    def test_multiple_expects_is_error(self):
        db = Fake("db").expects("insert").expects("insert")
        
    def test_multiple_expects_on_chained_fakes_ok(self):
        db = Fake("db").expects("insert").returns_fake().expects("insert")

class TestOrderedCalls(unittest.TestCase):
    
    def tearDown(self):
        fudge.clear_expectations()
    
    @raises(AssertionError)
    def test_out_of_order(self):
        fake = fudge.Fake().remember_order().expects("one").expects("two")
        fake.two()
        fake.one()
        fudge.verify()
    
    @raises(FakeDeclarationError)
    def test_cannot_remember_order_when_callable_is_true(self):
        fake = fudge.Fake(callable=True).remember_order()
    
    @raises(FakeDeclarationError)
    def test_cannot_remember_order_when_expect_call_is_true(self):
        fake = fudge.Fake(expect_call=True).remember_order()
    
    @raises(AssertionError)
    def test_not_enough_calls(self):
        # need to drop down a level to bypass expected calls:
        r = Registry()
        fake = Fake()
        call_order = ExpectedCallOrder(fake)
        r.remember_expected_call_order(call_order)
        
        exp = ExpectedCall(fake, "callMe", call_order=call_order)
        call_order.add_expected_call(exp)
        
        r.verify()
        
    @raises(AssertionError)
    def test_only_one_call(self):
        # need to drop down a level to bypass expected calls:
        r = Registry()
        fake = Fake()
        call_order = ExpectedCallOrder(fake)
        r.remember_expected_call_order(call_order)
        
        exp = ExpectedCall(fake, "one", call_order=call_order)
        call_order.add_expected_call(exp)
        exp() # call this
        
        exp = ExpectedCall(fake, "two", call_order=call_order)
        call_order.add_expected_call(exp)
        
        r.verify()
        
    def test_incremental_order_assertion_ok(self):
        # need to drop down a level to bypass expected calls:
        fake = Fake()
        call_order = ExpectedCallOrder(fake)
        
        exp = ExpectedCall(fake, "one", call_order=call_order)
        call_order.add_expected_call(exp)
        exp() # call this
        
        exp = ExpectedCall(fake, "two", call_order=call_order)
        call_order.add_expected_call(exp)
        
        # two() not called but assertion is not finalized:
        call_order.assert_order_met(finalize=False)
    
    def test_multiple_returns_affect_order(self):
        db = Fake("db")\
            .remember_order()\
            .expects("get_id").returns(1)\
            .expects("set_id")\
            .next_call(for_method="get_id").returns(2)
        eq_(db.get_id(), 1)
        eq_(db.set_id(), None)
        eq_(db.get_id(), 2)
        fudge.verify()
    
    @raises(AssertionError)
    def test_chained_fakes_honor_order(self):
        Thing = Fake("thing").remember_order().expects("__init__")
        holder = Thing.expects("get_holder").returns_fake()
        holder = holder.expects("init")
        
        thing = Thing()
        holder = thing.get_holder()
        # missing thing.init()
        fudge.verify()
    
    @raises(AssertionError)
    def test_too_many_calls(self):
        db = Fake("db")\
            .remember_order()\
            .expects("get_id").returns(1)\
            .expects("set_id")
        eq_(db.get_id(), 1)
        eq_(db.set_id(), None)
        # extra :
        eq_(db.get_id(), 1)
        