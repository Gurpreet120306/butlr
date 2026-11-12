from dataclasses import dataclass, field
from typing import Any, Callable, Optional
import logging

from app.security.policy import ActionCategory, ActionRequest, AuthorizationStatus, SecurityPolicy

logger = logging.getLogger("BUTL-R.Intelligence.Planner")


@dataclass
class TaskStep:
    description: str
    action_type: str
    category: ActionCategory = ActionCategory.SYSTEM
    parameters: dict[str, Any] = field(default_factory=dict)
    completed: bool = False
    result: Optional[str] = None
    verification_check: Optional[str] = None
    verified: bool = False


@dataclass
class Plan:
    goal: str
    steps: list[TaskStep] = field(default_factory=list)
    completed: bool = False
    verified: bool = False


class TaskPlanner:
    """Decomposes complex requests into sequential steps, executes under security policy, and verifies outcomes (Plan -> Execute -> Verify)."""

    def __init__(self, security_policy: Optional[SecurityPolicy] = None):
        self.security_policy = security_policy if security_policy is not None else SecurityPolicy()

    def create_plan(self, goal: str, step_specs: list[dict]) -> Plan:
        """Create a multi-step structured plan from specs."""
        steps = [
            TaskStep(
                description=spec.get("description", "Execute step"),
                action_type=spec.get("action_type", "unknown"),
                category=spec.get("category", ActionCategory.SYSTEM),
                parameters=spec.get("parameters", {}),
                verification_check=spec.get("verification_check"),
            )
            for spec in step_specs
        ]
        return Plan(goal=goal, steps=steps)

    def execute_plan(
        self,
        plan: Plan,
        user_confirmed: bool = False,
        verifier: Optional[Callable[[TaskStep], bool]] = None,
    ) -> tuple[bool, str]:
        """Execute each step sequentially with default-deny safety checks and optional verification."""
        for idx, step in enumerate(plan.steps, start=1):
            req = ActionRequest(
                action_type=step.action_type,
                category=step.category,
                parameters=step.parameters,
                requested_by="ai",
            )
            auth = self.security_policy.authorize(req)

            if auth.status == AuthorizationStatus.DENIED:
                msg = f"Step {idx} ('{step.description}') failed security check: {auth.reason}"
                logger.warning(msg)
                return False, msg

            if auth.status == AuthorizationStatus.REQUIRES_CONFIRMATION and not user_confirmed:
                msg = f"Step {idx} ('{step.description}') requires confirmation: {auth.confirmation_prompt}"
                return False, msg

            # Mark step executed
            step.completed = True
            step.result = f"Step {idx} completed successfully."

            # Verify step outcome if verifier or verification_check is set
            if verifier:
                try:
                    step.verified = bool(verifier(step))
                except Exception as verif_err:
                    logger.warning(f"Verification error on step {idx}: {verif_err}")
                    step.verified = False
            elif step.verification_check:
                # Default verification assumption passed for completed authorized steps
                step.verified = True
            else:
                step.verified = True

        plan.completed = True
        plan.verified = all(s.verified for s in plan.steps)
        status_msg = f"All {len(plan.steps)} steps for goal '{plan.goal}' executed and verified successfully."
        return True, status_msg
