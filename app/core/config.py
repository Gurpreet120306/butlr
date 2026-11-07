
from pathlib import Path


# Find the BUTL-R project root directory.
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings:
    """Central configuration for BUTL-R."""

    APP_NAME = "BUTL-R"
    APP_VERSION = "0.1.0"
    ENVIRONMENT = "development"

    ROOT_DIR = PROJECT_ROOT
    DATA_DIR = ROOT_DIR / "data"
    LOG_DIR = ROOT_DIR / "logs"

    @classmethod
    def initialize_directories(cls):
        """Create required application directories."""

        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
