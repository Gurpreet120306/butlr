import unittest
from unittest.mock import MagicMock
import mongomock
from starlette.testclient import TestClient

from app.api.server import create_app
from app.assistant.engine import ButlrAssistant
from app.assistant.conversation import ConversationManager
from app.assistant.memory import MemoryManager
from app.assistant.models import Message
from app.assistant.providers import BaseAIProvider
from app.core.database import MongoDB
from app.experimental.multimodal import MultimodalVisionAssistant
from app.intelligence.debugger import SmartDebugger
from app.intelligence.planner import TaskPlanner
from app.intelligence.productivity import ProductivityManager


class DummyProvider(BaseAIProvider):
    def __init__(self, model="gemma3:1b"):
        self.model = model

    def generate_reply(self, messages: list[Message]) -> str:
        return "I am BUTL-R, your desktop AI assistant."


class TestFastAPIServer(unittest.TestCase):
    def setUp(self):
        # Setup mock database
        self.mock_mongo = mongomock.MongoClient()
        self.mock_db = self.mock_mongo["test_api_butlr"]

        self.db = MongoDB()
        self.db.client = self.mock_mongo
        self.db.database = self.mock_db

        self.conv_mgr = ConversationManager(database=self.mock_db)
        self.mem_mgr = MemoryManager(database=self.mock_db)
        self.provider = DummyProvider()

        self.assistant = ButlrAssistant(
            provider=self.provider,
            conversation_manager=self.conv_mgr,
            memory_manager=self.mem_mgr,
        )

        # Setup mock vision
        self.mock_vision = MagicMock(spec=MultimodalVisionAssistant)
        self.mock_vision.model = "llama3.2-vision:latest"
        self.mock_vision.capture_and_analyze.return_value = (
            "/mock/screen.png",
            "Screen contains browser on localhost:3000.",
        )

        self.debugger = SmartDebugger(ai_provider=self.provider)
        self.planner = TaskPlanner()
        self.productivity = ProductivityManager(database=self.mock_db)

        # Create FastAPI app with injected test dependencies
        self.app = create_app(
            assistant=self.assistant,
            db=self.db,
            vision_assistant=self.mock_vision,
            debugger=self.debugger,
            planner=self.planner,
            productivity=self.productivity,
        )
        self.client = TestClient(self.app)

    def test_root_endpoint(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["app"], "BUTL-R")
        self.assertEqual(data["status"], "online")

    def test_health_endpoint(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["security_mode"], "default-deny")

    def test_chat_endpoint(self):
        payload = {"message": "Hello BUTL-R", "mode": "fast"}
        resp = self.client.post("/api/chat", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("reply", data)
        self.assertIn("conversation_id", data)

    def test_screen_capture_and_analyze_endpoint(self):
        payload = {"prompt": "Find any errors"}
        resp = self.client.post("/api/screen/capture-and-analyze", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["screenshot_path"], "/mock/screen.png")
        self.assertIn("Screen contains browser", data["analysis"])

    def test_debug_analyze_endpoint(self):
        payload = {
            "error_text": "TypeError: Cannot read properties of undefined (reading 'length')",
        }
        resp = self.client.post("/api/debug/analyze", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["detected"])
        self.assertEqual(data["error_type"], "TypeError")

    def test_debug_website_endpoint(self):
        payload = {
            "url": "http://localhost:3000",
            "console_logs": "Failed to load resource: the server responded with a status of 404 (Not Found)",
        }
        resp = self.client.post("/api/debug/website", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["detected"])
        self.assertEqual(data["error_type"], "HTTP_404_NotFound")

    def test_tasks_endpoints(self):
        # Create task
        create_resp = self.client.post("/api/tasks", json={"title": "Prepare presentation", "priority": "high"})
        self.assertEqual(create_resp.status_code, 200)
        task_id = create_resp.json()["task_id"]
        self.assertTrue(task_id)

        # Get tasks
        get_resp = self.client.get("/api/tasks")
        self.assertEqual(get_resp.status_code, 200)
        tasks = get_resp.json()["tasks"]
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["title"], "Prepare presentation")

    def test_plan_execute_endpoint(self):
        payload = {
            "goal": "Backup project notes",
            "steps": [
                {
                    "description": "Read local note",
                    "action_type": "read_data",
                    "category": "read",
                }
            ],
            "confirmed": True,
        }
        resp = self.client.post("/api/plan/execute", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["steps_completed"], 1)


if __name__ == "__main__":
    unittest.main()
