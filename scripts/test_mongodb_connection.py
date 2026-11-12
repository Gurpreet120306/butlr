
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import mongodb


def main():
    try:
        database = mongodb.connect()

        print("\nConnected database:", database.name)

        print("\nAvailable collections:")

        for collection in database.list_collection_names():
            print("-", collection)

    except Exception as error:
        print("\nDATABASE TEST FAILED:", error)

    finally:
        mongodb.close()


if __name__ == "__main__":
    main()

