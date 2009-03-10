
"""Exceptions used by the fudge module."""

__all__ = ['FakeDeclarationError']

class FakeDeclarationError(Exception):
    """Something wrong in how this :class:`fudge.Fake` was declared."""