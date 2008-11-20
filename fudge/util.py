
try:
    from functools import wraps
except ImportError:
    # for python < 2.5... this is a limited set of what we need to do
    # with a wrapped function :
    def wraps(f):
        def wrap_with_f(new_f):
            new_f.__name__ = f.__name__
            if hasattr(f, '__module__'):
                new_f.__module__ = f.__module__
            return new_f
        return wrap_with_f