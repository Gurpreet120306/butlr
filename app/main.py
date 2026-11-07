
from app.core.config import settings
from app.core.logger import setup_logger


def main():
    logger = setup_logger()

    print("=" * 50)
    print("          BUTL-R PERSONAL AI ASSISTANT")
    print("=" * 50)

    print(f"Application: {settings.APP_NAME}")
    print(f"Version: {settings.APP_VERSION}")
    print(f"Environment: {settings.ENVIRONMENT}")

    print("\nInitializing application...")

    logger.info("Application startup initiated.")
    logger.info("Configuration loaded successfully.")

    print("Configuration: READY")
    print("Logging: READY")
    print("Application status: ONLINE")

    logger.info("BUTL-R started successfully.")

    print("\nBUTL-R core foundation is operational!")
    print("=" * 50)


if __name__ == "__main__":
    main()
