
"""Value inspectors.

These inspectors can be passed to :func:`fudge.Fake.with_args` for more 
expressive argument matching.  As a pneumonic device, 
an instance of the :class:`fudge.inspector.ValueInspector` is available as "args" :

.. doctest::
    
    >>> import fudge
    >>> from fudge.inspectors import arg
    >>> image = fudge.Fake("image").expects("save").with_args(arg.endswith(".jpg"))
    
.. doctest::
    :hide:
    
    >>> fudge.clear_expectations()

"""

from fudge.util import fmt_val, fmt_dict_vals

__all__ = ['arg']

class ValueInspector(object):
    """Dispatches tests to inspect values. 
    
    An instance of this class is available as a singleton::
        
        >>> from fudge.inspectors import arg
    
    """
    
    def any_value(self):
        """Return test that matches any value.
        
        This is pretty much just a placeholder for when you 
        want to inspect multiple arguments but don't care about 
        all of them.
        
        .. doctest::
            
            >>> import fudge
            >>> from fudge.inspectors import arg
            >>> db = fudge.Fake("db")
            >>> db = db.expects("transaction").with_args(
            ...             "insert", isolation_level=arg.any_value())
            ... 
            >>> db.transaction("insert", isolation_level="lock")
            >>> fudge.verify()
        
        This also passes:
        
        .. doctest::
            :hide:
            
            >>> fudge.clear_calls()
            
        .. doctest::
        
            >>> db.transaction("insert", isolation_level="autocommit")
            >>> fudge.verify()
        
        .. doctest::
            :hide:
            
            >>> fudge.clear_expectations()
        
        """
        return AnyValue()
    
    def contains(self, part):
        """Return test if part in value.
        
        This is useful for when you just care that a substring or subelement 
        exists in a value.
        
        .. doctest::
            
            >>> import fudge
            >>> from fudge.inspectors import arg
            >>> addressbook = fudge.Fake().expects("import_").with_args(
            ...                                     arg.contains("Baba Brooks"))
            ... 
            >>> addressbook.import_("Bill Brooks; Baba Brooks; Henry Brooks;")
            >>> fudge.verify()
        
        .. doctest::
            :hide:
            
            >>> fudge.clear_expectations()
        
        Since contains() just invokes the __in__() method, checking that a list 
        item is present works as expected :
        
        .. doctest::
            
            >>> colorpicker = fudge.Fake("colorpicker")
            >>> colorpicker = colorpicker.expects("select").with_args(arg.contains("red"))
            >>> colorpicker.select(["green","red","blue"])
            >>> fudge.verify()
        
        .. doctest::
            :hide:
            
            >>> fudge.clear_expectations()
            
        """
        return Contains(part)
    
    def has_attr(self, **attributes):
        """Return test to assert the value is an argument with said arguments.
        
        This is useful for when a value can be an object but you only 
        need to test that the object has specific attributes.
        
        .. doctest::
            
            >>> import fudge
            >>> from fudge.inspectors import arg
            >>> db = fudge.Fake("db").expects("update").with_args(arg.has_attr(
            ...                                                 first_name="Bob",
            ...                                                 last_name="James" ))
            ... 
            >>> class User:
            ...     first_name = "Bob"
            ...     last_name = "James"
            ...     job = "jazz musician"
            ... 
            >>> db.update(User())
            >>> fudge.verify()
        
        In case of error, the object will be reproduced:
        
        .. doctest::
            :hide:
            
            >>> fudge.clear_calls()
        
        .. doctest::
            
            >>> class User:
            ...     first_name = "Bob"
            ... 
            ...     def __repr__(self):
            ...         return str(dict(first_name=self.first_name))
            ... 
            >>> db.update(User())
            Traceback (most recent call last):
            ...
            AssertionError: fake:db.update(arg.has_attr(first_name='Bob', last_name='James')) was called unexpectedly with args ({'first_name': 'Bob'})
            
            
        .. doctest::
            :hide:
            
            >>> fudge.clear_expectations()
            
        """
        return HasAttr(**attributes)
    
    def endswith(self, part):
        """Return test to assert the value ends with a string.
        
        This is useful for when values with dymaic parts that are hard to replicate.
        
        .. doctest::
            
            >>> import fudge
            >>> from fudge.inspectors import arg
            >>> tmpfile = fudge.Fake("tempfile").expects("mkname").with_args(
            ...                                             arg.endswith(".tmp"))
            ... 
            >>> tmpfile.mkname("7AakkkLazUUKHKJgh908JKjlkh.tmp")
            >>> fudge.verify()
            
        .. doctest::
            :hide:
            
            >>> fudge.clear_expectations()
            
        """
        return Endswith(part)
    
    def startswith(self, part):
        """Return test to assert the value starts with a string.
        
        This is useful for when values with dymaic parts that are hard to replicate.
        
        .. doctest::
            
            >>> import fudge
            >>> from fudge.inspectors import arg
            >>> keygen = fudge.Fake("keygen").expects("generate").with_args(
            ...                                             arg.startswith("_key"))
            ... 
            >>> keygen.generate("_key-18657yojgaodfty98618652olkj[oollk]")
            >>> fudge.verify()
            
        .. doctest::
            :hide:
            
            >>> fudge.clear_expectations()
            
        """
        return Startswith(part)

arg = ValueInspector()

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

class Contains(ValueTest):
    arg_method = "contains"
    
    def __init__(self, part):
        self.part = part
    
    def _repr_argspec(self):
        return self._make_argspec(fmt_val(self.part))
    
    def __eq__(self, other):
        if self.part in other:
            return True
        else:
            return False
        