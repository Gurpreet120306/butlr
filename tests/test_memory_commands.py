
import unittest

from mongomock import MongoClient

from app.assistant.memory import MemoryManager
from app.assistant.memory_commands import MemoryCommandHandler


class TestMemoryCommandHandler(unittest.TestCase):

    def setUp(self):
        self.client = MongoClient()
        self.database = self.client["butlr_memory_command_test"]

        self.memory_manager = MemoryManager(
            database=self.database
        )

        self.handler = MemoryCommandHandler(
            self.memory_manager
        )

    def tearDown(self):
        self.client.close()

    def test_remember_command(self):
        reply = self.handler.handle(
            "Remember that my favourite programming language is Python.",
            "conversation_1",
        )

        self.assertEqual(
            self.memory_manager.get_memory(
                "preferences",
                "favourite programming language",
            ),
            "Python",
        )

        self.assertIn("remember", reply.lower())

    def test_forget_requires_confirmation(self):
        self.memory_manager.save_memory(
            "preferences",
            "favourite programming language",
            "Python",
        )

        reply = self.handler.handle(
            "Forget my favourite programming language.",
            "conversation_1",
        )

        self.assertIn("confirm", reply.lower())

        self.assertEqual(
            self.memory_manager.get_memory(
                "preferences",
                "favourite programming language",
            ),
            "Python",
        )

    def test_confirm_forget(self):
        self.memory_manager.save_memory(
            "preferences",
            "favourite programming language",
            "Python",
        )

        self.handler.handle(
            "Forget my favourite programming language.",
            "conversation_1",
        )

        reply = self.handler.handle("yes", "conversation_1")

        self.assertIn("forgotten", reply.lower())

        self.assertIsNone(
            self.memory_manager.get_memory(
                "preferences",
                "favourite programming language",
            )
        )

    def test_cancel_forget(self):
        self.memory_manager.save_memory(
            "preferences",
            "favourite programming language",
            "Python",
        )

        self.handler.handle(
            "Forget my favourite programming language.",
            "conversation_1",
        )

        reply = self.handler.handle("no", "conversation_1")

        self.assertIn("won't delete", reply.lower())

        self.assertEqual(
            self.memory_manager.get_memory(
                "preferences",
                "favourite programming language",
            ),
            "Python",
        )

    def test_pending_deletion_is_conversation_specific(self):
        self.memory_manager.save_memory(
            "preferences",
            "favourite programming language",
            "Python",
        )

        self.handler.handle(
            "Forget my favourite programming language.",
            "conversation_1",
        )

        # A confirmation in another conversation must not delete it.
        reply = self.handler.handle("yes", "conversation_2")

        self.assertIsNone(reply)

        self.assertEqual(
            self.memory_manager.get_memory(
                "preferences",
                "favourite programming language",
            ),
            "Python",
        )

        # The original conversation can still confirm deletion.
        reply = self.handler.handle("yes", "conversation_1")

        self.assertIn("forgotten", reply.lower())

    def test_unrelated_message_cancels_pending_deletion(self):
        self.handler.handle(
            "Forget my favourite programming language.",
            "conversation_1",
        )

        reply = self.handler.handle(
            "Hello BUTL-R!",
            "conversation_1",
        )

        self.assertIsNone(reply)

        self.assertNotIn(
            "conversation_1",
            self.handler.pending_forget,
        )

    def test_sensitive_memory_is_rejected_gracefully(self):
        reply = self.handler.handle(
            "Remember that my password is secret123.",
            "conversation_1",
        )

        self.assertIn("sensitive", reply.lower())

    def test_empty_content_is_ignored(self):
        reply = self.handler.handle(
            "   ",
            "conversation_1",
        )

        self.assertIsNone(reply)


if __name__ == "__main__":
    unittest.main()
