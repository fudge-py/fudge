
__all__ = ['patch_object', 'with_patched_object', 'PatchHandler'] # patched_context, see below

from fudge.util import wraps

def patch_object(obj, attr_name, patched_value):
    """Patches an object and returns an instance of :class:`fudge.PatchHandler` for later restoration.
    
    Note that if *obj* is not an object but a path to a module then it will be imported.
    
    You can use more convenient wrappers :func:`with_patched_object` and :func:`patched_context`
    """
    if isinstance(obj, (str, unicode)):
        obj_path = obj
        obj = __import__(obj_path)
        for part in obj_path.split('.')[1:]:
            obj = getattr(obj, part)

    handle = PatchHandler(obj, attr_name)
    handle.patch(patched_value)
    return handle

try:
    from contextlib import contextmanager
except ImportError:
    pass
else:
    # in 2.5+
    @contextmanager
    def patched_context(obj, attr_name, patched_value):
        """A context manager to execute :func:`fudge.patch_object` in a `with statement`_
        
        Example::
            
            >>> class Session:
            ...     state = 'clean'
            ... 
            >>> with patched_context(Session, "state", "dirty"):
            ...     print Session.state
            ... 
            dirty
            >>> print Session.state
            clean
        
        .. _with statement: http://www.python.org/dev/peps/pep-0343/
            
        """
        patched_object = patch_object(obj, attr_name, patched_value)
        try:
            yield patched_object
        finally:
            patched_object.restore()

    __all__.append('patched_context')

def with_patched_object(obj, attr_name, patched_value):
    """Decorator that patches an object before method() and restores it afterwards.
    
    Example::
        
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

class PatchHandler(object):
    """Low level patch handler that memorizes a patch so you can restore it later.
    
    You can use more convenient wrappers :func:`with_patched_object` and :func:`patched_context`
    """
    def __init__(self, orig_object, attr_name):
        self.orig_object = orig_object
        self.attr_name = attr_name
        self.orig_value = getattr(self.orig_object, self.attr_name)
    
    def patch(self, patched_value):
        """Set a new value for the attibute of the object."""
        setattr(self.orig_object, self.attr_name, patched_value)
        
    def restore(self):
        """Restore the saved value for the attribute of the object."""
        setattr(self.orig_object, self.attr_name, self.orig_value)
