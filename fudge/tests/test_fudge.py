
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
        self.reg.start()
    
    @raises(AssertionError)
    def test_expected_calls(self):
        self.reg.expect_call(ExpectedCall(self.fake, 'nothing'))
        self.reg.stop()
        
    @raises(AssertionError)
    def test_more_expected_calls(self):
        exp = ExpectedCall(self.fake, 'elsewhere')
        self.reg.expect_call(exp)
        exp()
        self.reg.expect_call(ExpectedCall(self.fake, 'nothing'))
        self.reg.stop()
    
    def test_stop(self):
        exp = ExpectedCall(self.fake, 'callMe')
        self.reg.expect_call(exp)
        exp()
        eq_(len(self.reg.expected_calls), 1)
        self.reg.stop()
        eq_(len(self.reg.expected_calls), 0)
    
    def test_global_stop(self):
        exp = ExpectedCall(self.fake, 'callMe')
        exp()
        self.reg.expect_call(exp)
        eq_(len(self.reg.expected_calls), 1)
        fudge.start()
        eq_(len(self.reg.expected_calls), 0)
        self.reg.expect_call(exp)
        eq_(len(self.reg.expected_calls), 1)
        fudge.stop()
        eq_(len(self.reg.expected_calls), 0)
        
        
        