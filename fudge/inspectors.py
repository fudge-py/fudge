
from fudge.util import fmt_val, fmt_dict_vals

__all__ = ['arg']

class ValueTest(object):
    
    __test__ = False # nose
    
    def __eq__(self, other):
        raise NotImplementedError()

class Stringlike(ValueTest):
    
    def __init__(self, part):
        self.part = part
        
    def _repr_argspec(self):
        return "arg." + self.str_method + "(" + fmt_val(self.part) + ")"
        
    __str__ = _repr_argspec
    __unicode__ = _repr_argspec
    __repr__ = _repr_argspec
    
    def stringlike(self, value):
        if isinstance(value, (str, unicode)):
            return value
        else:
            return str(value)
    
    def __eq__(self, other):
        check_stringlike = getattr(self.stringlike(other), self.str_method)
        return check_stringlike(self.part)

class Startswith(Stringlike):
    str_method = "startswith"
    
class Endswith(Stringlike):
    str_method = "endswith"
    
class ValueInspector(object):
    
    def endswith(self, part):
        return Endswith(part)
    
    def startswith(self, part):
        return Startswith(part)

arg = ValueInspector()
        