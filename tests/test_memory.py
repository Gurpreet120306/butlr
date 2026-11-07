
import unittest
from mongomock import MongoClient

from app.assistant.memory import MemoryManager


class TestMemoryManager(unittest.TestCase):

    def setUp(self):
        self.client = MongoClient()
        self.database = self.client["test_butlr"]

        self.memory_manager = MemoryManager(
            database=self.database
        )

    def tearDown(self):
        self.client.close()

    def test_save_memory(self):
        result = self.memory_manager.save_memory(
            "preferences",
            "favourite language",
            "Python",
        )

        self.assertTrue(result)

    def test_retrieve_memory(self):
        self.memory_manager.save_memory(
            "preferences",
            "favourite language",
            "Python",
        )

        result = self.memory_manager.get_memory(
            "preferences",
            "favourite language",
        )

        self.assertEqual(result, "Python")

    def test_update_existing_memory(self):
        self.memory_manager.save_memory(
            "preferences",
            "favourite language",
            "Python",
        )

        self.memory_manager.save_memory(
            "preferences",
            "favourite language",
            "JavaScript",
        )

        result = self.memory_manager.get_memory(
            "preferences",
            "favourite language",
        )

        self.assertEqual(result, "JavaScript")

        count = self.database["memories"].count_documents({})

        self.assertEqual(count, 1)

    def test_retrieve_missing_memory(self):
        result = self.memory_manager.get_memory(
            "preferences",
            "unknown",
        )

        self.assertIsNone(result)

    def test_delete_memory(self):
        self.memory_manager.save_memory(
            "preferences",
            "favourite language",
            "Python",
        )

        result = self.memory_manager.delete_memory(
            "preferences",
            "favourite language",
        )

        self.assertTrue(result)

        self.assertIsNone(
            self.memory_manager.get_memory(
                "preferences",
                "favourite language",
            )
        )

    def test_delete_missing_memory(self):
        result = self.memory_manager.delete_memory(
            "preferences",
            "unknown",
        )

        self.assertFalse(result)

    def test_empty_memory_rejected(self):
        with self.assertRaises(ValueError):
            self.memory_manager.save_memory(
                "",
                "favourite language",
                "Python",
            )


    def test_password_memory_rejected(self):
        with self.assertRaises(ValueError):
            self.memory_manager.save_memory(
                "security",
                "account password",
                "MyPassword123",
            )

    def test_api_key_memory_rejected(self):
        with self.assertRaises(ValueError):
            self.memory_manager.save_memory(
                "security",
                "service credential",
                "My API key is abc123",
            )



if __name__ == "__main__":
    unittest.main()
