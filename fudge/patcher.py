
__all__ = ['patch_object', 'with_patched_object']

from fudge.util import wraps

def patch_object(obj, attr_name, patched_value):
    if isinstance(obj, (str, unicode)):
        obj_path = obj
        obj = __import__(obj_path)
        for part in obj_path.split('.')[1:]:
            obj = getattr(obj, part)

    handle = PatchHandler(obj, attr_name)
    handle.patch(patched_value)
    return handle

def with_patched_object(obj, attr_name, patched_value):
    """Decorator that patches an object before method() and restores it afterwards."""
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
    def __init__(self, orig_object, attr_name):
        self.orig_object = orig_object
        self.attr_name = attr_name
        self.orig_value = getattr(self.orig_object, self.attr_name)
    
    def patch(self, patched_value):
        setattr(self.orig_object, self.attr_name, patched_value)
        
    def restore(self):
        setattr(self.orig_object, self.attr_name, self.orig_value)