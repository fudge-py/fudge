
import os
import re
import sys
import thread
from fudge.patcher import *
from fudge.util import wraps

class Registry(object):
    """An internal, thread-safe registry of expected calls.
    
    You do not need to use this directly, use Fake.expects(...), etc
    """
    
    def __init__(self):
        self.expected_calls = {}
    
    def __contains__(self, obj):
        return obj in self.get_expected_calls()
    
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
            self.clear_actual_calls()
        
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

def clear_expectations():
    registry.clear_expectations()

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

class Call(object):
    """A call that can be made on a Fake object.
    
    You do not need to use this directly, use Fake.provides(...), etc
    """
    
    def __init__(self, fake, call_name=None):
        self.fake = fake
        self.call_name = call_name
        self.call_replacement = None
        self.expected_arg_count = None
        self.expected_kwarg_count = None
        self.expected_args = None
        self.expected_kwargs = None
        self.return_val = None
        self.was_called = False
        
    def __call__(self, *args, **kwargs):
        self.was_called = True
        if self.call_replacement:
            return self.call_replacement(*args, **kwargs)
            
        if self.expected_args:
            if args != self.expected_args:
                raise AssertionError(
                    "%s was called unexpectedly with args %s" % (self, args))
        elif self.expected_arg_count is not None:
            if len(args) != self.expected_arg_count:
                raise AssertionError(
                    "%s was called with %s arg(s) but expected %s" % (
                        self, len(args), self.expected_arg_count))
                    
        if self.expected_kwargs:
            if kwargs != self.expected_kwargs:
                raise AssertionError(
                    "%s was called unexpectedly with keyword args %s" % (
                                self, ", ".join(fmt_dict_vals(kwargs))))
        elif self.expected_kwarg_count is not None:
            if len(kwargs.keys()) != self.expected_kwarg_count:
                raise AssertionError(
                    "%s was called with %s keyword arg(s) but expected %s" % (
                        self, len(kwargs.keys()), self.expected_kwarg_count))
        
        return self.return_val
    
    def __repr__(self):
        cls_name = self.fake.__class__.__name__
        if self.call_name:
            call = "%s.%s(" % (cls_name, self.call_name)
        else:
            call = "%s(" % cls_name
        args = []
        if self.expected_args:
            args.extend([fmt_val(a) for a in self.expected_args])
        if self.expected_kwargs:
            args.extend(fmt_dict_vals(self.expected_kwargs))
        if args:
            call = "%s%s" % (call, ", ".join(args))
        call = "%s)" % call
        return call
    
class ExpectedCall(Call):
    """An expectation that a call will be made on a Fake object.
    
    You do not need to use this directly, use Fake.expects(...), etc
    """
    
    def assert_called(self):
        if not self.was_called:
            raise AssertionError("%s was not called" % (self))

class Fake(object):
    
    def __init__(self, name=None, allows_any_call=False, callable=False):
        self.name = (name or self._guess_name())
        self._declared_calls = {}
        self._last_declared_call_name = None
        self._allows_any_call = allows_any_call
        self._stub = None
        self._callable = callable
    
    def __getattr__(self, name):
        if name in self._declared_calls:
            return self._declared_calls[name]
        else:
            if self._allows_any_call:
                return Call(self, call_name=name)
            raise AttributeError("%s object does not allow call or attribute '%s'" % (
                                    self, name))
    
    def __call__(self, *args, **kwargs):
        if '__init__' in self._declared_calls:
            # special case, simulation of __init__():
            call = self._declared_calls['__init__']
        elif self._callable:
            # go into stub mode:
            if not self._stub:
                self._stub = Call(self)
            call = self._stub
        else:
            raise RuntimeError("%s object cannot be called (maybe you want %s(callable=True) ?)" % (
                                                                        self, self.__class__.__name__))
        call(*args, **kwargs)
        return self
    
    def __repr__(self):
        return "fake:%s" % (self.name or "unnamed")
    
    _assignment = re.compile(r"\s*(?P<name>[a-zA-Z0-9_]+)\s*=\s*(fudge\.)?Fake\(.*")    
    def _guess_asn_from_file(self, frame):
        if frame.f_code.co_filename:
            if os.path.exists(frame.f_code.co_filename):
                cofile = open(frame.f_code.co_filename,'r')
                try:
                    for ln, line in enumerate(cofile):
                        # I'm not sure why -1 is needed
                        if ln==frame.f_lineno-1:
                            possible_asn = line
                            m = self._assignment.match(possible_asn)
                            if m:
                                return m.group('name')
                finally:
                    cofile.close()
    
    def _guess_name(self):
        if not hasattr(sys, '_getframe'):
            # Stackless, Jython?
            return None
        
        # get frame where class was instantiated,
        #   my_obj = Fake()
        #   ^
        #   we want to set self.name = 'my_obj'
        frame = sys._getframe(2)
        if len(frame.f_code.co_varnames):
            # at the top-most frame:
            co_names = frame.f_code.co_varnames
        else:
            # any other frame:
            co_names = frame.f_code.co_names
        
        # find names that are not locals.
        # this probably indicates my_obj = ...
        
        candidates = [n for n in co_names if n not in frame.f_locals]
        if len(candidates)==0:
            # the value was possibly queued for deref
            #   foo = 44
            #   foo = Fake()
            return self._guess_asn_from_file(frame)
        elif len(candidates)==1:
            return candidates[0]
        else:
            # we are possibly halfway through a module
            # where not all names have been compiled
            return self._guess_asn_from_file(frame)
    
    def _get_current_call(self):
        if not self._last_declared_call_name:
            if not self._stub:
                self._stub = Call(self)
            return self._stub
        exp = self._declared_calls[self._last_declared_call_name]
        return exp
    
    def calls(self, call):
        exp = self._get_current_call()
        exp.call_replacement = call
        return self
    
    def expects(self, call_name):
        self._last_declared_call_name = call_name
        c = ExpectedCall(self, call_name)
        self._declared_calls[call_name] = c
        registry.expect_call(c)
        return self
    
    def provides(self, call_name):
        self._last_declared_call_name = call_name
        c = Call(self, call_name)
        self._declared_calls[call_name] = c
        return self
    
    def returns(self, val):
        exp = self._get_current_call()
        exp.return_val = val
        return self
    
    def returns_fake(self):
        exp = self._get_current_call()
        fake = self.__class__()
        exp.return_val = fake
        return fake
    
    def with_args(self, *args, **kwargs):
        exp = self._get_current_call()
        if args:
            exp.expected_args = args
        if kwargs:
            exp.expected_kwargs = kwargs
        return self
    
    def with_arg_count(self, count):
        exp = self._get_current_call()
        exp.expected_arg_count = count
        return self
    
    def with_kwarg_count(self, count):
        exp = self._get_current_call()
        exp.expected_kwarg_count = count
        return self
        