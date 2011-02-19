
"""Patching utilities for working with fake objects.

See :ref:`using-fudge` for common scenarios.
"""

__all__ = ['patch_object', 'with_patched_object', 'PatchHandler',
           'patched_context', 'patch']

import sys
from threading import Lock

import fudge
from fudge.util import wraps

lock = Lock()


class patch(object):
    """A test decorator that patches importable names with :class:`fakes <Fake>`
    
    Each fake is exposed as an argument to the test:
    
    .. doctest::
        :hide:
        
        >>> import fudge

    .. doctest::
        
        >>> @fudge.patch('os.remove')
        ... def test(fake_remove):
        ...     fake_remove.expects_call()
        ...     # do stuff...
        ... 
        >>> test()
        Traceback (most recent call last):
        ...
        AssertionError: fake:os.remove() was not called
    
    .. doctest::
        :hide:
        
        >>> fudge.clear_expectations()
    
    Many paths can be patched at once:

    .. doctest::
        
        >>> @fudge.patch('os.remove',
        ...              'shutil.rmtree')
        ... def test(fake_remove, fake_rmtree):
        ...     fake_remove.is_callable()
        ...     # do stuff...
        ... 
        >>> test()
    
    For convenience, the patch method calls
    :func:`fudge.clear_calls`, :func:`fudge.verify`, and :func:`fudge.clear_expectations`.  For that reason, you must manage all your fake objects within the test function itself.

    .. note::
    
        If you are using a unittest class, you cannot declare fakes
        within ``setUp()`` unless you manually clear calls and clear 
        expectations.  If you do that, you'll want to use the 
        :func:`fudge.with_fakes` decorator instead of ``@patch``.
    
    """
    
    def __init__(self, *obj_paths):
        self.obj_paths = obj_paths
    
    def __call__(self, fn):
        @wraps(fn)
        def caller(*args, **kw):
            fakes = self.__enter__()
            if not isinstance(fakes, (tuple, list)):
                fakes = [fakes]
            args += tuple(fakes)
            value = None
            try:
                value = fn(*args, **kw)
            except:
                etype, val, tb = sys.exc_info()
                self.__exit__(etype, val, tb)
                raise etype, val, tb
            else:
                self.__exit__(None, None, None)
            return value
        return caller
    
    def __enter__(self):
        fudge.clear_expectations()
        fudge.clear_calls()
        self.patches = []
        all_fakes = []
        for path in self.obj_paths:
            try:
                target, attr = path.rsplit('.', 1)    
            except (TypeError, ValueError):
                raise TypeError(
                    "Need a valid target to patch. You supplied: %r"
                    % path)
            fake = fudge.Fake(path)
            all_fakes.append(fake)
            self.patches.append(patch_object(target, attr, fake))
        if len(all_fakes) == 1:
            return all_fakes[0]
        else:
            return all_fakes
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if not exc_type:
                fudge.verify()
        finally:
            for p in self.patches:
                p.restore()
            fudge.clear_expectations()


def with_patched_object(obj, attr_name, patched_value):
    """Decorator that patches an object before the decorated method 
    is called and restores it afterwards.
    
    This is a wrapper around :func:`fudge.patcher.patch_object`
    
    Example::
        
        >>> from fudge import with_patched_object
        >>> class Session:
        ...     state = 'clean'
        ... 
        >>> @with_patched_object(Session, "state", "dirty")
        ... def test():
        ...     print Session.state
        ... 
        >>> test()
        dirty
        >>> print Session.state
        clean
        
    """
    def patcher(method):
        @wraps(method)
        def method_call(*m_args, **m_kw):
            patched_obj = patch_object(obj, attr_name, patched_value)
            try:
                return method(*m_args, **m_kw)
            finally:
                patched_obj.restore()
        return method_call
    return patcher

class patched_context(object):
    """A context manager to patch an object temporarily during a `with statement`_ block.
        
    This is a wrapper around :func:`fudge.patcher.patch_object`
    
    .. lame, lame, cannot figure out how to apply __future__ to doctest 
       so this output is currently skipped
    
    .. doctest:: python25
        :options: +SKIP
        
        >>> from fudge import patched_context
        >>> class Session:
        ...     state = 'clean'
        ... 
        >>> with patched_context(Session, "state", "dirty"): # doctest: +SKIP
        ...     print Session.state
        ... 
        dirty
        >>> print Session.state
        clean
    
    .. _with statement: http://www.python.org/dev/peps/pep-0343/
        
    """
    def __init__(self, obj, attr_name, patched_value):
        
        # note that a @contextmanager decorator would be simpler 
        # but it can't be used since a value cannot be yielded within a 
        # try/finally block which is needed to restore the object on finally.
        
        self.patched_object = patch_object(obj, attr_name, patched_value)
    
    def __enter__(self):
        return self.patched_object
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.patched_object.restore()

