
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

