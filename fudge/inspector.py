
"""Value inspectors that can be passed to :func:`fudge.Fake.with_args` for more
expressive argument matching.

As a mnemonic device,
an instance of the :class:`fudge.inspector.ValueInspector` is available as "arg" :

.. doctest::

    >>> import fudge
    >>> from fudge.inspector import arg
    >>> image = fudge.Fake("image").expects("save").with_args(arg.endswith(".jpg"))

In other words, this declares that the first argument to ``image.save()``
should end with the suffix ".jpg"

.. doctest::
    :hide:

    >>> fudge.clear_expectations()

"""
import warnings

from fudge.util import fmt_val, fmt_dict_vals

__all__ = ['arg', 'arg_not']

class ValueInspector(object):
    """Dispatches tests to inspect values.
    """

    invert_eq = False

    def _make_value_test(self, test_class, *args, **kwargs):
        if not self.invert_eq:
            return test_class(*args, **kwargs)
        class ValueTestInverter(test_class):
            def __repr__(wrapper_self):
                return "(NOT) %s" % test_class.__repr__(wrapper_self)
            def __eq__(wrapper_self, other):
                return not test_class.__eq__(wrapper_self, other)
        return ValueTestInverter(*args, **kwargs)

    def any(self):
        """Match any value.

        This is pretty much just a placeholder for when you
        want to inspect multiple arguments but don't care about
        all of them.

        .. doctest::

            >>> import fudge
            >>> from fudge.inspector import arg
            >>> db = fudge.Fake("db")
            >>> db = db.expects("transaction").with_args(
            ...             "insert", isolation_level=arg.any())
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

        The arg_not version will not match anything and is probably not very
        useful.

        .. doctest::

            >>> import fudge
            >>> from fudge.inspector import arg_not
            >>> query = fudge.Fake('query').expects_call().with_args(
            ...     arg_not.any()
            ... )
            >>> query('asdf')
            Traceback (most recent call last):
            ...
            AssertionError: fake:query((NOT) arg.any()) was called unexpectedly with args ('asdf')
            >>> query()
            Traceback (most recent call last):
            ...
            AssertionError: fake:query((NOT) arg.any()) was called unexpectedly with args ()

        .. doctest::
            :hide:

            >>> fudge.clear_expectations()

        """
        return self._make_value_test(AnyValue)

    def any_value(self):
        """**DEPRECATED**: use :func:`arg.any() <fudge.inspector.ValueInspector.any>`
        """
        warnings.warn('arg.any_value() is deprecated in favor of arg.any()',
                      DeprecationWarning, 3)
        return self.any()

    def contains(self, part):
        """Ensure that a value contains some part.

        This is useful for when you only care that a substring or subelement
        exists in a value.

        .. doctest::

            >>> import fudge
            >>> from fudge.inspector import arg
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

        arg_not.contains matches an argument not containing some element.

        .. doctest::

            >>> from fudge.inspector import arg_not
            >>> colorpicker = colorpicker.expects('select').with_args(arg_not.contains('blue'))
            >>> colorpicker.select('reddish')
            >>> colorpicker.select(['red', 'green'])
            >>> fudge.verify()

            >>> colorpicker.select('blue-green')
            Traceback (most recent call last):
            ...
            AssertionError: fake:colorpicker.select(arg.contains('red'))[0] was called unexpectedly with args ('blue-green')
            >>> colorpicker.select(['red', 'blue', 'green'])
            Traceback (most recent call last):
            ...
            AssertionError: fake:colorpicker.select((NOT) arg.contains('blue'))[1] was called unexpectedly with args (['red', 'blue', 'green'])

        .. doctest::
            :hide:

            >>> fudge.clear_expectations()

        """
        return self._make_value_test(Contains, part)

    def endswith(self, part):
        """Ensure that a value ends with some part.

        This is useful for when values with dynamic parts that are hard to replicate.

        .. doctest::

            >>> import fudge
            >>> from fudge.inspector import arg
            >>> tmpfile = fudge.Fake("tempfile").expects("mkname").with_args(
            ...                                             arg.endswith(".tmp"))
            ...
            >>> tmpfile.mkname("7AakkkLazUUKHKJgh908JKjlkh.tmp")
            >>> fudge.verify()

        .. doctest::
            :hide:

            >>> fudge.clear_expectations()

        The arg_not version works as expected, matching arguments that do not
        end with the given element.

        .. doctest::

            >>> from fudge.inspector import arg_not
            >>> query = fudge.Fake('query').expects_call().with_args(arg_not.endswith('Ringo'))
            >>> query('John, Paul, George and Steve')
            >>> fudge.verify()

        .. doctest::
            :hide:

            >>> fudge.clear_expectations()

        """
        return self._make_value_test(Endswith, part)

    def has_attr(self, **attributes):
        """Ensure that an object value has at least these attributes.

        This is useful for testing that an object has specific attributes.

        .. doctest::

            >>> import fudge
            >>> from fudge.inspector import arg
            >>> db = fudge.Fake("db").expects("update").with_args(arg.has_attr(
            ...                                                       first_name="Bob",
            ...                                                       last_name="James" ))
            ...
            >>> class User:
            ...     first_name = "Bob"
            ...     last_name = "James"
            ...     job = "jazz musician" # this is ignored
            ...
            >>> db.update(User())
            >>> fudge.verify()

        In case of error, the other object's __repr__ will be invoked:

        .. doctest::
            :hide:

            >>> fudge.clear_calls()

        .. doctest::

            >>> class User:
            ...     first_name = "Bob"
            ...
            ...     def __repr__(self):
            ...         return repr(dict(first_name=self.first_name))
            ...
            >>> db.update(User())
            Traceback (most recent call last):
            ...
            AssertionError: fake:db.update(arg.has_attr(first_name='Bob', last_name='James')) was called unexpectedly with args ({'first_name': 'Bob'})

        When called as a method on arg_not, has_attr does the opposite, and
        ensures that the argument does not have the specified attributes.

        .. doctest::

            >>> from fudge.inspector import arg_not
            >>> class User:
            ...     first_name = 'Bob'
            ...     last_name = 'Dobbs'
            >>> query = fudge.Fake('query').expects_call().with_args(
            ...     arg_not.has_attr(first_name='James')
            ... )
            >>> query(User())
            >>> fudge.verify()

        .. doctest::
            :hide:

            >>> fudge.clear_expectations()

        """
        return self._make_value_test(HasAttr, **attributes)

    def passes_test(self, test):
        """Check that a value passes some test.

        For custom assertions you may need to create your own callable
        to inspect and verify a value.

        .. doctest::

            >>> def is_valid(s):
            ...     if s in ('active','deleted'):
            ...         return True
            ...     else:
            ...         return False
            ...
            >>> import fudge
            >>> from fudge.inspector import arg
            >>> system = fudge.Fake("system")
            >>> system = system.expects("set_status").with_args(arg.passes_test(is_valid))
            >>> system.set_status("active")
            >>> fudge.verify()

        .. doctest::
            :hide:

            >>> fudge.clear_calls()

        The callable you pass takes one argument, the value, and should return
        True if it's an acceptable value or False if not.

        .. doctest::

            >>> system.set_status("sleep") # doctest: +ELLIPSIS
            Traceback (most recent call last):
            ...
            AssertionError: fake:system.set_status(arg.passes_test(<function is_valid at...)) was called unexpectedly with args ('sleep')

        .. doctest::
            :hide:

            >>> fudge.clear_expectations()

        If it makes more sense to perform assertions in your test function then
        be sure to return True :

            >>> def is_valid(s):
            ...     assert s in ('active','deleted'), (
            ...         "Unexpected status value: %s" % s)
            ...     return True
            ...
            >>> import fudge
            >>> from fudge.inspector import arg
            >>> system = fudge.Fake("system")
            >>> system = system.expects("set_status").with_args(arg.passes_test(is_valid))
            >>> system.set_status("sleep")
            Traceback (most recent call last):
            ...
            AssertionError: Unexpected status value: sleep

        .. doctest::
            :hide:

            >>> fudge.clear_expectations()

        Using the inverted version, arg_not.passes_test, asserts that the
        argument does not pass the provided test.

        .. doctest::

            >>> from fudge.inspector import arg_not
            >>> query = fudge.Fake('query').expects_call().with_args(
            ...     arg_not.passes_test(lambda x: x > 10)
            ... )
            >>> query(5)
            >>> fudge.verify()

        .. doctest::
            :hide:

            >>> fudge.clear_expectations()

        """
        return self._make_value_test(PassesTest, test)

    def isinstance(self, cls):
        """Check that a value is instance of specified class.

        .. doctest::

            >>> import fudge
            >>> from fudge.inspector import arg
            >>> system = fudge.Fake("system")
            >>> system = system.expects("set_status").with_args(arg.isinstance(str))
            >>> system.set_status("active")
            >>> fudge.verify()

        .. doctest::
            :hide:

            >>> fudge.clear_calls()

        Should return True if it's allowed class or False if not.

        .. doctest::

            >>> system.set_status(31337) # doctest: +ELLIPSIS
            Traceback (most recent call last):
            ...
            AssertionError: fake:system.set_status(arg.isinstance('str')) was called unexpectedly with args (31337)

        .. doctest::
            :hide:

            >>> fudge.clear_expectations()

        """
        return self._make_value_test(IsInstance, cls)


    def startswith(self, part):
        """Ensure that a value starts with some part.

        This is useful for when values with dynamic parts that are hard to replicate.

        .. doctest::

            >>> import fudge
            >>> from fudge.inspector import arg
            >>> keychain = fudge.Fake("keychain").expects("accept_key").with_args(
            ...                                                     arg.startswith("_key"))
            ...
            >>> keychain.accept_key("_key-18657yojgaodfty98618652olkj[oollk]")
            >>> fudge.verify()

        .. doctest::
            :hide:

            >>> fudge.clear_expectations()

        Using arg_not.startswith instead ensures that arguments do not start
        with that part.

        .. doctest::

            >>> from fudge.inspector import arg_not
            >>> query = fudge.Fake('query').expects_call().with_args(
            ...     arg_not.startswith('asdf')
            ... )
            >>> query('qwerty')
            >>> fudge.verify()

        .. doctest::
            :hide:

            >>> fudge.clear_expectations()

        """
        return self._make_value_test(Startswith, part)

