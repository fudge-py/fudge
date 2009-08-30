
if (typeof nosejs !== "undefined") {
    nosejs.requireResource("jquery-1.3.1.js");
    nosejs.requireResource("jquery/qunit-testrunner.js");
    nosejs.requireFile("../fudge.js");
}

function raises(exception_name, func) {
    var caught = false;
    try {
        func();
    } catch (e) {
        caught = true;
        equals(e.name, exception_name, e);
    }
    if (!caught) {
        throw new fudge.AssertionError("expected to catch " + exception_name);
    }
}

function init_test() {
    fudge.registry.clear_all();
}
    
module("Test Fake");

test("Fake().toString", function() {
    equals(new fudge.Fake("something").toString(), "fake:something");
});

test("can find objects", function() {
    
    var fake;
    init_test();
    
    simple = {iam: function() { return "simple"; }};
    dot = {};
    dot.sep = {iam: function() { return "dot.sep"; }};
    
    fake = new fudge.Fake("simple");
    equals(fake._object.iam(), "simple");
    
    fake = new fudge.Fake("dot.sep");
    equals(fake._object.iam(), "dot.sep");
});

// this test made more sense when Fake used _object = eval(name)
/*
test("cannot send bad JavaScript as name", function() {
    init_test();
    expect(1);
    raises("TypeError", function() {
        var fake = new fudge.Fake("length()"); // TypeError: length is not a function
    });
});
*/

test("can create objects", function() {
    init_test();
    var fake = new fudge.Fake("_non_existant_.someCall");
    ok(_non_existant_, "_non_existant_");
    ok(_non_existant_.someCall, "_non_existant_.someCall");
});

test("expected call not called", function() {
    /*
    @raises(AssertionError)
    def test_nocall(self):
        exp = self.fake.expects('something')
        fudge.verify()
    */
    init_test();
    expect(1);
    var fake = new fudge.Fake("some_obj");
    fake.expects("someCall");
    raises("AssertionError", function() { 
        fudge.verify();
    });
});

test("call intercepted", function() {
    init_test();
    var fake = new fudge.Fake("bob_loblaw");
    fake.expects("blog");
    bob_loblaw.blog();
    // verify should pass the test...
    fudge.verify();
});

test("returns value", function() {
    init_test();
    var fake = new fudge.Fake("grocery_store");
    fake.expects("check_eggs").returns("eggs are good!");
    equals(grocery_store.check_eggs(), "eggs are good!");
    fudge.verify();
});

test("returns fake", function() {
    init_test();
    expect(1);
    var fake = new fudge.Fake("ice_skates");
    fake.expects("go").returns_fake().expects("not_called");
    ice_skates.go();
    raises("AssertionError", function() { 
        fudge.verify();
    });
});

test("returns fake creates calls", function() {
    init_test();
    var fake = new fudge.Fake("ice_skates").expects("foo").returns_fake().expects("bar");
    ice_skates.foo().bar();
});

test("returns fake maintains expectations", function() {
    init_test();
    var fake = new fudge.Fake("ice_skates");
    fake.expects("go").returns_fake().expects("show_off");
    ice_skates.go().show_off();
    fudge.verify();
});

test("expected arguments are set", function() {
    init_test(); 
    fudge.clear_expectations();
    var fake = new fudge.Fake("Session").expects("add").with_args("one", {"debug":false});
    var call = fudge.registry.expected_calls[0];
    equals(call.expected_arguments[0], "one");
    equals(call.expected_arguments[1].debug, false);
});

test("expected arguments raises error", function() {
    init_test(); 
    fudge.clear_expectations();
    fudge.clear_calls();
    var fake = new fudge.Fake("session").expects("add").with_args("one", {"debug":false});
    raises("AssertionError", function() { 
        session.add();
    });
});

test("expected arguments pass", function() {
    init_test(); 
    fudge.clear_expectations();
    fudge.clear_calls();
    console.log("arg test");
    var fake = new fudge.Fake("session").expects("add").with_args("one", {"debug":false});
    session.add("one", {"debug":false});
});

module("Test ExpectedCall");

