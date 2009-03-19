
from fudge.util import fmt_val, fmt_dict_vals

__all__ = ['arg']

class ValueTest(object):
    
    arg_method = None
    __test__ = False # nose
    
    def __eq__(self, other):
        raise NotImplementedError()
    
    def _repr_argspec(self):
        raise NotImplementedError()
    
    def __str__(self):
        return self._repr_argspec()
    
    def __unicode__(self):
        return self._repr_argspec()
    
    def __repr__(self):
        return self._repr_argspec()
    
    def _make_argspec(self, arg):
        if self.arg_method is None:
            raise NotImplementedError(
                "%r must have set attribute arg_method" % self.__class__)
        return "arg." + self.arg_method + "(" + arg + ")"

class Stringlike(ValueTest):
    
    def __init__(self, part):
        self.part = part
        
    def _repr_argspec(self):
        return self._make_argspec(fmt_val(self.part))
    
    def stringlike(self, value):
        if isinstance(value, (str, unicode)):
            return value
        else:
            return str(value)
    
    def __eq__(self, other):
        check_stringlike = getattr(self.stringlike(other), self.arg_method)
        return check_stringlike(self.part)

class Startswith(Stringlike):
    arg_method = "startswith"
    
class Endswith(Stringlike):
    arg_method = "endswith"

class HasAttr(ValueTest):
    arg_method = "has_attr"
    
    def __init__(self, **attributes):
        self.attributes = attributes
        
    def _repr_argspec(self):
        return self._make_argspec(", ".join(sorted(fmt_dict_vals(self.attributes))))
    
    def __eq__(self, other):
        for name, value in self.attributes.items():
            if not hasattr(other, name):
                return False
            if getattr(other, name) != value:
                return False
        
        return True

class AnyValue(ValueTest):
    arg_method = "any_value"
    
    def __eq__(self, other):
        # will match anything:
        return True
        
    def _repr_argspec(self):
        return self._make_argspec("")
    
    
class ValueInspector(object):
    
    def any_value(self):
        return AnyValue()
    
    def has_attr(self, **attributes):
        return HasAttr(**attributes)
    
    def endswith(self, part):
        return Endswith(part)
    
    def startswith(self, part):
        return Startswith(part)

arg = ValueInspector()
        