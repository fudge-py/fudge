
"""Fudge is a module for replacing real objects with fakes (mocks, stubs, etc) while testing.
"""

__version__ = '0.9.0'
import os
import re
import sys
import thread
from fudge.patcher import *
from fudge.util import wraps

__all__ = ['start', 'stop', 'clear_expectations', 'Fake']

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
    
    This is also available as a decorator: :func:`fudge.with_fakes`
    """
    registry.start()
    
def stop():
    """Stop testing with fake objects.
    
    Specifically, analyze all registered fake 
    objects and raise an AssertionError if an 
    expected call was never made to one or more 
    objects.
    
    This is also available as a decorator: :func:`fudge.with_fakes`
    """
    registry.stop()

def clear_expectations():
    registry.clear_expectations()

def with_fakes(method):
    """Decorator that calls :func:`fudge.start` before method() and :func:`fudge.stop` afterwards.
    """
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
        cls_name = repr(self.fake)
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
    
    def get_call_object(self):
        """return self.
        
        this exists for compatibility with :class:`CallStack`
        """
        return self
    
class ExpectedCall(Call):
    """An expectation that a call will be made on a Fake object.
    
    You do not need to use this directly, use Fake.expects(...), etc
    """
    
    def assert_called(self):
        if not self.was_called:
            raise AssertionError("%s was not called" % (self))

class CallStack(object):
    """A stack of :class:`Call` objects
    
    Calling this object behaves just like Call except 
    the Call instance you operate on gets changed each time __call__() is made
    """
    def __init__(self, fake, initial_calls=None):
        self.fake = fake
        self._pointer = 0
        if initial_calls is not None:
            self._calls = initial_calls
        else:
            self._calls = []
            
    def add_call(self, call):
        self._calls.append(call)
    
    def get_call_object(self):
        """returns the last *added* call object.
        
        this is so Fake knows which one to alter
        """
        return self._calls[len(self._calls)-1]
    
    def reset(self):
        self._pointer = 0
    
    def __call__(self, *args, **kw):
        try:
            current_call = self._calls[self._pointer]
        except IndexError:
            raise AssertionError(
                "This attribute of %s can only be called %s time(s).  "
                "Call reset() if necessary." % (self.fake, len(self._calls)))
        self._pointer += 1
        return current_call(*args, **kw)

class Fake(object):
    """A fake object that replaces a real one while testing.
    
    Most calls with a few exceptions return ``self`` so that you can chain them together to 
    create readable code.
    
    Keyword arguments:
    
    **name=None**
        Name of the class, module, or function you mean to replace. If not specified, 
        Fake() will try to guess the name by inspecting the calling frame (if possible).
    
    **allows_any_call=False**
        When True, any method is allowed to be called on the Fake() instance.  Each method 
        will be a stub that does nothing if it has not been defined.  Implies callable=True.
    
    **callable=False**
        When True, the Fake() acts like a callable.  Use this if you are replacing a single 
        method.
    
    Short example::
    
        >>> import fudge
        >>> auth = fudge.Fake('auth').expects('login').with_args('joe_username', 'joes_password')
        >>> auth.login("joe_username", "joes_password") # now works
        >>> fudge.clear_expectations()
        
    """
    
    def __init__(self, name=None, allows_any_call=False, callable=False):
        self._attributes = {}
        self._declared_calls = {}
        self._name = (name or self._guess_name())
        self._last_declared_call_name = None
        self._allows_any_call = allows_any_call
        self._stub = None
        self._call_stack = None
        self._callable = callable or allows_any_call
    
    def __getattribute__(self, name):
        """Favors stubbed out attributes, falls back to real attributes
        
        """
        # this getter circumvents infinite loops:
        def g(n):
            return object.__getattribute__(self, n)
            
        if name in g('_declared_calls'):
            # if it's a call that has been declared
            # as that of the real object then hand it over:
            return g('_declared_calls')[name]
        elif name in g('_attributes'):
            # return attribute declared on real object
            return g('_attributes')[name]
        else:
            # otherwise, first check if it's a call
            # of Fake itself (i.e. returns(),  with_args(), etc)
            try:
                self_call = g(name)
            except AttributeError:
                pass
            else:
                return self_call
            
            if g('_allows_any_call'):
                return Call(self, call_name=name)
            
            raise AttributeError("%s object does not allow call or attribute '%s'" % (
                                    self, name))
    
    def __call__(self, *args, **kwargs):
        if '__init__' in self._declared_calls:
            # special case, simulation of __init__():
            call = self._declared_calls['__init__']
            call(*args, **kwargs)
            return self
        elif self._callable:
            # go into stub mode:
            if not self._stub:
                self._stub = Call(self)
            call = self._stub
            return call(*args, **kwargs)
        else:
            raise RuntimeError("%s object cannot be called (maybe you want %s(callable=True) ?)" % (
                                                                        self, self.__class__.__name__))
    
    def __repr__(self):
        return "fake:%s" % (self._name or "unnamed")
    
    def _declare_call(self, call_name, call):
        self._declared_calls[call_name] = call
    
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
        #   we want to set self._name = 'my_obj'
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
        exp = self._declared_calls[self._last_declared_call_name].get_call_object()
        return exp
    
    def calls(self, call):
        """Redefine a call."""
        exp = self._get_current_call()
        exp.call_replacement = call
        return self
    
    def expects(self, call_name):
        """Expect a call."""
        self._last_declared_call_name = call_name
        c = ExpectedCall(self, call_name)
        self._declare_call(call_name, c)
        registry.expect_call(c)
        return self
    
    def has_attr(self, **attributes):
        self._attributes.update(attributes)
        return self
    
    def next_call(self):
        """Start expecting multiple calls on your object.
        
        Up until calling this method, calls are infinite.
        """
        exp = self._get_current_call()
        if not isinstance(exp, CallStack):
            # lazily create a stack with the last defined 
            # expected call as the first on the stack:
            stack = CallStack(self, initial_calls=[exp])
        
            # replace the old call obj using the same name:
            self._declare_call(exp.call_name, stack)
        else:
            stack = exp
        
        # hmm, we need a copy here so that the last call 
        # falls off the stack.
        stack.add_call(Call(self, call_name=exp.call_name))
        return self
    
    def provides(self, call_name):
        """Provide a call."""
        self._last_declared_call_name = call_name
        c = Call(self, call_name)
        self._declare_call(call_name, c)
        return self
    
    def returns(self, val):
        """Return a value."""
        exp = self._get_current_call()
        exp.return_val = val
        return self
    
    def returns_fake(self, *args, **kwargs):
        """Return a fake.
        
        Any arguments are passed to the :class:`fudge.Fake` constructor
        
        Take note that this is different from the cascading nature of 
        other methods.  This will return an instance to the *new* fake object 
        so you should be careful to store its return value in a new variable.
        """
        exp = self._get_current_call()
        fake = self.__class__(*args, **kwargs)
        exp.return_val = fake
        return fake
    
    def with_args(self, *args, **kwargs):
        """Expect specific arguments."""
        exp = self._get_current_call()
        if args:
            exp.expected_args = args
        if kwargs:
            exp.expected_kwargs = kwargs
        return self
    
    def with_arg_count(self, count):
        """Expect an exact argument count."""
        exp = self._get_current_call()
        exp.expected_arg_count = count
        return self
    
    def with_kwarg_count(self, count):
        """Expect an exact count of keyword arguments."""
        exp = self._get_current_call()
        exp.expected_kwarg_count = count
        return self
        