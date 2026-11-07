
from app.assistant.conversation import ConversationManager
from app.assistant.providers import BaseAIProvider
from app.assistant.memory import MemoryManager
from app.assistant.memory_commands import MemoryCommandHandler

class ButlrAssistant:
    """Connects conversation management with an AI provider."""

    def __init__(
        self,
        provider: BaseAIProvider,
        conversation_manager=None,
        memory_manager=None,
    ):
        self.provider = provider
        
        self.memory_manager = (
            memory_manager
            if memory_manager is not None
            else MemoryManager()
        )

        self.memory_commands = MemoryCommandHandler(
            self.memory_manager
        )

        self.conversation_manager = (
            conversation_manager
            if conversation_manager is not None
            else ConversationManager()
        )

    def start_conversation(self):
        """Start a new conversation."""
        return self.conversation_manager.create_conversation()

    def set_mode(self, mode: str):
        """Switch between supported AI modes."""

        if not hasattr(self.provider, "set_mode"):
            raise RuntimeError(
                "The configured AI provider does not support mode switching."
            )

        return self.provider.set_mode(mode)

    def get_mode(self):
        """Return the current AI mode."""

        return getattr(self.provider, "mode", "unknown")



    def _get_memory_context(self, content: str) -> str:
        """Retrieve only memories relevant to the current message."""

        query = content.lower()

        if not any(
            keyword in query
            for keyword in (
                "my name",
                "favourite",
                "favorite",
                "remembered",
                "what do you know about me",
            )
        ):
            return ""

        # Search only for memory keys mentioned in the question.
        memories = self.memory_manager.memories.find(
            {},
            {
                "_id": 0,
                "category": 1,
                "key": 1,
                "value": 1,
            },
        )

        relevant_memories = []

        for memory in memories:
            key = memory["key"].lower()

            if key in query or (
                key.startswith("my ")
                and key[3:] in query
            ):
                relevant_memories.append(
                    f"{memory['category']} | "
                    f"{memory['key']} | "
                    f"{memory['value']}"
                )

        return "\n".join(relevant_memories)


    def send_message(self, conversation_id: str, content: str) -> str:
        """Send a message and receive an AI response."""

        # Handle explicit memory commands before calling the AI.
        memory_reply = self.memory_commands.handle(content,conversation_id,)

        if memory_reply is not None:
            self.conversation_manager.add_message(
                conversation_id,
                "user",
                content,
            )

            self.conversation_manager.add_message(
                conversation_id,
                "assistant",
                memory_reply,
            )

            return memory_reply



        self.conversation_manager.add_message(
            conversation_id,
            "user",
            content,
        )

        messages = self.conversation_manager.get_messages(
            conversation_id
        )

        memory_context = self._get_memory_context(content)

        if hasattr(self.provider, "AVAILABLE_MODES"):
            reply = self.provider.generate_reply(
                messages,
                memory_context=memory_context,
            )
        else:
            reply = self.provider.generate_reply(messages)

        self.conversation_manager.add_message(
            conversation_id,
            "assistant",
            reply,
        )

        return reply

    def get_history(self, conversation_id: str):
        """Retrieve all messages in a conversation."""
        return self.conversation_manager.get_messages(conversation_id)

    def delete_conversation(self, conversation_id: str):
        """Delete a conversation."""
        self.conversation_manager.delete_conversation(conversation_id)

    
    def remember(self, category: str, key: str, value: str):
        """Save information in BUTL-R's long-term memory."""
        return self.memory_manager.save_memory(
            category,
            key,
            value,
        )

    def recall(self, category: str, key: str):
        """Retrieve information from long-term memory."""
        return self.memory_manager.get_memory(
            category,
            key,
        )

    def forget(self, category: str, key: str):
        """Delete information from long-term memory."""
        return self.memory_manager.delete_memory(
            category,
            key,
        )