test("ExpectedCall properties", function() {
    init_test();
    var fake = new fudge.Fake("my_auth_mod");
    var ec = new fudge.ExpectedCall(fake, "logout");
    equals(ec.call_name, "logout");
});

test("call is logged", function() {
    init_test();
    var fake = new fudge.Fake("aa_some_obj");
    var ec = new fudge.ExpectedCall(fake, "watchMe");
    aa_some_obj.watchMe();
    equals(ec.was_called, true, "aa_some_obj.watchMe() was not logged");
});

module("Test fudge.registry");

/*
    def setUp(self):
        self.fake = Fake()
        self.reg = fudge.registry
        # in case of error, clear out everything:
        self.reg.clear_all()
*/

test("expected call not called", function() {
    /*
    @raises(AssertionError)
    def test_expected_call_not_called(self):
        self.reg.clear_calls()
        self.reg.expect_call(ExpectedCall(self.fake, 'nothing'))
        self.reg.verify()
    */
    init_test();
    expect(1);
    var fake = new fudge.Fake("some_obj");
    fudge.registry.expect_call(new fudge.ExpectedCall(fake, 'nothing'));
    raises("AssertionError", function() { 
        fudge.registry.verify();
    });
});

test("start resets calls", function() {
    /*     
    def test_start_resets_calls(self):
        exp = ExpectedCall(self.fake, 'callMe')
        self.reg.expect_call(exp)
        exp()
        eq_(exp.was_called, True)
        
        self.reg.clear_calls()
        eq_(exp.was_called, False, "call was not reset by start()")
    */
    init_test();
    var fake = new fudge.Fake("yeah");
    var exp = new fudge.ExpectedCall(fake, "sayYeah");
    fudge.registry.expect_call(exp);
    yeah.sayYeah();
    equals(exp.was_called, true, "call was never logged");
    fudge.registry.clear_calls();
    equals(exp.was_called, false, "call was not reset by clear_calls()");
});

test("verify resets calls", function() {
    init_test();
    var fake = new fudge.Fake("reset_yeah");
    var exp = new fudge.ExpectedCall(fake, "sayYeah");
    fudge.registry.expect_call(exp);
    equals(fudge.registry.expected_calls.length, 1, "registry has too many calls");
    reset_yeah.sayYeah();
    equals(exp.was_called, true, "call was never logged");
    
    fudge.registry.verify();
    equals(exp.was_called, false, "call was not reset by verify()");
    equals(fudge.registry.expected_calls.length, 1, "verify() should not reset expectations");
});

test("global verify", function() {
    init_test();
    var fake = new fudge.Fake("gverify_yeah");
    var exp = new fudge.ExpectedCall(fake, "sayYeah");
    gverify_yeah.sayYeah();
    fudge.registry.expect_call(exp);
    equals(exp.was_called, true, "call was never logged");
    equals(fudge.registry.expected_calls.length, 1, "registry has wrong number of calls");
    
    fudge.verify();
    
    equals(exp.was_called, false, "call was not reset by verify()");
    equals(fudge.registry.expected_calls.length, 1, "verify() should not reset expectations");
});

test("global clear expectations", function() {  
    /* 
    def test_global_clear_expectations(self):
        exp = ExpectedCall(self.fake, 'callMe')
        exp()
        self.reg.expect_call(exp)
        eq_(len(self.reg.get_expected_calls()), 1)
        
        fudge.clear_expectations()
        
        eq_(len(self.reg.get_expected_calls()), 0, 
            "clear_expectations() should reset expectations")
    */
    init_test();
    var fake = new fudge.Fake("gclear_yeah");
    var exp = new fudge.ExpectedCall(fake, "sayYeah");
    gclear_yeah.sayYeah();
    fudge.registry.expect_call(exp);
    equals(fudge.registry.expected_calls.length, 1, "registry has wrong number of calls");
    
    fudge.clear_expectations();
    
    equals(fudge.registry.expected_calls.length, 0, "clear_expectations() should reset expectations");
});

module("utilities");

test("reproduce call args", function() {
    equals(fudge.repr_call_args(new Array("yeah's", {debug:true, when:'now'})), 
            "('yeah\\'s', {'debug': true, 'when': 'now'})");
});
