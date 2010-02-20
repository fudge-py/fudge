# this exists so the doctest can import twython before fudging out its methods

def setup(*args, **kw):
    raise RuntimeError("Test failed to mock out this method")