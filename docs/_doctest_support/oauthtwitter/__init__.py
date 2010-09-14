# this exists so the doctest can import oauthtwitter before fudging out its methods

def OAuthApi(*args, **kw):
    raise RuntimeError("Test failed to mock out this method")