
import thread
from fudge.patcher import *
from fudge.util import wraps

class Registry(object):
    """An internal, thread-safe registry of expected calls.
    
    You do not need to use this directly, use Fake.expects(...), etc
    """
    
    def __init__(self):
        self.expected_calls = {}
    
    def clear_actual_calls(self):
        for exp in self.get_expected_calls():
            exp.was_called = False
    
    def clear_all(self):
        self.clear_actual_calls()
        self.clear_expectations()
        
    def clear_expectations(self):
        c = self.get_expected_calls()
        c[:] = []
    
    def get_expected_calls(self):
        self.expected_calls.setdefault(thread.get_ident(), [])
        return self.expected_calls[thread.get_ident()]
    
    def start(self):
        """Clears out any calls that were made on previously 
        registered fake objects.
        
        You do not need to use this directly.  Use fudge.start()
        """
        self.clear_actual_calls()
    
    def stop(self):
        """Ensure all expected calls were called, 
        raise AssertionError otherwise.
        
        You do not need to use this directly.  Use fudge.stop()
        """
        try:
            for exp in self.get_expected_calls():
                exp.assert_called()
        finally:
            self.clear_all()
        
    def expect_call(self, expected_call):
        c = self.get_expected_calls()
        c.append(expected_call)
        
registry = Registry()

def start():
    """Start testing with fake objects.
    
    Specifically, clear out any calls that 
    were made on previously registered fake 
    objects.  You don't really need to call 
    this but it's safer since an exception 
    might bubble up from a previous test.
    """
    registry.start()
    
def stop():
    """Stop testing with fake objects.
    
    Specifically, analyze all registered fake 
    objects and raise an AssertionError if an 
    expected call was never made to one or more 
    objects.
    """
    registry.stop()

def with_fakes(method):
    @wraps(method)
    def apply_start_stop(*args, **kw):
        start()
        method(*args, **kw)
        stop()
    return apply_start_stop

def fmt_val(val):
    """Format a value for inclusion in an 
    informative text string.
    """
    val = repr(val)
    if len(val) > 10:
        close = val[-1]
        val = val[0:7] + "..."
        if close in ("'", '"', ']', '}', ')'):
            val = val + close
    return val

def fmt_dict_vals(dict_vals):
    """Returns list of key=val pairs formatted
    for inclusion in an informative text string.
    """
    items = dict_vals.items()
    if not items:
        return [fmt_val(None)]
    return ["%s=%s" % (k, fmt_val(v)) for k,v in items]
    
class ExpectedCall(object):
    """An expectation that a call will be made on a Fake object.
    
    You do not need to use this directly, use Fake.expects(...), etc
    """
    
    def __call__(self, *args, **kwargs):
        if self.expected_args:
            if args != self.expected_args:
                raise AssertionError(
                    "%s was called unexpectedly with args %s" % (self, args))
        elif len(args) != self.expected_arg_count:
            raise AssertionError(
                "%s was called with %s arg(s) but expected %s" % (
                    self, len(args), self.expected_arg_count))
                    
        if self.expected_kwargs:
            if kwargs != self.expected_kwargs:
                raise AssertionError(
                    "%s was called unexpectedly with keyword args %s" % (
                                self, ", ".join(fmt_dict_vals(kwargs))))
        elif len(kwargs.keys()) != self.expected_kwarg_count:
            raise AssertionError(
                "%s was called with %s keyword arg(s) but expected %s" % (
                    self, len(kwargs.keys()), self.expected_kwarg_count))
        
        self.was_called = True
        return self.return_val
    
    def __repr__(self):
        call = "%s.%s(" % (self.fake.__class__.__name__, self.call_name)
        args = []
        if self.expected_args:
            args.extend([fmt_val(a) for a in self.expected_args])
        if self.expected_kwargs:
            args.extend(fmt_dict_vals(self.expected_kwargs))
        if args:
            call = "%s%s" % (call, ", ".join(args))
        call = "%s)" % call
        return call
    
    def __init__(self, fake, call_name):
        self.fake = fake
        self.was_called = False
        self.call_name = call_name
        self.expected_arg_count = 0
        self.expected_kwarg_count = 0
        self.expected_args = None
        self.expected_kwargs = None
        self.return_val = None
    
    def assert_called(self):
        if not self.was_called:
            raise AssertionError("%s was not called" % (self))

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
        