try:
    import _thread as thread
except ImportError:
    import thread
import sys
import unittest
import fudge
from fudge import ExpectedCall, ExpectedCallOrder

class TestRegistry(unittest.TestCase):

    def setUp(self):
        self.fake = fudge.Fake()
        self.reg = fudge.registry
        # in case of error, clear out everything:
        self.reg.clear_all()

    def tearDown(self):
        pass

    def test_expected_call_not_called(self):
        with self.assertRaises(AssertionError):
            self.reg.clear_calls()
            self.reg.expect_call(ExpectedCall(self.fake, 'nothing'))
            self.reg.verify()

    def test_clear_calls_resets_calls(self):
        exp = ExpectedCall(self.fake, 'callMe')
        self.reg.expect_call(exp)
        exp()
        self.assertEqual(exp.was_called, True)

        self.reg.clear_calls()
        self.assertEqual(exp.was_called, False, "call was not reset by clear_calls()")

    def test_clear_calls_resets_call_order(self):
        exp_order = ExpectedCallOrder(self.fake)
        exp = ExpectedCall(self.fake, 'callMe', call_order=exp_order)
        exp_order.add_expected_call(exp)
        self.reg.remember_expected_call_order(exp_order)

        exp()
        self.assertEqual(exp_order._actual_calls, [exp])

        self.reg.clear_calls()
        self.assertEqual(exp_order._actual_calls, [], "call order calls were not reset by clear_calls()")

    def test_verify_resets_calls(self):
        exp = ExpectedCall(self.fake, 'callMe')
        exp()
        self.assertEqual(exp.was_called, True)
        self.assertEqual(len(self.reg.get_expected_calls()), 1)

        self.reg.verify()
        self.assertEqual(exp.was_called, False, "call was not reset by verify()")
        self.assertEqual(len(self.reg.get_expected_calls()), 1, "verify() should not reset expectations")

    def test_verify_resets_call_order(self):
        exp_order = ExpectedCallOrder(self.fake)
        exp = ExpectedCall(self.fake, 'callMe', call_order=exp_order)
        exp_order.add_expected_call(exp)
        self.reg.remember_expected_call_order(exp_order)

        exp()
        self.assertEqual(exp_order._actual_calls, [exp])

        self.reg.verify()
        self.assertEqual(exp_order._actual_calls, [], "call order calls were not reset by verify()")

    def test_global_verify(self):
        exp = ExpectedCall(self.fake, 'callMe')
        exp()
        self.assertEqual(exp.was_called, True)
        self.assertEqual(len(self.reg.get_expected_calls()), 1)

        fudge.verify()

        self.assertEqual(exp.was_called, False, "call was not reset by verify()")
        self.assertEqual(len(self.reg.get_expected_calls()), 1, "verify() should not reset expectations")

    def test_global_clear_expectations(self):
        exp = ExpectedCall(self.fake, 'callMe')
        exp()
        self.assertEqual(len(self.reg.get_expected_calls()), 1)
        exp_order = ExpectedCallOrder(self.fake)
        self.reg.remember_expected_call_order(exp_order)
        self.assertEqual(self.reg.get_expected_call_order().keys(), [self.fake])

        fudge.clear_expectations()

        self.assertEqual(len(self.reg.get_expected_calls()), 0,
            "clear_expectations() should reset expectations")
        self.assertEqual(len(self.reg.get_expected_call_order().keys()), 0,
            "clear_expectations() should reset expected call order")

    def test_multithreading(self):
        if sys.platform.startswith('java'):
            raise unittest.SkipTest('this test is flaky in Jython')

        reg = fudge.registry

        class thread_run:
            waiting = 5
            errors = []

        # while this barely catches collisions
        # it ensures that each thread can use the registry ok
        def registry(num):
            try:
                try:
                    fudge.clear_calls()
                    fudge.clear_expectations()

                    exp_order = ExpectedCallOrder(self.fake)
                    reg.remember_expected_call_order(exp_order)
                    self.assertEqual(len(reg.get_expected_call_order().keys()), 1)

                    # registered first time on __init__ :
                    exp = ExpectedCall(self.fake, 'callMe', call_order=exp_order)
                    reg.expect_call(exp)
                    reg.expect_call(exp)
                    reg.expect_call(exp)
                    self.assertEqual(len(reg.get_expected_calls()), 4)

                    # actual calls:
                    exp()
                    exp()
                    exp()
                    exp()

                    fudge.verify()
                    fudge.clear_expectations()
                except Exception as er:
                    thread_run.errors.append(er)
                    raise
            finally:
                thread_run.waiting -= 1

        thread.start_new_thread(registry, (1,))
        thread.start_new_thread(registry, (2,))
        thread.start_new_thread(registry, (3,))
        thread.start_new_thread(registry, (4,))
        thread.start_new_thread(registry, (5,))

        count = 0
        while thread_run.waiting > 0:
            count += 1
            import time
            time.sleep(0.25)
            if count == 60:
                raise RuntimeError("timed out waiting for thread")
        if len(thread_run.errors):
            raise RuntimeError(
                "Error(s) in thread: %s" % ["%s: %s" % (
                    e.__class__.__name__, e) for e in thread_run.errors])