class NotValueInspector(ValueInspector):
    """Inherits all the argument methods from ValueInspector, but inverts them
    to expect the opposite. See the ValueInspector method docstrings for
    examples.
    """

    invert_eq = True

    def __call__(self, thing):
        """This will match any value except the argument given.

        .. doctest::

            >>> import fudge
            >>> from fudge.inspector import arg, arg_not
            >>> query = fudge.Fake('query').expects_call().with_args(
            ...     arg.any(),
            ...     arg_not('foobar')
            ... )
            >>> query([1, 2, 3], 'asdf')
            >>> query('asdf', 'foobar')
            Traceback (most recent call last):
            ...
            AssertionError: fake:query(arg.any(), arg_not(foobar)) was called unexpectedly with args ('asdf', 'foobar')

        .. doctest::
            :hide:

            >>> fudge.clear_expectations()

        """
        return NotValue(thing)

arg = ValueInspector()
arg_not = NotValueInspector()

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
    arg_method = "any"

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

class PassesTest(ValueTest):
    arg_method = "passes_test"

    def __init__(self, test):
        self.test = test

    def __eq__(self, other):
        return self.test(other)

    def _repr_argspec(self):
        return self._make_argspec(repr(self.test))

class IsInstance(ValueTest):
    arg_method = "isinstance"

    def __init__(self, cls):
        self.cls = cls

    def __eq__(self, other):
        return isinstance(other, self.cls)

    def _repr_argspec(self):
        return self._make_argspec(repr(self.cls.__name__))

class NotValue(ValueTest):
    def __init__(self, item):
        self.item = item

    def __eq__(self, other):
        return not self.item == other

    def _repr_argspec(self):
        return "arg_not(%s)" % self.item
