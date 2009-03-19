
from nose.tools import eq_, raises
import unittest
import fudge
from fudge import inspectors
from fudge.inspectors import arg
from fudge import Fake

class TestArgs(unittest.TestCase):
    
    def tearDown(self):
        fudge.clear_expectations()
    
    def test_endswith_ok(self):
        db = Fake("db").expects("execute").with_args(arg.endswith("values (1,2,3,4)"))
        db.execute("insert into foo values (1,2,3,4)")
    
    def test_endswith_ok_uni(self):
        db = Fake("db").expects("execute").with_args(arg.endswith(u"Ivan Krsti\u0107"))
        db.execute(u"select Ivan Krsti\u0107")
    
    def test_any_value(self):
        db = Fake("db").expects("execute").with_args(arg.anyvalue())
        db.execute("delete from foo where 1")

class TestObjectlike(unittest.TestCase):
    
    def tearDown(self):
        fudge.clear_expectations()
    
    def test_has_attr(self):
        class Config(object):
            size = 12
            color = 'red'
            weight = 'heavy'
            
        widget = Fake("widget").expects("configure")\
                               .with_args(arg.has_attr(size=12,color='red'))
        widget.configure(Config())
    
    def test_objectlike_str(self):
        o = inspectors.HasAttr(one=1, two="two")
        eq_(str(o), "arg.has_attr(one=1, two='two')")
    
    def test_objectlike_repr(self):
        o = inspectors.HasAttr(one=1, two="two")
        eq_(str(o), "arg.has_attr(one=1, two='two')")
    
    def test_objectlike_unicode(self):
        o = inspectors.HasAttr(one=1, ivan=u"Ivan_Krsti\u0107")
        eq_(str(o), "arg.has_attr(ivan=u'Ivan_Krsti\\u0107', one=1)")

class TestStringlike(unittest.TestCase):
    
    def tearDown(self):
        fudge.clear_expectations()
    
    def test_startswith_ok(self):
        db = Fake("db").expects("execute").with_args(arg.startswith("insert into"))
        db.execute("insert into foo values (1,2,3,4)")
    
    @raises(AssertionError)
    def test_startswith_fail(self):
        db = Fake("db").expects("execute").with_args(arg.startswith("insert into"))
        db.execute("select from")
    
    def test_startswith_ok_uni(self):
        db = Fake("db").expects("execute").with_args(arg.startswith(u"Ivan_Krsti\u0107"))
        db.execute(u"Ivan_Krsti\u0107(); foo();")
    
    def test_startswith_unicode(self):
        p = inspectors.Startswith(u"Ivan_Krsti\u0107")
        eq_(unicode(p), "arg.startswith(u'Ivan_Krsti\u0107')")
        
    def test_endswith_unicode(self):
        p = inspectors.Endswith(u"Ivan_Krsti\u0107")
        eq_(unicode(p), "arg.endswith(u'Ivan_Krsti\u0107')")
    
    def test_startswith_repr(self):
        p = inspectors.Startswith("_start")
        eq_(repr(p), "arg.startswith('_start')")
    
    def test_endswith_repr(self):
        p = inspectors.Endswith("_ending")
        eq_(repr(p), "arg.endswith('_ending')")
    
    def test_startswith_str(self):
        p = inspectors.Startswith("_start")
        eq_(str(p), "arg.startswith('_start')")
    
    def test_endswith_str(self):
        p = inspectors.Endswith("_ending")
        eq_(str(p), "arg.endswith('_ending')")
    
    def test_startswith_str_long_value(self):
        p = inspectors.Startswith(
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        )
        eq_(str(p), 
            "arg.startswith('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA...')" )
    
    def test_endswith_str_long_value(self):
        p = inspectors.Endswith(
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        )
        eq_(str(p), 
            "arg.endswith('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA...')" )
    
        