def patch_object(obj, attr_name, patched_value):
    """Patches an object and returns an instance of :class:`fudge.patcher.PatchHandler` for later restoration.
    
    Note that if *obj* is not an object but a path to a module then it will be imported.
    
    You may want to use a more convenient wrapper :func:`with_patched_object` or :func:`patched_context`
    
    Example::
        
        >>> from fudge import patch_object
        >>> class Session:
        ...     state = 'clean'
        ... 
        >>> patched_session = patch_object(Session, "state", "dirty")
        >>> Session.state
        'dirty'
        >>> patched_session.restore()
        >>> Session.state
        'clean'
    
    Here is another example showing how to patch multiple objects at once::
        
        >>> class Session:
        ...     state = 'clean'
        ... 
        >>> class config:
        ...     session_strategy = 'database'
        ... 
        >>> patches = [
        ...     patch_object(config, "session_strategy", "filesystem"),
        ...     patch_object(Session, "state", "dirty")
        ... ]
        >>> try:
        ...     # your app under test would run here ...
        ...     print "(while patched)"
        ...     print "config.session_strategy=%r" % config.session_strategy
        ...     print "Session.state=%r" % Session.state
        ... finally:
        ...     for p in patches:
        ...         p.restore()
        ...     print "(patches restored)"
        (while patched)
        config.session_strategy='filesystem'
        Session.state='dirty'
        (patches restored)
        >>> config.session_strategy
        'database'
        >>> Session.state
        'clean'
        
    """
    if isinstance(obj, (str, unicode)):
        obj_path = adjusted_path = obj
        done = False
        exc = None
        while not done:
            try:
                obj = __import__(adjusted_path)
                done = True
            except ImportError:
                # Handle paths that traveerse object attributes.
                # Such as: smtplib.SMTP.connect
                #          smtplib <- module to import 
                adjusted_path = adjusted_path.rsplit('.', 1)[0]
                if not exc:
                    exc = sys.exc_info()
                if not adjusted_path.count('.'):
                    # We're at the top level module and it doesn't exist.
                    # Raise the first exception since it will make more sense:
                    etype, val, tb = exc
                    raise etype, val, tb
        for part in obj_path.split('.')[1:]:
            obj = getattr(obj, part)

    handle = PatchHandler(obj, attr_name)
    handle.patch(patched_value)
    return handle

class PatchHandler(object):
    """Low level patch handler that memorizes a patch so you can restore it later.
    
    You can use more convenient wrappers :func:`with_patched_object` and :func:`patched_context`
    
    .. note::
        
        This may produce unexpected results in a multi-threaded environment if you are 
        patching global module variables.
        
    """
    def __init__(self, orig_object, attr_name):
        self.orig_object = orig_object
        self.attr_name = attr_name
        self.proxy_object = None
        lock.acquire()
        try:
            self.orig_value = getattr(self.orig_object, self.attr_name)
        finally:
            lock.release()
    
    def patch(self, patched_value):
        """Set a new value for the attibute of the object."""
        lock.acquire()
        try:
            try:
                setattr(self.orig_object, self.attr_name, patched_value)
            except TypeError:
                proxy_name = 'fudge_proxy_%s_%s_%s' % (
                                    self.orig_object.__module__,
                                    self.orig_object.__name__,
                                    patched_value.__class__.__name__
                )
                self.proxy_object = type(proxy_name, (self.orig_object,), { 
                                            self.attr_name: patched_value })
                setattr(sys.modules[self.orig_object.__module__], 
                        self.orig_object.__name__, self.proxy_object)
        finally:
            lock.release()
        
    def restore(self):
        """Restore the saved value for the attribute of the object."""
        lock.acquire()
        try:
            if self.proxy_object is None:
                setattr(self.orig_object, self.attr_name, self.orig_value)
            else:
                setattr(sys.modules[self.orig_object.__module__], self.orig_object.__name__, self.orig_object)
        finally:
            lock.release()
