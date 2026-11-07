import sqlite3
from contextlib import closing
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone

from app.assistant.models import Message
from app.core.config import settings


class ConversationManager:
    """Manages conversations and stores them permanently in SQLite."""

    def __init__(self, db_path=None):

        if db_path is None:
            settings.initialize_directories()
            self.db_path = settings.DATA_DIR / "butlr.db"
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        self._initialize_database()

    def _connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize_database(self):
        """Create the database tables if they do not exist."""

        with closing(self._connect()) as connection:
            with connection:
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        conversation_id TEXT PRIMARY KEY,
                        created_at TEXT NOT NULL
                    )
                """)

                connection.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        message_id TEXT PRIMARY KEY,
                        conversation_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp TEXT NOT NULL,

                        FOREIGN KEY (conversation_id)
                        REFERENCES conversations(conversation_id)
                        ON DELETE CASCADE
                    )
                """)

    def create_conversation(self):
        conversation_id = str(uuid4())

        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                    """
                    INSERT INTO conversations (
                        conversation_id,
                        created_at
                    )
                    VALUES (?, ?)
                    """,
                    (
                        conversation_id,
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )

        return conversation_id

    def add_message(self, conversation_id, role, content):

        message = Message(
            role=role,
            content=content,
        )

        with closing(self._connect()) as connection:
            with connection:
                conversation = connection.execute(
                    """
                    SELECT 1 FROM conversations
                    WHERE conversation_id = ?
                    """,
                    (conversation_id,),
                ).fetchone()

                if conversation is None:
                    raise KeyError("Conversation does not exist.")

                connection.execute(
                    """
                    INSERT INTO messages (
                        message_id,
                        conversation_id,
                        role,
                        content,
                        timestamp
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        message.message_id,
                        conversation_id,
                        message.role,
                        message.content,
                        message.timestamp.isoformat(),
                    ),
                )

        return message

    def get_messages(self, conversation_id):

        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT message_id, role, content, timestamp
                FROM messages
                WHERE conversation_id = ?
                ORDER BY rowid
                """,
                (conversation_id,),
            ).fetchall()

            conversation = connection.execute(
                """
                SELECT 1 FROM conversations
                WHERE conversation_id = ?
                """,
                (conversation_id,),
            ).fetchone()

        if conversation is None:
            raise KeyError("Conversation does not exist.")

        return [
            Message(
                message_id=row[0],
                role=row[1],
                content=row[2],
                timestamp=datetime.fromisoformat(row[3]),
            )
            for row in rows
        ]

    def delete_conversation(self, conversation_id):

        with closing(self._connect()) as connection:
            with connection:
                cursor = connection.execute(
                    """
                    DELETE FROM conversations
                    WHERE conversation_id = ?
                    """,
                    (conversation_id,),
                )

                if cursor.rowcount == 0:
                    raise KeyError("Conversation does not exist.")