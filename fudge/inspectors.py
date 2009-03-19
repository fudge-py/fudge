
from fudge.util import fmt_val, fmt_dict_vals

class ValueTest(object):
    
    def __eq__(self, other):
        raise NotImplementedError()

class Startswith(ValueTest):
    
    def __init__(self, part):
        self.part = part
        
    def _repr_argspec(self):
        return "arg.startswith(" + fmt_val(self.part) + ")"
        
    __str__ = _repr_argspec
    __unicode__ = _repr_argspec
    __repr__ = _repr_argspec
    
    def stringlike(self, value):
        if isinstance(value, (str, unicode)):
            return value
        else:
            return str(value)
    
    def __eq__(self, other):
        return self.stringlike(other).startswith(self.part)
    
class ValueInspector(object):
    
    def startswith(self, part):
        return Startswith(part)

arg = ValueInspector()
        