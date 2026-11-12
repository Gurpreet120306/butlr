import logging
import subprocess
from typing import Optional

from app.security.policy import ActionCategory, ActionRequest, AuthorizationStatus, SecurityPolicy
from app.security.audit import AuditLogger

logger = logging.getLogger("BUTL-R.Tools.Apps")


class ApplicationManager:
    """Manages launching pre-approved desktop applications with default-deny security."""

    # Strict approved whitelist of benign utility applications
    APPROVED_APPLICATIONS = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "file_explorer": "explorer.exe",
        "explorer": "explorer.exe",
        "task_manager": "taskmgr.exe",
    }

    def __init__(self, security_policy: Optional[SecurityPolicy] = None, audit_logger: Optional[AuditLogger] = None):
        self.security_policy = security_policy if security_policy is not None else SecurityPolicy()
        self.audit_logger = audit_logger

    def get_approved_applications(self) -> list[str]:
        """Return list of allowed application names."""
        return list(self.APPROVED_APPLICATIONS.keys())

    def launch(self, app_name: str, user_confirmed: bool = False) -> tuple[bool, str]:
        """Launch an approved desktop application after security authorization."""
        normalized_name = app_name.strip().lower()

        # Default-deny: reject unapproved binaries upfront
        if normalized_name not in self.APPROVED_APPLICATIONS:
            msg = f"Default-deny: Application '{app_name}' is not in the approved whitelist."
            logger.warning(msg)
            if self.audit_logger:
                self.audit_logger.log_event(
                    event_type="app_launch_attempt",
                    action_type="launch_application",
                    decision="denied",
                    reason=msg,
                    target=app_name,
                )
            return False, msg

        # Check security policy
        request = ActionRequest(
            action_type="launch_application",
            category=ActionCategory.EXECUTE,
            target=normalized_name,
            requested_by="ai",
        )
        auth = self.security_policy.authorize(request)

        if auth.status == AuthorizationStatus.DENIED:
            return False, f"Permission denied: {auth.reason}"

        if auth.status == AuthorizationStatus.REQUIRES_CONFIRMATION and not user_confirmed:
            return False, f"Confirmation required: {auth.confirmation_prompt}"

        # Execute approved application safely
        executable = self.APPROVED_APPLICATIONS[normalized_name]
        try:
            subprocess.Popen([executable], shell=False)
            if self.audit_logger:
                self.audit_logger.log_event(
                    event_type="app_launched",
                    action_type="launch_application",
                    decision="allowed",
                    reason=f"Launched approved application '{normalized_name}'",
                    target=executable,
                )
            return True, f"Successfully launched {normalized_name}."
        except Exception as error:
            logger.error(f"Failed to launch application {executable}: {error}")
            return False, f"Error launching application: {error}"
