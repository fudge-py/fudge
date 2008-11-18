
from fudge.util import *

class Registry(object):
    
    def __init__(self):
        self.expected_calls = []
        self.clear()
        
    def clear(self):
        self.calls_made = {}
        
    def start(self):
        self.clear()
    
    def stop(self):
        """ensure all expected calls were called, 
        raise AssertionError otherwise
        """
        self.expected_calls[:] = []
        
    def expect_call(self, expected_call):
        self.expected_calls.append(expected_call)
        
registry = Registry()

def start():
    registry.start()
    
def stop():
    registry.stop()

class ExpectedCall(object):
    
    def __call__(self, *args, **kwargs):
        self.actual_args = args
        self.actual_kwargs = kwargs
        self.was_called = True
        return self.return_val
    
    def __init__(self, fake, call_name):
        self.fake = fake
        self.was_called = False
        self.call_name = call_name
        self.expected_arg_count = 0
        self.expected_args = None
        self.expected_kwargs = None
        self.return_val = None
        self.actual_args = []
        self.actual_kwargs = {}

class Fake(object):
    
    def __init__(self):
        self.calls = {}
        self.last_expected_call_name = None
    
    def __getattr__(self, name):
        if name in self.calls:
            return self.calls[name]
        else:
            raise AttributeError("%s object has no attribute '%s'" % (
                                    self.__class__, name))
    
    def __call__(self, *args, **kwargs):
        # special case, simulation of __init__():
        expected_call = self.calls['__init__']
        expected_call(*args, **kwargs)
        return self
    
    def expects(self, call_name):
        self.last_expected_call_name = call_name
        exp = ExpectedCall(self, call_name)
        self.calls[call_name] = exp
        registry.expect_call(exp)
        return self
    
    def with_args(self, *args, **kwargs):
        assert self.last_expected_call_name
        exp = self.calls[self.last_expected_call_name]
        if args:
            exp.expected_args = args
        if kwargs:
            exp.expected_kwargs = kwargs
        return self
    
    def with_arg_count(self, count):
        assert self.last_expected_call_name
        exp = self.calls[self.last_expected_call_name]
        exp.expected_arg_count = count
        return self
    
    def returns_fake(self):
        assert self.last_expected_call_name
        exp = self.calls[self.last_expected_call_name]
        fake = self.__class__()
        exp.return_val = fake
        return fake
    
    def returns(self, val):
        assert self.last_expected_call_name
        exp = self.calls[self.last_expected_call_name]
        exp.return_val = val
        return self
        