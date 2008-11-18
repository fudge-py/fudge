
__all__ = ['patch_object']

def patch_object(obj, attr_name, patched_value):
    handle = PatchHandler(obj, attr_name)
    handle.patch(patched_value)
    return handle

class PatchHandler(object):
    def __init__(self, orig_object, attr_name):
        self.orig_object = orig_object
        self.attr_name = attr_name
        self.orig_value = getattr(self.orig_object, self.attr_name)
    
    def patch(self, patched_value):
        setattr(self.orig_object, self.attr_name, patched_value)
        
    def restore(self):
        setattr(self.orig_object, self.attr_name, self.orig_value)