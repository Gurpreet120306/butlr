from dataclasses import dataclass
from typing import Optional, Callable


@dataclass
class SpecializedAgent:
    """Specialized AI persona tailored for a specific domain."""
    name: str
    role: str
    system_prompt: str
    handler: Optional[Callable[[str], str]] = None

    def execute_task(self, task: str) -> str:
        if self.handler:
            return self.handler(task)
        return f"[{self.name} - {self.role}] Completed task: '{task}'"


class AgentOrchestrator:
    """Coordinates and delegates requests across a team of specialized AI agents."""

    def __init__(self):
        self.agents: dict[str, SpecializedAgent] = {}
        self._register_default_agents()

    def _register_default_agents(self):
        self.register_agent(SpecializedAgent(
            name="researcher",
            role="Information Specialist",
            system_prompt="You are a meticulous researcher who summarizes facts clearly.",
        ))
        self.register_agent(SpecializedAgent(
            name="coder",
            role="Software Engineer",
            system_prompt="You write robust, secure, and clean Python code.",
        ))
        self.register_agent(SpecializedAgent(
            name="critic",
            role="Safety & Verification Reviewer",
            system_prompt="You review proposed actions for security risks and errors.",
        ))

    def register_agent(self, agent: SpecializedAgent):
        self.agents[agent.name] = agent

    def route_task(self, domain: str, task: str) -> str:
        """Route a task to the appropriate agent persona."""
        domain_key = domain.lower().strip()
        agent = self.agents.get(domain_key)
        if not agent:
            # Fallback to general coordinator
            return f"No specialized agent for '{domain}'. General assistant will handle: '{task}'"
        return agent.execute_task(task)
