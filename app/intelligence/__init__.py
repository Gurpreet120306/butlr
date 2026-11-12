"""BUTL-R Advanced Intelligence: Task Planning, Automation, Productivity, Document Understanding, and Smart Debugging."""

from app.intelligence.planner import TaskPlanner, Plan, TaskStep
from app.intelligence.plugins import PluginRegistry, BasePlugin
from app.intelligence.productivity import ProductivityManager
from app.intelligence.docs import DocumentAssistant
from app.intelligence.debugger import SmartDebugger

__all__ = [
    "TaskPlanner",
    "Plan",
    "TaskStep",
    "PluginRegistry",
    "BasePlugin",
    "ProductivityManager",
    "DocumentAssistant",
    "SmartDebugger",
]
