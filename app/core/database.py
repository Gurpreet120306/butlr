from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

class MongoDB:
    """Manages BUTL-R's MongoDB connection."""

    def __init__(self):
        self.client = None
        self.database = None

    def connect(self):
        """Connect to MongoDB or reuse an existing connection."""

        try:
            if self.client is None:
                self.client = MongoClient(
                    "mongodb://localhost:27017/",
                    serverSelectionTimeoutMS=5000,
                    tz_aware=True,
                )

            self.client.admin.command("ping")

            self.database = self.client["butlr"]

            print("BUTL-R MongoDB connection successful!")

            return self.database

        except ConnectionFailure as error:
            print(f"MongoDB connection failed: {error}")
            raise

    def is_healthy(self) -> bool:
        """Check whether MongoDB connection is alive and responsive."""
        if self.client is None:
            return False
        try:
            self.client.admin.command("ping")
            return True
        except Exception:
            return False

    def reconnect(self, max_retries: int = 3):
        """Force a fresh connection, closing any stale client."""
        self.close()
        for attempt in range(1, max_retries + 1):
            try:
                return self.connect()
            except ConnectionFailure:
                if attempt == max_retries:
                    raise
                import time
                time.sleep(0.5 * attempt)

    def close(self):
        """Close the MongoDB connection."""

        if self.client is not None:
            self.client.close()
            self.client = None
            self.database = None

            print("MongoDB connection closed.")


mongodb = MongoDB()