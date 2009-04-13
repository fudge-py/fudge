
/**
 * Fudge is a JavaScript module for using fake objects (mocks, stubs, etc) to test real ones.
 * <p>
 * The module is designed for two specific situations:
 * </p>
 * <ul>
 * <li>Replace an object
 *   <ul>
 *   <li>
 *   Temporarily return a canned value for a 
 *     method or allow a method to be called without affect.
 *   </li>
 *   </ul>
 * </li>
 * <li>Ensure an object is used correctly
 *   <ul>
 *   <li>
 *     Declare expectations about what methods should be 
 *     called and what arguments should be sent.
 *   </li>
 *   </ul>
 * </li>
 * </ul>
 * @module fudge
 */

fudge = function() {
    
    var AssertionError = function(msg) {
        Error.call(this, msg);
        this.name = "AssertionError";
        this.message = msg;
    };
    AssertionError.prototype.toString = function() { return this.message; };

    var registry = new function() {
    
        this.expected_calls = [];
    
        this.clear_actual_calls = function() {
            /*            
            def clear_actual_calls(self):
                for exp in self.get_this.expected_calls():
                    exp.was_called = False
            */
            for (var i=0; i<this.expected_calls.length; i++) {
                var exp = this.expected_calls[i];
                exp.was_called = false;
            }
        };
    
        this.clear_all = function() {
            /*            
            def clear_all(self):
                self.clear_actual_calls()
                self.clear_expectations()
            */
            this.clear_actual_calls();
            this.clear_expectations();
        };
    
        this.clear_expectations = function() {
            /*            
            def clear_expectations(self):
                c = self.get_this.expected_calls()
                c[:] = []
            */
            this.expected_calls = [];
        };
        
        this.clear_calls = function() {
            this.clear_actual_calls();
        };
    
        this.verify = function() {
            for (var i=0; i<this.expected_calls.length; i++) {
                var exp = this.expected_calls[i];
                try {
                    exp.assert_called();
                } catch (e) {
                    this.clear_actual_calls();
                    throw(e);
                }
            }
            this.clear_actual_calls();
        };
    
        this.expect_call = function(expected_call) {
            /*
            def expect_call(self, expected_call):
                c = self.get_this.expected_calls()
                c.append(expected_call)
            */
            this.expected_calls.push(expected_call);
        };
    };
    
    var args_are_equal = function(array, test_array) {
        if (array.length != test_array.length) {
            return false;
        }
        for (var i = 0; i < test_array.length; i++) {
            var val = array[i];
            var test_val = test_array[i];
            
            switch (typeof val) {
                case "object":
                    for (var k in val) {
                        if (test_val[k] === 'undefined' || test_val[k] !== val[k]) {
                            return false;
                        }
                    }
                    for (var k in test_val) {
                        if (val[k] === 'undefined' || val[k] !== test_val[k]) {
                            return false;
                        }
                    }
                    break;
                case "string":
                default:
                    if ( val !== test_val) {
                        return false;
                    }
                    break;
            }
        }
        return true;
    };

    var AnyCall = function(fake, call_name) {
        /*
        class Call(object):
            """A call that can be made on a Fake object.
    
            You do not need to use this directly, use Fake.provides(...), etc
            """
        */
        this.fake = fake;
        this.call_name = call_name;
        this.call_replacement = null;
        this.expected_arguments = null;
        this.expected_arg_count = null;
        this.expected_kwarg_count = null;
        this.return_val = null;
        this.was_called = false;
    
        var expector = this;
        this.fake._object[call_name] = function() {
            expector.was_called = true;
            if (expector.expected_arguments !== null) {
                
                if ( ! args_are_equal(arguments, expector.expected_arguments) ) {
                    throw(new AssertionError(
                                expector.fake + 
                                " was called unexpectedly with arguments: " + 
                                repr_call_args(arguments) + 
                                " -- expected: " + repr_call_args(expector.expected_arguments)));
                }
            }
            return expector.return_val;
        };
    };

    AnyCall.prototype.__call__ = function() {
        /*
        def __call__(self, *args, **kwargs):
            self.was_called = True
            if self.call_replacement:
                return self.call_replacement(*args, **kwargs)
            
            if self.expected_args:
                if args != self.expected_args:
                    raise AssertionError(
                        "%s was called unexpectedly with args %s" % (self, args))
            elif self.expected_arg_count is not None:
                if len(args) != self.expected_arg_count:
                    raise AssertionError(
                        "%s was called with %s arg(s) but expected %s" % (
                            self, len(args), self.expected_arg_count))
                    
            if self.expected_kwargs:
                if kwargs != self.expected_kwargs:
                    raise AssertionError(
                        "%s was called unexpectedly with keyword args %s" % (
                                    self, ", ".join(fmt_dict_vals(kwargs))))
            elif self.expected_kwarg_count is not None:
                if len(kwargs.keys()) != self.expected_kwarg_count:
                    raise AssertionError(
                        "%s was called with %s keyword arg(s) but expected %s" % (
                            self, len(kwargs.keys()), self.expected_kwarg_count))
        
            return self.return_val
        */
    };

     // can be called, but doesn't do anything
    AnyCall.prototype.assert_called = function() {};

    var ExpectedCall = function(fake, call_name) {
        AnyCall.call(this, fake, call_name);
    };

    ExpectedCall.prototype.assert_called = function() {
        /*
        def assert_called(self):
            if not self.was_called:
                raise AssertionError("%s was not called" % (self))
        */
        if (!this.was_called) {
            throw(new AssertionError(this.fake._name + "." + this.call_name + "() was not called"));
        }
    };
    
    var fmt_val = function(val) {
        switch (typeof val) {
            case "object":
                // i.e. {'debug': true, 'throttle': 1}
                var f_val = "{";
                var f_last_key = null;
                for (var k in val) {
                    if (f_last_key !== null) {
                        f_val += ", ";
                    }
                    f_val += fmt_val(k) + ": " + fmt_val(val[k]);
                    f_last_key = k;
                }
                f_val += "}";
                val = f_val;
                break;
            case "string":
                // i.e. 'yeah\'s'
                val = "'" + val.replace("'","\\'") + "'";
                break
            default:
                break;
        }
        return val;
    }
    
    var repr_call_args = function(call_args) {
        var call = "(";
        var last = null;
        for (var i=0; i<call_args.length; i++) {
            if (last !== null) {
                call += ", ";
            }
            var arg = fmt_val(call_args[i]);
            call += arg;
            last = arg;
        }
        call += ")";
        return call;
    };

    /**
     * <p>
       A fake object to replace a real one while testing.
       </p>
       <p>
       All calls return ``this`` so that you can chain them together to 
       create readable code.
       </p>
       <p>
       Arguments:
       </p>
       <ul>
       <li>name
       <ul><li>
            Name of the JavaScript global to replace.
            </li></ul>
       </li>
       <li>config.allows_any_call = false
       <ul><li>
            When True, any method is allowed to be called on the Fake() instance.  Each method 
            will be a stub that does nothing if it has not been defined.  Implies callable=True.
           </li></ul>
       </li>
       <li>config.callable = false
       <ul><li>
            When True, the Fake() acts like a callable.  Use this if you are replacing a single 
            method.
            </li></ul>
       </li>
       </ul>
       <p>
       Short example:
       </p>
       <pre><code>
       var auth = new fudge.Fake('auth')
                                .expects('login')
                                .with_args('joe_username', 'joes_password');
       fudge.clear_calls();
       auth.login();
       fudge.verify();
       </code></pre>
     * 
     * @class Fake
     * @namespace fudge
     */
    var Fake = function(name, config) {
        if (!config) {
            config = {};
        }
        this._name = name;
        
        if (config.object) {
            this._object = config.object;
        } else {
            // object is a global by name
            if (name) {
                var parts = name.split(".");
                if (parts.length === 0) {
                    // empty string?
                    throw new Error("Fake('" + name + "'): invalid name");
                }   
                // descend into dot-separated object.
                //  i.e.
                //  foo.bar.baz
                //      window[foo]
                //      foo[bar]
                //      baz
                var last_parent = window;
                for (var i=0; i<parts.length; i++) {
                    var new_part = parts[i];
                    if (!last_parent[new_part]) {
                        // lazily create mock objects that don't exist:
                        last_parent[new_part] = {};
                    }
                    last_parent = last_parent[new_part];
                }
                this._object = last_parent;
    
                if (!this._object) {
                    throw new Error(
                        "Fake('" + name + "'): name must be the name of a " + 
                        "global variable assigned to window (it is: " + this._object + ")");
                }
            } else {
                throw new Error("Can only call Fake(name) or Fake({object: object})")
            }
        }
    
        this._declared_calls = {};
        this._last_declared_call_name = null;
        this._allows_any_call = config.allows_any_call;
        this._stub = null;
        this._callable = config.callable || config.allows_any_call;
    };
    
    Fake.prototype.toString = function() {
        return "fake:" + this._name;
    };

    Fake.prototype.__getattr__ = function(name) {
        /*
        def __getattr__(self, name):
            if name in self._declared_calls:
                return self._declared_calls[name]
            else:
                if self._allows_any_call:
                    return Call(self, call_name=name)
                raise AttributeError("%s object does not allow call or attribute '%s'" % (
                                        self, name))
        */
    };

    Fake.prototype.__call__ = function() {
        /*
        def __call__(self, *args, **kwargs):
            if '__init__' in self._declared_calls:
                # special case, simulation of __init__():
                call = self._declared_calls['__init__']
                call(*args, **kwargs)
                return self
            elif self._callable:
                # go into stub mode:
                if not self._stub:
                    self._stub = Call(self)
                call = self._stub
                return call(*args, **kwargs)
            else:
                raise RuntimeError("%s object cannot be called (maybe you want %s(callable=True) ?)" % (
                                                                            self, self.__class__.__name__))
        */
    };

    Fake.prototype._get_current_call = function() {
        /*
        def _get_current_call(self):
            if not self._last_declared_call_name:
                if not self._stub:
                    self._stub = Call(self)
                return self._stub
            exp = self._declared_calls[self._last_declared_call_name]
            return exp
        */
        if (!this._last_declared_call_name) {
            if (!this._stub) {
                this._stub = AnyCall(this);
            }
            return this._stub;
        }
        return this._declared_calls[this._last_declared_call_name];
    };

    Fake.prototype.calls = function(call) {
        /*
        def calls(self, call):
            """Redefine a call."""
            exp = self._get_current_call()
            exp.call_replacement = call
            return self
        */
    };
    
    /**
     * Expect a call.
       <br /><br /> 
       If the method *call_name* is never called, then raise an error.
        
     * @method expects
     * @return Object
     */
    Fake.prototype.expects = function(call_name) {
        this._last_declared_call_name = call_name;
        var c = new ExpectedCall(this, call_name);
        this._declared_calls[call_name] = c;
        registry.expect_call(c);
        return this;
    };
    
    /**
     * Provide a call.
       <br /><br /> 
       The call acts as a stub -- no error is raised if it is not called.
     *
     * @method provides
     * @return Object
     */
    Fake.prototype.provides = function(call_name) {
        /*
        def provides(self, call_name):
            """Provide a call."""
            self._last_declared_call_name = call_name
            c = Call(self, call_name)
            self._declared_calls[call_name] = c
            return self
        */
    };
    
    /**
     * Set the last call to return a value.
        <br /> <br />
        Set a static value to return when a method is called.
     *
     * @method returns
     * @return Object
     */
    Fake.prototype.returns = function(val) {
        var exp = this._get_current_call();
        exp.return_val = val;
        return this;
    };
    
    /**
     * <p>Set the last call to return a new :class:`fudge.Fake`.</p>
        <p>
        Any given arguments are passed to the :class:`fudge.Fake` constructor
        </p>
        <p>
        Take note that this is different from the cascading nature of 
        other methods.  This will return an instance of the *new* Fake, 
        not self, so you should be careful to store its return value in a new variable.
        </p>
     *
     * @method returns_fake
     * @return Object
     */
    Fake.prototype.returns_fake = function() {
        // make an anonymous object ...
        var return_val = {};
        var fake = new Fake(this._name, {
            "object": return_val
        });
        // ... then attach it to the return value of the last declared method
        this.returns(return_val);
        return fake;
    };
    
    /**
     * Set the last call to expect specific arguments.
     *
     * @method with_args
     * @return Object
     */
    Fake.prototype.with_args = function() {
        var exp = this._get_current_call();
        exp.expected_arguments = arguments;
        return this;
    };
    
    /**
     * Set the last call to expect an exact argument count.
     *
     * @method with_arg_count
     * @return Object
     */
    Fake.prototype.with_arg_count = function(count) {
        /*
        def with_arg_count(self, count):
            """Expect an exact argument count."""
            exp = self._get_current_call()
            exp.expected_arg_count = count
            return self
        */
    };

    /**
     * Set the last call to expect an exact count of keyword arguments.
     *
     * @method with_kwarg_count
     * @return Object
     */
    Fake.prototype.with_kwarg_count = function(count) {  
        /*
        def with_kwarg_count(self, count):
            """Expect an exact count of keyword arguments."""
            exp = self._get_current_call()
            exp.expected_kwarg_count = count
            return self
        */
    };
    
    // fill fudge.* namespace :
    return {
        '__version__': '0.9.3',
        AssertionError: AssertionError,
        clear_expectations: function() { return registry.clear_expectations(); },
        ExpectedCall: ExpectedCall,
        Fake: Fake,
        registry: registry,
        clear_calls: function() { return registry.clear_calls(); },
        verify: function() { return registry.verify(); },
        repr_call_args: repr_call_args
    };
    
}(); // end fudge namespace
