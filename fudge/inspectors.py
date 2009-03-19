
class ValueTest(object):
    
    def __eq__(self, other):
        raise NotImplementedError()

class Startswith(ValueTest):
    
    def __init__(self, part):
        self.part = part
    
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
        