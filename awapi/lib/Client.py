# this only exists for the docs and is not really used

class Client(object):
    
    def __init__(self, *args, **kwargs):
        raise AssertionError("this class %s should never be called" % self.__class__)