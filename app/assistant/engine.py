
from app.assistant.conversation import ConversationManager
from app.assistant.providers import BaseAIProvider
from app.assistant.memory import MemoryManager
from app.assistant.memory_commands import MemoryCommandHandler
from app.core.resilience import FallbackHandler
from app.security.policy import (
    ActionCategory,
    ActionRequest,
    AuthorizationResult,
    AuthorizationStatus,
    SecurityPolicy,
)
from app.security.audit import AuditLogger
from app.security.privacy import PrivacyManager
from app.security.sanitizer import detect_prompt_injection


class ButlrAssistant:
    """Connects conversation management with an AI provider, security policy, and privacy manager."""

    def __init__(
        self,
        provider: BaseAIProvider,
        conversation_manager=None,
        memory_manager=None,
        security_policy=None,
        audit_logger=None,
        privacy_manager=None,
    ):
        self.provider = provider

        self.conversation_manager = (
            conversation_manager
            if conversation_manager is not None
            else ConversationManager()
        )

        self.memory_manager = (
            memory_manager
            if memory_manager is not None
            else MemoryManager(database=self.conversation_manager.database)
        )

        self.security_policy = (
            security_policy
            if security_policy is not None
            else SecurityPolicy()
        )

        self.audit_logger = (
            audit_logger
            if audit_logger is not None
            else AuditLogger(database=self.conversation_manager.database)
        )

        self.privacy_manager = (
            privacy_manager
            if privacy_manager is not None
            else PrivacyManager(database=self.conversation_manager.database)
        )

        self.memory_commands = MemoryCommandHandler(
            self.memory_manager
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
        """Retrieve memories relevant to the user's message."""

        query = content.lower().strip()

        # Handle broad questions asking for all remembered information.
        broad_queries = (
            "what do you know about me",
            "what do you remember about me",
            "what do you remember",
            "tell me what you know about me",
            "what are my memories",
            "what have you remembered",
        )
        if any(phrase in query for phrase in broad_queries):
            all_memories = self.memory_manager.memories.find(
                {},
                {
                    "_id": 0,
                    "category": 1,
                    "key": 1,
                    "value": 1,
                },
            )
            return "\n".join(
                f"{m['category']} | {m['key']} | {m['value']}"
                for m in all_memories
            )

        stop_words = {
            "what", "which", "is", "are", "my", "me",
            "do", "you", "the", "a", "an", "of",
            "to", "about", "can", "please", "tell",
            "remind", "remember", "know", "i",
            "have", "had", "was", "were", "your",
        }

        query_words = {
            word.strip(".,!?")
            for word in query.split()
        } - stop_words

        if not query_words:
            return ""

        memories = self.memory_manager.memories.find(
            {},
            {
                "_id": 0,
                "category": 1,
                "key": 1,
                "value": 1,
            },
        )

        scored_memories = []

        for memory in memories:
            key_raw = memory["key"].lower()
            key_words = {
                word.strip(".,!?")
                for word in key_raw.split()
            } - stop_words

            if not key_words:
                continue

            # Exact key appears directly in the query string
            if key_raw in query:
                scored_memories.append((1.0, memory))
                continue

            overlap = key_words & query_words
            if overlap:
                union = key_words | query_words
                jaccard = len(overlap) / len(union)
                key_coverage = len(overlap) / len(key_words)

                if jaccard >= 0.4 or key_coverage >= 0.6:
                    score = max(jaccard, key_coverage)
                    scored_memories.append((score, memory))

        scored_memories.sort(key=lambda item: item[0], reverse=True)

        return "\n".join(
            f"{memory['category']} | {memory['key']} | {memory['value']}"
            for _, memory in scored_memories
        )

    def authorize_action(self, action_request: ActionRequest) -> AuthorizationResult:
        """Evaluate an action against security policy and log an audit record."""
        result = self.security_policy.authorize(action_request)
        self.audit_logger.log_event(
            event_type="action_authorization",
            action_type=action_request.action_type,
            decision=result.status.value,
            reason=result.reason,
            requested_by=action_request.requested_by,
            conversation_id=action_request.conversation_id,
            target=action_request.target,
            parameters=action_request.parameters,
        )
        return result

    def send_message(self, conversation_id: str, content: str) -> str:
        """Send a message and receive an AI response."""

        # Defense against prompt injection attempts
        is_injection, reason = detect_prompt_injection(content)
        if is_injection:
            self.audit_logger.log_event(
                event_type="prompt_injection_detected",
                action_type="send_message",
                decision="denied",
                reason=reason,
                requested_by="user",
                conversation_id=conversation_id,
                target=content[:80],
            )
            warning_reply = (
                "I cannot process this request because it violates "
                "BUTL-R safety and security guidelines."
            )
            self.conversation_manager.add_message(
                conversation_id,
                "user",
                content,
            )
            self.conversation_manager.add_message(
                conversation_id,
                "assistant",
                warning_reply,
            )
            return warning_reply

        memory_reply = self.memory_commands.handle(
            content,
            conversation_id,
        )

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

        try:
            if hasattr(self.provider, "AVAILABLE_MODES"):
                reply = self.provider.generate_reply(
                    messages,
                    memory_context=memory_context,
                )
            else:
                reply = self.provider.generate_reply(messages)
        except Exception as error:
            self.audit_logger.log_event(
                event_type="provider_error",
                action_type="generate_reply",
                decision="error",
                reason=str(error),
                requested_by="assistant",
                conversation_id=conversation_id,
            )
            reply = FallbackHandler.get_fallback(error)

        self.conversation_manager.add_message(
            conversation_id,
            "assistant",
            reply,
        )

        return reply

    def get_history(self, conversation_id: str):
        """Retrieve all messages in a conversation."""
        return self.conversation_manager.get_messages(
            conversation_id
        )

    def delete_conversation(self, conversation_id: str):
        """Delete a conversation after security audit."""
        self.authorize_action(ActionRequest(
            action_type="delete_conversation",
            category=ActionCategory.SYSTEM,
            target=conversation_id,
            requested_by="user",
            conversation_id=conversation_id,
        ))
        self.conversation_manager.delete_conversation(
            conversation_id
        )

    def remember(self, category: str, key: str, value: str):
        """Save information in BUTL-R's long-term memory."""
        self.authorize_action(ActionRequest(
            action_type="write_memory",
            category=ActionCategory.MEMORY,
            target=f"{category}:{key}",
            requested_by="user",
            parameters={"category": category, "key": key},
        ))
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
        self.authorize_action(ActionRequest(
            action_type="delete_memory",
            category=ActionCategory.MEMORY,
            target=f"{category}:{key}",
            requested_by="user",
            parameters={"category": category, "key": key},
        ))
        return self.memory_manager.delete_memory(
            category,
            key,
        )

    def export_data(self) -> dict:
        """Export all user data for transparency and ownership."""
        return self.privacy_manager.export_user_data()

    def purge_all_history(self) -> int:
        """Purge all conversation history with audit logging."""
        self.audit_logger.log_event(
            event_type="privacy_purge",
            action_type="purge_all_conversations",
            decision="allowed",
            reason="User requested complete conversation purge",
            requested_by="user",
        )
        return self.privacy_manager.purge_all_conversations()

    def purge_all_memories(self) -> int:
        """Purge all memories with audit logging."""
        self.audit_logger.log_event(
            event_type="privacy_purge",
            action_type="purge_all_memories",
            decision="allowed",
            reason="User requested complete memory purge",
            requested_by="user",
        )
        return self.privacy_manager.purge_all_memories()
