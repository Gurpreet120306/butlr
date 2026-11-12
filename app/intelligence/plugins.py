import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from app.security.policy import ActionCategory, ActionRequest, AuthorizationStatus, SecurityPolicy

logger = logging.getLogger("BUTL-R.Intelligence.Plugins")


class BasePlugin(ABC):
    """Abstract interface for BUTL-R tool plugins."""

    name: str = "base_plugin"
    description: str = "Base plugin interface"
    action_type: str = "plugin_action"
    category: ActionCategory = ActionCategory.SYSTEM

    @abstractmethod
    def run(self, parameters: dict[str, Any]) -> Any:
        pass


class PluginRegistry:
    """Manages secure registration and execution of external tool plugins."""

    def __init__(self, security_policy: Optional[SecurityPolicy] = None):
        self.security_policy = security_policy if security_policy is not None else SecurityPolicy()
        self.plugins: dict[str, BasePlugin] = {}

    def register_plugin(self, plugin: BasePlugin, permission: AuthorizationStatus = AuthorizationStatus.ALLOWED) -> None:
        """Register a plugin and configure its security policy."""
        self.plugins[plugin.name] = plugin
        # Register the plugin action into security policy
        self.security_policy.set_permission(plugin.action_type, permission)
        logger.info(f"Registered plugin '{plugin.name}' (action: '{plugin.action_type}')")

    def execute_plugin(self, plugin_name: str, parameters: dict[str, Any], user_confirmed: bool = False) -> tuple[bool, Any]:
        """Execute a registered plugin after security policy authorization."""
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            return False, f"Plugin '{plugin_name}' not found."

        req = ActionRequest(
            action_type=plugin.action_type,
            category=plugin.category,
            parameters=parameters,
            requested_by="ai",
        )
        auth = self.security_policy.authorize(req)

        if auth.status == AuthorizationStatus.DENIED:
            return False, f"Security violation: {auth.reason}"

        if auth.status == AuthorizationStatus.REQUIRES_CONFIRMATION and not user_confirmed:
            return False, f"Confirmation required: {auth.confirmation_prompt}"

        try:
            result = plugin.run(parameters)
            return True, result
        except Exception as err:
            logger.error(f"Plugin '{plugin_name}' execution error: {err}")
            return False, f"Error executing plugin: {err}"
