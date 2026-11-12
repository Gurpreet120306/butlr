import unittest
from pathlib import Path
from mongomock import MongoClient

from app.intelligence.planner import TaskPlanner
from app.intelligence.plugins import PluginRegistry, BasePlugin
from app.intelligence.productivity import ProductivityManager
from app.intelligence.docs import DocumentAssistant
from app.security.policy import ActionCategory, SecurityPolicy, AuthorizationStatus


class DummyWeatherPlugin(BasePlugin):
    name = "weather_plugin"
    action_type = "get_weather"
    category = ActionCategory.READ

    def run(self, parameters: dict) -> str:
        city = parameters.get("city", "Delhi")
        return f"Weather in {city}: 25C, Clear"


class TestIntelligenceSubsystem(unittest.TestCase):

    def setUp(self):
        self.client = MongoClient()
        self.database = self.client["butlr_intelligence_test"]
        self.policy = SecurityPolicy()

    def tearDown(self):
        self.client.close()

    def test_task_planner_creates_and_executes_plan(self):
        """Planner builds sequential plan and executes authorized steps."""
        planner = TaskPlanner(security_policy=self.policy)
        plan = planner.create_plan(
            goal="Prepare daily report",
            step_specs=[
                {"description": "Check system info", "action_type": "read_system_info"},
                {"description": "Read user memory", "action_type": "read_memory"},
            ],
        )

        self.assertEqual(len(plan.steps), 2)
        success, msg = planner.execute_plan(plan)
        self.assertTrue(success)
        self.assertTrue(plan.completed)
        self.assertTrue(plan.steps[0].completed)

    def test_task_planner_blocks_unauthorized_step(self):
        """Planner immediately stops if a plan step violates security policy."""
        planner = TaskPlanner(security_policy=self.policy)
        plan = planner.create_plan(
            goal="Harmful operation",
            step_specs=[
                {"description": "Execute shell", "action_type": "unrestricted_shell"},
            ],
        )

        success, msg = planner.execute_plan(plan)
        self.assertFalse(success)
        self.assertIn("failed security check", msg)
        self.assertFalse(plan.completed)

    def test_plugin_registry_and_execution(self):
        """Plugins register with policy engine and execute safely."""
        registry = PluginRegistry(security_policy=self.policy)
        registry.register_plugin(DummyWeatherPlugin(), permission=AuthorizationStatus.ALLOWED)

        success, result = registry.execute_plugin("weather_plugin", {"city": "Mumbai"})
        self.assertTrue(success)
        self.assertIn("Mumbai: 25C", result)

    def test_productivity_manager_tasks_and_notes(self):
        """ProductivityManager adds, lists, and completes tasks and notes."""
        prod = ProductivityManager(database=self.database)

        # Task management
        task = prod.add_task("Finish project milestone", due_date="Today")
        tasks = prod.list_tasks(include_completed=False)
        self.assertEqual(len(tasks), 1)

        completed = prod.complete_task(task["task_id"])
        self.assertTrue(completed)
        self.assertEqual(len(prod.list_tasks(include_completed=False)), 0)

        # Notes
        note = prod.add_note("Idea", "Build local AI robot")
        notes = prod.list_notes()
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0]["title"], "Idea")

    def test_document_assistant_summary_and_search(self):
        """DocumentAssistant extracts metrics and finds line matches."""
        docs = DocumentAssistant()
        sample_file = Path(__file__).resolve()

        summary = docs.summarize_document(str(sample_file))
        self.assertNotIn("error", summary)
        self.assertGreater(summary["word_count"], 10)

        matches = docs.search_in_document(str(sample_file), "DummyWeatherPlugin")
        self.assertGreater(len(matches), 0)
        self.assertIn("class DummyWeatherPlugin", matches[0][1])


if __name__ == "__main__":
    unittest.main()
