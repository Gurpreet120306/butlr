import unittest
from unittest.mock import MagicMock

from app.intelligence.debugger import SmartDebugger
from app.intelligence.planner import TaskPlanner, TaskStep
from app.security.policy import ActionCategory, SecurityPolicy


class TestSmartDebugger(unittest.TestCase):
    def setUp(self):
        self.mock_provider = MagicMock()
        self.mock_provider.generate_reply.return_value = "Cause: Syntax error in file. Fix: Add closing parenthesis."
        self.debugger = SmartDebugger(ai_provider=self.mock_provider)

    def test_diagnose_javascript_type_error(self):
        js_error = "TypeError: Cannot read properties of undefined (reading 'map')"
        result = self.debugger.diagnose_error(js_error)
        self.assertTrue(result["detected"])
        self.assertEqual(result["error_type"], "TypeError")
        self.assertIn("optional chaining", result["suggested_fix"].lower())

    def test_diagnose_python_traceback(self):
        py_traceback = (
            'Traceback (most recent call last):\n'
            '  File "app/main.py", line 42, in run\n'
            '    data = json.loads(payload)\n'
            'json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)'
        )
        result = self.debugger.diagnose_error(py_traceback)
        self.assertTrue(result["detected"])
        self.assertEqual(result["file"], "app/main.py")
        self.assertEqual(result["line"], 42)

    def test_diagnose_website_404_error(self):
        web_error = "GET https://example.com/api/v1/users 404 (Not Found)"
        result = self.debugger.analyze_website_error("https://example.com/api/v1/users", console_logs=web_error)
        self.assertTrue(result["detected"])
        self.assertEqual(result["error_type"], "HTTP_404_NotFound")
        self.assertEqual(result["target_url"], "https://example.com/api/v1/users")

    def test_verify_resolution_success(self):
        original = "TypeError: undefined is not a function"
        resolution = "Build succeeded with 0 errors. Status: 200 OK."
        result = self.debugger.verify_resolution(original, resolution)
        self.assertTrue(result["resolved"])

    def test_verify_resolution_failure(self):
        original = "TypeError: undefined is not a function"
        resolution = "Process exited with TypeError: undefined is not a function"
        result = self.debugger.verify_resolution(original, resolution)
        self.assertFalse(result["resolved"])

    def test_plan_execute_verify_closed_loop(self):
        planner = TaskPlanner(security_policy=SecurityPolicy())
        specs = [
            {
                "description": "Inspect website source",
                "action_type": "read_file",
                "category": ActionCategory.SYSTEM,
                "verification_check": "source_loaded",
            },
            {
                "description": "Run unit test suite",
                "action_type": "read_data",
                "category": ActionCategory.READ,
                "verification_check": "tests_passed",
            },
        ]
        plan = planner.create_plan("Fix site error", specs)

        def mock_verifier(step: TaskStep) -> bool:
            return True

        success, msg = planner.execute_plan(plan, verifier=mock_verifier)
        self.assertTrue(success)
        self.assertTrue(plan.completed)
        self.assertTrue(plan.verified)
        self.assertTrue(all(s.verified for s in plan.steps))


if __name__ == "__main__":
    unittest.main()
