
"""Fudge is a module for replacing real objects with fakes (mocks, stubs, etc) while testing.

See :ref:`fudge-examples` for common scenarios.

"""

__version__ = '0.9.1'
import os
import re
import sys
import thread
import warnings
from fudge.exc import FakeDeclarationError
from fudge.patcher import *
from fudge.util import wraps

__all__ = ['start', 'stop', 'clear_expectations', 'Fake']

class Registry(object):
    """An internal, thread-safe registry of expected calls.
    
    You do not need to use this directly, use Fake.expects(...), etc
    """
    
    def __init__(self):
        self.expected_calls = {}
        self.call_stacks = []
    
    def __contains__(self, obj):
        return obj in self.get_expected_calls()
        
    def clear_actual_calls(self):
        for exp in self.get_expected_calls():
            exp.was_called = False
    
    def clear_all(self):
        self.clear_actual_calls()
        self.clear_expectations()
    
    def clear_calls(self):
        """Clears out any calls that were made on previously 
        registered fake objects and resets all call stacks.
        
        You do not need to use this directly.  Use fudge.clear_calls()
        """
        self.clear_actual_calls()
        for stack in self.call_stacks:
            stack.reset()
    
    def clear_expectations(self):
        c = self.get_expected_calls()
        c[:] = []
        
    def expect_call(self, expected_call):
        c = self.get_expected_calls()
        c.append(expected_call)
    
    def get_expected_calls(self):
        self.expected_calls.setdefault(thread.get_ident(), [])
        return self.expected_calls[thread.get_ident()]
    
    def register_call_stack(self, call_stack):
        self.call_stacks.append(call_stack)
    
    def verify(self):
        """Ensure all expected calls were called, 
        raise AssertionError otherwise.
        
        You do not need to use this directly.  Use fudge.verify()
        """
        try:
            for exp in self.get_expected_calls():
                exp.assert_called()
                exp.assert_times_called()
        finally:
            self.clear_calls()
        
registry = Registry()

def clear_calls():
    """Begin a new set of calls on fake objects.
    
    Specifically, clear out any calls that 
    were made on previously registered fake 
    objects and reset all call stacks.  
    You should call this any time you begin 
    making calls on fake objects.
    
    This is also available as a decorator: :func:`fudge.with_fakes`
    """
    registry.clear_calls()

def verify():
    """Verify that all methods have been called as expected.
    
    Specifically, analyze all registered fake 
    objects and raise an AssertionError if an 
    expected call was never made to one or more 
    objects.
    
    This is also available as a decorator: :func:`fudge.with_fakes`
    """
    registry.verify()

## Deprecated:

def start():
    """Start testing with fake objects.
    
    Deprecated.  Use :func:`fudge.clear_calls` instead.
    """
    warnings.warn("fudge.start() has been deprecated.  Use fudge.clear_calls() instead", 
                    DeprecationWarning, 3)
    clear_calls()
    
def stop():
    """Stop testing with fake objects.
    
    Deprecated.  Use :func:`fudge.verify` instead.
    """
    warnings.warn("fudge.stop() has been deprecated.  Use fudge.verify() instead", 
                    DeprecationWarning, 3)
    verify()

##

def clear_expectations():
    registry.clear_expectations()

def with_fakes(method):
    """Decorator that calls :func:`fudge.clear_calls` before method() and :func:`fudge.verify` afterwards.
    """
    @wraps(method)
    def apply_clear_and_verify(*args, **kw):
        clear_calls()
        method(*args, **kw)
        verify() # if no exceptions
    return apply_clear_and_verify

