from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ActionCategory(Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    NETWORK = "network"
    SYSTEM = "system"
    MEMORY = "memory"


class AuthorizationStatus(Enum):
    ALLOWED = "allowed"
    DENIED = "denied"
    REQUIRES_CONFIRMATION = "requires_confirmation"


@dataclass
class ActionRequest:
    """Represents a proposed action from the AI, user, or tool."""
    action_type: str
    category: ActionCategory
    target: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    requested_by: str = "ai"  # "ai", "user", or "system"
    conversation_id: str = ""


@dataclass
class AuthorizationResult:
    """The security decision produced by the policy engine."""
    status: AuthorizationStatus
    reason: str
    action_type: str
    requires_confirmation: bool = False
    confirmation_prompt: str = ""


class SecurityPolicy:
    """Enforces default-deny access control and authorization policies."""

    # Actions that are unconditionally forbidden and cannot be overridden.
    HARD_DENIED_ACTIONS = {
        "unrestricted_shell",
        "execute_arbitrary_code",
        "dump_database_credentials",
        "expose_system_secrets",
    }

    # Standard default policies
    DEFAULT_PERMISSIONS = {
        # Safe read operations
        "read_memory": AuthorizationStatus.ALLOWED,
        "read_system_info": AuthorizationStatus.ALLOWED,
        "get_conversation_history": AuthorizationStatus.ALLOWED,
        "read_file": AuthorizationStatus.ALLOWED,
        "read_data": AuthorizationStatus.ALLOWED,

        # Sensitive operations requiring explicit confirmation
        "delete_memory": AuthorizationStatus.REQUIRES_CONFIRMATION,
        "write_memory": AuthorizationStatus.ALLOWED,
        "delete_conversation": AuthorizationStatus.REQUIRES_CONFIRMATION,
        "write_file": AuthorizationStatus.REQUIRES_CONFIRMATION,
        "delete_file": AuthorizationStatus.REQUIRES_CONFIRMATION,
        "launch_application": AuthorizationStatus.REQUIRES_CONFIRMATION,
        "send_network_request": AuthorizationStatus.REQUIRES_CONFIRMATION,
    }

    def __init__(self, custom_permissions: Optional[dict[str, AuthorizationStatus]] = None):
        self.permissions = dict(self.DEFAULT_PERMISSIONS)
        if custom_permissions:
            self.permissions.update(custom_permissions)

    def set_permission(self, action_type: str, status: AuthorizationStatus):
        """Update or revoke permission for an action."""
        if action_type in self.HARD_DENIED_ACTIONS:
            raise PermissionError(f"Action '{action_type}' is permanently denied by core security rules.")
        self.permissions[action_type] = status

    def authorize(self, request: ActionRequest) -> AuthorizationResult:
        """Evaluate an action request against the security policy.
        
        Strict default-deny: Any action not explicitly ALLOWED or REQUIRES_CONFIRMATION
        is automatically DENIED.
        """
        action = request.action_type.strip().lower()

        # 1. Hard-denied check (Cannot be bypassed)
        if action in self.HARD_DENIED_ACTIONS:
            return AuthorizationResult(
                status=AuthorizationStatus.DENIED,
                reason=f"Security violation: Action '{action}' is strictly forbidden.",
                action_type=action,
                requires_confirmation=False,
            )

        # 2. Strict check: AI suggestions cannot bypass confirmation for write/execute/system actions
        permission = self.permissions.get(action)

        # Default-deny rule: unregistered actions are always denied
        if permission is None:
            return AuthorizationResult(
                status=AuthorizationStatus.DENIED,
                reason=f"Default-deny: Action '{action}' is not registered or permitted.",
                action_type=action,
                requires_confirmation=False,
            )

        # 3. Action requires explicit user confirmation
        if permission == AuthorizationStatus.REQUIRES_CONFIRMATION:
            target_desc = f" on '{request.target}'" if request.target else ""
            prompt = f"BUTL-R needs your permission to perform '{action}'{target_desc}. Do you confirm? (yes/no)"
            return AuthorizationResult(
                status=AuthorizationStatus.REQUIRES_CONFIRMATION,
                reason="Sensitive operation requires explicit user confirmation.",
                action_type=action,
                requires_confirmation=True,
                confirmation_prompt=prompt,
            )

        # 4. Action is allowed
        if permission == AuthorizationStatus.ALLOWED:
            return AuthorizationResult(
                status=AuthorizationStatus.ALLOWED,
                reason="Action permitted by policy.",
                action_type=action,
                requires_confirmation=False,
            )

        # 5. Explicitly denied
        return AuthorizationResult(
            status=AuthorizationStatus.DENIED,
            reason=f"Action '{action}' is denied by user or system policy.",
            action_type=action,
            requires_confirmation=False,
        )
