from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from app.core.database import mongodb


class ProductivityManager:
    """Manages personal tasks, reminders, schedules, and notes in MongoDB."""

    def __init__(self, database=None):
        if database is None:
            database = mongodb.connect()
        self.database = database
        self.tasks = database["user_tasks"]
        self.notes = database["user_notes"]

    # ------------------ TASKS / TODOS ------------------

    def add_task(self, title: str, due_date: Optional[str] = None) -> dict:
        """Add a new personal task to the to-do list."""
        task_id = str(uuid4())[:8]
        doc = {
            "task_id": task_id,
            "title": title.strip(),
            "due_date": due_date,
            "completed": False,
            "created_at": datetime.now(timezone.utc),
        }
        self.tasks.insert_one(doc)
        return doc

    def list_tasks(self, include_completed: bool = False) -> list[dict]:
        """List tasks, optionally filtering out completed items."""
        query = {} if include_completed else {"completed": False}
        return list(self.tasks.find(query, {"_id": 0}).sort("created_at", -1))

    def complete_task(self, task_id: str) -> bool:
        """Mark a task as completed."""
        result = self.tasks.update_one(
            {"task_id": task_id},
            {"$set": {"completed": True, "completed_at": datetime.now(timezone.utc)}},
        )
        return result.modified_count > 0

    # ------------------ NOTES ------------------

    def add_note(self, title: str, content: str) -> dict:
        """Save a new note."""
        note_id = str(uuid4())[:8]
        doc = {
            "note_id": note_id,
            "title": title.strip(),
            "content": content.strip(),
            "created_at": datetime.now(timezone.utc),
        }
        self.notes.insert_one(doc)
        return doc

    def list_notes(self) -> list[dict]:
        """Retrieve all personal notes."""
        return list(self.notes.find({}, {"_id": 0}).sort("created_at", -1))