def fmt_val(val):
    """Format a value for inclusion in an 
    informative text string.
    """
    val = repr(val)
    max = 50
    if len(val) > max:
        close = val[-1]
        val = val[0:max-4] + "..."
        if close in (">", "'", '"', ']', '}', ')'):
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
    
    index=None
        When numerical, this indicates the position of the call 
        (as in, a CallStack)
    """
    
    def __init__(self, fake, call_name=None, index=None):
        self.fake = fake
        self.call_name = call_name
        self.call_replacement = None
        self.expected_arg_count = None
        self.expected_kwarg_count = None
        self.expected_args = None
        self.expected_kwargs = None
        self.index = index
        self.return_val = None
        self.was_called = False
        self.expected_times_called = None
        self.actual_times_called = 0
        
    def __call__(self, *args, **kwargs):
        self.was_called = True
        self.actual_times_called += 1
        
        # make sure call count doesn't go over :
        if self.expected_times_called is not None and \
                self.actual_times_called > self.expected_times_called:
            raise AssertionError(
                '%s was called %s time(s). Expected %s.' % (
                    self, self.actual_times_called, self.expected_times_called))

        if self.call_replacement:
            return self.call_replacement(*args, **kwargs)
            
        if self.expected_args:
            if args != self.expected_args:
                raise AssertionError(
                    "%s was called unexpectedly with args %s" % (self, self._repr_call(args, kwargs)))
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

    def _repr_call(self, expected_args, expected_kwargs):
        args = []
        if expected_args:
            args.extend([fmt_val(a) for a in expected_args])
        if expected_kwargs:
            args.extend(fmt_dict_vals(expected_kwargs))
        if args:
            call = "(%s)" % ", ".join(args)
        else:
            call = "()"
        return call
    
    def __repr__(self):
        cls_name = repr(self.fake)
        if self.call_name:
            call = "%s.%s" % (cls_name, self.call_name)
        else:
            call = "%s" % cls_name
        call = "%s%s" % (call, self._repr_call(self.expected_args, self.expected_kwargs))
        if self.index is not None:
            call = "%s[%s]" % (call, self.index)
        return call
    
    def get_call_object(self):
        """return self.
        
        this exists for compatibility with :class:`CallStack`
        """
        return self

    def assert_times_called(self):
        if self.expected_times_called is not None and \
                self.actual_times_called != self.expected_times_called:
            raise AssertionError(
                '%s was called %s time(s). Expected %s.' % (
                    self, self.actual_times_called, self.expected_times_called))
            
    

class ExpectedCall(Call):
    """An expectation that a call will be made on a Fake object.
    
    You do not need to use this directly, use Fake.expects(...), etc
    """
    
    def __init__(self, *args, **kw):
        super(ExpectedCall, self).__init__(*args, **kw)
        registry.expect_call(self)
    
    def assert_called(self):
        if not self.was_called:
            raise AssertionError("%s was not called" % (self))


class CallStack(object):
    """A stack of :class:`Call` objects
    
    Calling this object behaves just like Call except 
    the Call instance you operate on gets changed each time __call__() is made
    
    expected=False
        When True, this indicates that the call stack was derived 
        from an expected call.  This is used by Fake to register 
        each call on the stack.
        
    """
    
    def __init__(self, fake, initial_calls=None, expected=False):
        self.fake = fake
        self._pointer = 0 # position of next call to be made (can be reset)
        self._calls = []
        if initial_calls is not None:
            for c in initial_calls:
                self.add_call(c)
        self.expected = expected
        registry.register_call_stack(self)
    
    def __iter__(self):
        for c in self._calls:
            yield c
            
    def add_call(self, call):
        self._calls.append(call)
        call.index = len(self._calls)-1
    
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
        method.  See example below.
    
    **expect_call=True**
        When True, the Fake() acts like a callable that must be called (implies callable=True).
        Use this when replace a single method that must be called.  See example below.
    
    Short example::
    
        >>> import fudge
        >>> auth = fudge.Fake('auth').expects('login').with_args('joe_username', 'joes_password')
        >>> auth.login("joe_username", "joes_password") # now works
        >>> fudge.clear_expectations()
    
    When ``callable=True`` the object acts like a method ::
        
        >>> import fudge
        >>> login = fudge.Fake('login', callable=True)
        >>> login() # can be called
    
    When ``expect_call=True`` the object acts like a method that must be called ::
    
        >>> import fudge
        >>> login = fudge.Fake('login', expect_call=True).times_called(2)
        >>> login()
        >>> fudge.verify()
        Traceback (most recent call last):
        ...
        AssertionError: fake:login() was called 1 time(s). Expected 2.
        >>> fudge.clear_expectations()
        
    """
    
    def __init__(self, name=None, allows_any_call=False, callable=False, expect_call=False):
        self._attributes = {}
        self._declared_calls = {}
        self._name = (name or self._guess_name())
        self._last_declared_call_name = None
        self._allows_any_call = allows_any_call
        self._call_stack = None
        if expect_call:
            self._callable = ExpectedCall(self)
        elif callable or allows_any_call:
            self._callable = Call(self)
        else:
            self._callable = None
    
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
                g('_callable').call_name = name
                return g('_callable')
            
            raise AttributeError("%s object does not allow call or attribute '%s'" % (
                                    self, name))
    
    def __call__(self, *args, **kwargs):
        if '__init__' in self._declared_calls:
            # special case, simulation of __init__():
            call = self._declared_calls['__init__']
            call(*args, **kwargs)
            return self
        elif self._callable:
            return self._callable(*args, **kwargs)
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
            if not self._callable:
                raise ValueError("Call to a method that expects a predefined call but no such call exists")
            return self._callable
        exp = self._declared_calls[self._last_declared_call_name].get_call_object()
        return exp
    
    def calls(self, call):
        """Redefine a call.
        
        The fake method will execute your function.  I.E.::
            
            >>> f = Fake().provides('hello').calls(lambda: 'Why, hello there')
            >>> f.hello()
            'Why, hello there'
            
        """
        exp = self._get_current_call()
        exp.call_replacement = call
        return self
    
    def expects(self, call_name):
        """Expect a call.
        
        If the method *call_name* is never called, then raise an error.  I.E.::
            
            >>> session = Fake('session').expects('open').expects('close')
            >>> import fudge
            >>> fudge.clear_calls()
            >>> session.open()
            >>> fudge.verify()
            Traceback (most recent call last):
            ...
            AssertionError: fake:session.close() was not called
            
        """
        self._last_declared_call_name = call_name
        c = ExpectedCall(self, call_name)
        self._declare_call(call_name, c)
        return self
    
    def has_attr(self, **attributes):
        """Sets available attributes.
        
        I.E.::
            
            >>> User = Fake('User').provides('__init__').has_attr(name='Harry')
            >>> user = User()
            >>> user.name
            'Harry'
            
        """
        self._attributes.update(attributes)
        return self
    
    def next_call(self):
        """Start expecting or providing multiple calls.
        
        Up until calling this method, calls are infinite.
        
        For example, before next_call() ... ::
        
            >>> f = Fake().provides('status').returns('Awake!')
            >>> f.status()
            'Awake!'
            >>> f.status()
            'Awake!'
        
        After next_call() ... ::
            
            >>> f = Fake().provides('status').returns('Awake!')
            >>> f = f.next_call().returns('Asleep')
            >>> f = f.next_call().returns('Dreaming')
            >>> f.status()
            'Awake!'
            >>> f.status()
            'Asleep'
            >>> f.status()
            'Dreaming'
            >>> f.status()
            Traceback (most recent call last):
            ...
            AssertionError: This attribute of fake:unnamed can only be called 3 time(s).  Call reset() if necessary.
            
        .. note:: This cannot be used in combination with :func:`fudge.Fake.times_called`
        
        """
        exp = self._declared_calls[self._last_declared_call_name]
        if getattr(exp, 'expected_times_called', None) is not None:
            raise FakeDeclarationError("Cannot use next_call() in combination with times_called()")
        
        if not isinstance(exp, CallStack):
            # lazily create a stack with the last defined 
            # expected call as the first on the stack:
            stack = CallStack(self, initial_calls=[exp], 
                                    expected=isinstance(exp, ExpectedCall))
        
            # replace the old call obj using the same name:
            self._declare_call(self._last_declared_call_name, stack)
        else:
            stack = exp
        
        # hmm, we need a copy here so that the last call 
        # falls off the stack.
        if stack.expected:
            next_call = ExpectedCall(self, call_name=self._last_declared_call_name)
        else:
            next_call = Call(self, call_name=self._last_declared_call_name)
        stack.add_call(next_call)
        return self
    
    def provides(self, call_name):
        """Provide a call.
        
        The call acts as a stub -- no error is raised if it is not called.::
        
            >>> session = Fake('session').provides('open').provides('close')
            >>> import fudge
            >>> fudge.clear_expectations() # from any previously declared fakes
            >>> fudge.clear_calls()
            >>> session.open()
            >>> fudge.verify() # close() not called but no error
            
        """
        self._last_declared_call_name = call_name
        c = Call(self, call_name)
        self._declare_call(call_name, c)
        return self
    
    def returns(self, val):
        """Set the last call to return a value.
        
        Set a static value to return when a method is called.  I.E.::
        
            >>> f = Fake().provides('get_number').returns(64)
            >>> f.get_number()
            64
            
        """
        exp = self._get_current_call()
        exp.return_val = val
        return self
    
    def returns_fake(self, *args, **kwargs):
        """Set the last call to return a new :class:`fudge.Fake`.
        
        Any given arguments are passed to the :class:`fudge.Fake` constructor
        
        Take note that this is different from the cascading nature of 
        other methods.  This will return an instance of the *new* Fake, 
        not self, so you should be careful to store its return value in a new variable.
        
        I.E.::
            
            >>> session = Fake('session')
            >>> query = session.provides('query').returns_fake()
            >>> assert query is not session
            >>> query = query.provides('one').returns(['object'])
            
            >>> session.query().one()
            ['object']
            
        """
        exp = self._get_current_call()
        fake = self.__class__(*args, **kwargs)
        exp.return_val = fake
        return fake
        
    def times_called(self, n):
        """Set the number of times an object can be called.

        When working with provided calls, you'll only see an 
        error if the expected call count is exceeded ::
        
            >>> auth = Fake('auth').provides('login').times_called(1)
            >>> auth.login()
            >>> auth.login()
            Traceback (most recent call last):
            ...
            AssertionError: fake:auth.login() was called 2 time(s). Expected 1.
        
        When working with expected calls, you'll see an error if 
        the call count is never met ::
        
            >>> import fudge
            >>> auth = fudge.Fake('auth').expects('login').times_called(2)
            >>> auth.login()
            >>> fudge.verify()
            Traceback (most recent call last):
            ...
            AssertionError: fake:auth.login() was called 1 time(s). Expected 2.
        
        .. note:: This cannot be used in combination with :func:`fudge.Fake.next_call`
        
        """
        if self._last_declared_call_name:
            actual_last_call = self._declared_calls[self._last_declared_call_name]
            if isinstance(actual_last_call, CallStack):
                raise FakeDeclarationError("Cannot use times_called() in combination with next_call()")
        # else: # self._callable is in effect
        
        exp = self._get_current_call()
        exp.expected_times_called = n
        return self
    
    def with_args(self, *args, **kwargs):
        """Set the last call to expect specific arguments.
        
        I.E.::
            
            >>> counter = Fake('counter').expects('increment').with_args(25, table='hits')
            >>> counter.increment(24, table='clicks')
            Traceback (most recent call last):
            ...
            AssertionError: fake:counter.increment(25, table='hits') was called unexpectedly with args (24, table='clicks')
            
        """
        exp = self._get_current_call()
        if args:
            exp.expected_args = args
        if kwargs:
            exp.expected_kwargs = kwargs
        return self
    
    def with_arg_count(self, count):
        """Set the last call to expect an exact argument count.
        
        I.E.::
            
            >>> auth = Fake('auth').provides('login').with_arg_count(2)
            >>> auth.login('joe_user') # forgot password
            Traceback (most recent call last):
            ...
            AssertionError: fake:auth.login() was called with 1 arg(s) but expected 2
            
        """
        exp = self._get_current_call()
        exp.expected_arg_count = count
        return self
    
    def with_kwarg_count(self, count):
        """Set the last call to expect an exact count of keyword arguments.
        
        I.E.::
            
            >>> auth = Fake('auth').provides('login').with_kwarg_count(2)
            >>> auth.login(username='joe') # forgot password=
            Traceback (most recent call last):
            ...
            AssertionError: fake:auth.login() was called with 1 keyword arg(s) but expected 2
            
        """
        exp = self._get_current_call()
        exp.expected_kwarg_count = count
        return self
