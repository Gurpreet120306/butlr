
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from app.core.config import settings


class MongoDB:
    """Manages BUTL-R's MongoDB connection."""

    def __init__(self):
        self.client = None
        self.database = None

    def connect(self):
        """Connect to the local MongoDB server."""

        try:
            self.client = MongoClient(
                "mongodb://localhost:27017/",
                serverSelectionTimeoutMS=5000,
            )

            # Verify that MongoDB is reachable.
            self.client.admin.command("ping")

            # Select BUTL-R's database.
            self.database = self.client["butlr"]

            print("BUTL-R MongoDB connection successful!")

            return self.database

        except ConnectionFailure as error:
            print(f"MongoDB connection failed: {error}")
            raise

    def close(self):
        """Close the MongoDB connection."""

        if self.client is not None:
            self.client.close()
            self.client = None
            self.database = None

            print("MongoDB connection closed.")


# Shared database manager for BUTL-R.
mongodb = MongoDB()
