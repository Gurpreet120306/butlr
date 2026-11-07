
import re


class MemoryCommandHandler:
    """Recognizes explicit user requests involving memory."""

    def __init__(self, memory_manager):
        self.memory_manager = memory_manager

        # Pending deletions are isolated by conversation ID.
        self.pending_forget = {}

    def handle(self, content, conversation_id):
        """Process a recognized memory command."""

        if not isinstance(content, str) or not content.strip():
            return None

        text = content.strip()
        confirmation = text.lower()

        # Check whether this conversation has a pending deletion.
        if conversation_id in self.pending_forget:

            if confirmation in {"yes", "confirm", "delete it"}:
                category, key = self.pending_forget.pop(
                    conversation_id
                )

                deleted = self.memory_manager.delete_memory(
                    category,
                    key,
                )

                if deleted:
                    return f"I've forgotten {key}."

                return f"I couldn't find a saved memory for {key}."

            if confirmation in {"no", "cancel"}:
                self.pending_forget.pop(conversation_id)

                return "Okay. I won't delete that memory."

            # An unrelated message cancels the pending deletion.
            # Continue processing the new message normally.
            self.pending_forget.pop(conversation_id)

        # Recognize: Remember that my favourite language is Python.
        match = re.fullmatch(
            r"remember that my (.+?) is (.+)",
            text,
            flags=re.IGNORECASE,
        )

        if match:
            key = match.group(1).strip()
            value = match.group(2).strip()

            try:
                self.memory_manager.save_memory(
                    "preferences",
                    key,
                    value,
                )
            except ValueError:
                return (
                    "I couldn't save that information because "
                    "it may contain sensitive data."
                )

            return f"I'll remember that your {key} is {value}."

        # Recognize: Forget my favourite language.
        match = re.fullmatch(
            r"forget my (.+)",
            text,
            flags=re.IGNORECASE,
        )

        if match:
            key = match.group(1).strip().rstrip(".")

            self.pending_forget[conversation_id] = (
                "preferences",
                key,
            )

            return (
                f"Do you want me to forget your {key}? "
                "Please confirm with 'yes' or cancel with 'no'."
            )

        return None
