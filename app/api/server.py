import logging
from typing import Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.assistant.engine import ButlrAssistant
from app.assistant.ollama_provider import OllamaProvider
from app.assistant.providers import BaseAIProvider
from app.core.database import MongoDB
from app.experimental.multimodal import MultimodalVisionAssistant
from app.intelligence.debugger import SmartDebugger
from app.intelligence.planner import TaskPlanner
from app.intelligence.productivity import ProductivityManager
from app.tools.screen import ScreenCaptureManager

logger = logging.getLogger("BUTL-R.API")


# Pydantic Request Models
class ChatRequest(BaseModel):
    message: str = Field(..., description="User query or voice transcript")
    conversation_id: Optional[str] = Field(None, description="Active conversation UUID")
    mode: str = Field("fast", description="'fast' or 'quality'")


class ScreenAnalysisRequest(BaseModel):
    prompt: str = Field(
        "Analyze what is shown on this screen and identify any errors, notifications, or active windows.",
        description="Prompt for vision model",
    )


class DebugRequest(BaseModel):
    error_text: str = Field(..., description="Error message, stack trace, or console log")
    context: Optional[str] = Field(None, description="Optional code snippet or URL context")


class WebsiteDebugRequest(BaseModel):
    url: str = Field(..., description="Target website URL")
    console_logs: Optional[str] = Field(None, description="Optional browser console output or network log")


class TaskCreateRequest(BaseModel):
    title: str = Field(..., description="Task title")
    category: str = Field("general", description="Category tag")
    priority: str = Field("medium", description="Priority level")


class PlanExecuteRequest(BaseModel):
    goal: str = Field(..., description="High-level user goal")
    steps: list[dict[str, Any]] = Field(..., description="List of step dictionaries")
    confirmed: bool = Field(False, description="User confirmation token for sensitive operations")


def create_app(
    assistant: Optional[ButlrAssistant] = None,
    db: Optional[MongoDB] = None,
    vision_assistant: Optional[MultimodalVisionAssistant] = None,
    debugger: Optional[SmartDebugger] = None,
    planner: Optional[TaskPlanner] = None,
    productivity: Optional[ProductivityManager] = None,
) -> FastAPI:
    """FastAPI application factory supporting dependency injection for testing and live production."""

    app = FastAPI(
        title="BUTL-R API",
        description="REST API Backend for BUTL-R Personal AI Desktop Assistant (HACKNAUTS 2.0)",
        version="2.0.0",
    )

    # Initialize services if not provided
    active_db = db or MongoDB()
    if assistant is not None:
        active_assistant = assistant
    else:
        default_provider = OllamaProvider(model="gemma3:1b")
        active_assistant = ButlrAssistant(provider=default_provider)

    active_vision = vision_assistant or MultimodalVisionAssistant()
    active_debugger = debugger or SmartDebugger(ai_provider=active_assistant.provider)
    active_planner = planner or TaskPlanner()
    active_productivity = productivity or ProductivityManager(db=active_db)

    @app.get("/")
    def index():
        return {
            "app": "BUTL-R",
            "version": "2.0.0",
            "tagline": "An AI Powered Desktop Assistant (HACKNAUTS 2.0)",
            "status": "online",
        }

    @app.get("/api/health")
    def health():
        provider = active_assistant.provider
        provider_name = getattr(provider, "model", "Custom")

        return {
            "status": "healthy",
            "ai_provider": provider_name,
            "mode": getattr(active_assistant, "active_mode", "fast"),
            "security_mode": "default-deny",
            "privacy": "local-only",
        }

    @app.post("/api/chat")
    def chat(req: ChatRequest):
        try:
            mode = req.mode.lower()
            if mode in {"fast", "quality"}:
                try:
                    active_assistant.set_mode(mode)
                except (RuntimeError, ValueError):
                    pass

            cid = req.conversation_id
            if not cid:
                cid = active_assistant.start_conversation()

            reply = active_assistant.send_message(
                conversation_id=cid,
                content=req.message,
            )
            return {
                "reply": reply,
                "conversation_id": cid,
                "mode": getattr(active_assistant, "active_mode", mode),
            }
        except Exception as error:
            logger.error(f"Chat endpoint error: {error}")
            raise HTTPException(status_code=500, detail=str(error))

    @app.post("/api/screen/capture-and-analyze")
    def capture_screen_and_analyze(req: ScreenAnalysisRequest):
        """Observe: Captures the user's active screen and analyzes it with multimodal vision."""
        try:
            screenshot_path, analysis = active_vision.capture_and_analyze(prompt=req.prompt)
            return {
                "screenshot_path": screenshot_path,
                "analysis": analysis,
                "model": active_vision.model,
            }
        except Exception as error:
            logger.error(f"Screen analysis error: {error}")
            raise HTTPException(status_code=500, detail=str(error))

    @app.post("/api/debug/analyze")
    def debug_error(req: DebugRequest):
        """Smart Debugging: Diagnose code/console error and provide suggested fix."""
        try:
            result = active_debugger.diagnose_error(error_text=req.error_text, context=req.context)
            return result
        except Exception as error:
            logger.error(f"Debugger error: {error}")
            raise HTTPException(status_code=500, detail=str(error))

    @app.post("/api/debug/website")
    def debug_website(req: WebsiteDebugRequest):
        """Flagship demo: 'Find the error on my website'."""
        try:
            result = active_debugger.analyze_website_error(url=req.url, console_logs=req.console_logs)
            return result
        except Exception as error:
            logger.error(f"Website debugger error: {error}")
            raise HTTPException(status_code=500, detail=str(error))

    @app.get("/api/tasks")
    def get_tasks():
        """Retrieve user productivity tasks."""
        try:
            tasks = active_productivity.list_tasks(include_completed=True)
            for t in tasks:
                if "_id" in t:
                    t["_id"] = str(t["_id"])
            return {"tasks": tasks, "count": len(tasks)}
        except Exception as error:
            logger.error(f"Tasks retrieval error: {error}")
            raise HTTPException(status_code=500, detail=str(error))

    @app.post("/api/tasks")
    def create_task(req: TaskCreateRequest):
        """Create a new user productivity task."""
        try:
            task = active_productivity.add_task(
                title=req.title,
            )
            return {"task_id": task["task_id"], "status": "created"}
        except Exception as error:
            logger.error(f"Task creation error: {error}")
            raise HTTPException(status_code=500, detail=str(error))

    @app.post("/api/plan/execute")
    def execute_plan(req: PlanExecuteRequest):
        """Decide & Execute: Execute a multi-step plan with security verification."""
        try:
            plan = active_planner.create_plan(goal=req.goal, step_specs=req.steps)
            success, message = active_planner.execute_plan(plan, user_confirmed=req.confirmed)
            return {
                "goal": req.goal,
                "success": success,
                "message": message,
                "steps_completed": sum(1 for s in plan.steps if s.completed),
                "total_steps": len(plan.steps),
                "verified": plan.verified,
            }
        except Exception as error:
            logger.error(f"Plan execution error: {error}")
            raise HTTPException(status_code=500, detail=str(error))

    return app
