
from nose.tools import eq_
import unittest
import fudge
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
        
    def test_endswith_not_str(self):
        class unstringable(object):
            def __str__():
                raise TypeError()
            
        db = Fake("db").expects("execute").with_args(arg.endswith("_ending"))
        db.execute(unstringable)
    
    def test_startswith_ok(self):
        db = Fake("db").expects("execute").with_args(arg.startswith("insert into"))
        db.execute("insert into foo values (1,2,3,4)")
    
    def test_startswith_ok_uni(self):
        db = Fake("db").expects("execute").with_args(arg.startswith(u"Ivan_Krsti\u0107"))
        db.execute(u"Ivan_Krsti\u0107(); foo();")
    
    def test_any_value(self):
        db = Fake("db").expects("execute").with_args(arg.anyvalue())
        db.execute("delete from foo where 1")
        
    def test_has_attr(self):
        class Config(object):
            size = 12
            color = 'red'
            weight = 'heavy'
            
        widget = Fake("widget").expects("configure")\
                               .with_args(arg.has_attr(size=12,color='red'))
        widget.configure(Config())
        