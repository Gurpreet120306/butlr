
import unittest

from app.core.config import settings
from app.core.logger import setup_logger


class TestButlrCore(unittest.TestCase):

    def test_application_name(self):
        self.assertEqual(settings.APP_NAME, "BUTL-R")

    def test_application_version(self):
        self.assertEqual(settings.APP_VERSION, "0.1.0")

    def test_project_directory_exists(self):
        self.assertTrue(settings.ROOT_DIR.exists())

    def test_required_directories(self):
        settings.initialize_directories()

        self.assertTrue(settings.DATA_DIR.exists())
        self.assertTrue(settings.LOG_DIR.exists())

    def test_logger_initialization(self):
        logger = setup_logger()

        self.assertIsNotNone(logger)


if __name__ == "__main__":
    unittest.main()
