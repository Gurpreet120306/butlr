import re
import logging
from typing import Optional, Any
from app.assistant.providers import BaseAIProvider

logger = logging.getLogger("BUTL-R.Intelligence.Debugger")


class SmartDebugger:
    """Detects, diagnoses, and suggests verified fixes for software, web, and script errors."""

    def __init__(self, ai_provider: Optional[BaseAIProvider] = None):
        self.ai_provider = ai_provider

    def diagnose_error(self, error_text: str, context: Optional[str] = None) -> dict[str, Any]:
        """Parse error text, identify root cause, and propose a concrete fix."""
        if not error_text or not error_text.strip():
            return {
                "detected": False,
                "error_type": "None",
                "explanation": "No error content provided for diagnosis.",
                "suggested_fix": "",
                "file": None,
                "line": None,
            }

        # Step 1: Rule-based regex extraction for rapid, guaranteed offline parsing
        rule_diagnostic = self._extract_rule_based_diagnosis(error_text)

        # Step 2: If an AI provider is connected, enhance diagnosis with local LLM reasoning
        ai_recommendation = None
        if self.ai_provider:
            try:
                prompt = (
                    f"You are an expert software debugger. Diagnose this error and provide a concise, direct fix:\n"
                    f"Error Output:\n{error_text}\n"
                )
                if context:
                    prompt += f"Context/Code:\n{context}\n"
                prompt += "\nFormat: 1. Cause (one sentence), 2. Fix (direct code or configuration change)."
                ai_reply = self.ai_provider.generate_reply([{"role": "user", "content": prompt}])
                if ai_reply and not ai_reply.startswith("Error"):
                    ai_recommendation = ai_reply.strip()
            except Exception as error:
                logger.debug(f"AI diagnostic fallback: {error}")

        if ai_recommendation:
            rule_diagnostic["ai_suggestion"] = ai_recommendation
            if not rule_diagnostic["suggested_fix"]:
                rule_diagnostic["suggested_fix"] = ai_recommendation

        return rule_diagnostic

    def _extract_rule_based_diagnosis(self, error_text: str) -> dict[str, Any]:
        """Extract error type, file, line number, and typical remediation."""
        error_type = "GenericError"
        file_path = None
        line_num = None
        explanation = "An error was encountered."
        suggested_fix = "Review the execution context and check input parameters."

        # Python Traceback detection
        py_match = re.search(r'File "([^"]+)", line (\d+), in (.+)\n\s*(.+)', error_text)
        if py_match:
            file_path = py_match.group(1)
            line_num = int(py_match.group(2))
            error_line = error_text.strip().splitlines()[-1]
            if ":" in error_line:
                error_type = error_line.split(":")[0].strip()
                explanation = f"Python {error_type} in {file_path} at line {line_num}."

        # JavaScript / Web Console error detection
        js_match = re.search(r"(Uncaught \w+Error|TypeError|ReferenceError|SyntaxError):\s*(.+)", error_text)
        if js_match:
            error_type = js_match.group(1)
            details = js_match.group(2)
            explanation = f"JavaScript runtime error: {details}."
            if "is not defined" in details:
                var_name = details.split(" ")[0]
                suggested_fix = f"Ensure variable '{var_name}' is declared (e.g., 'let {var_name}' or import statement) before use."
            elif "cannot read propert" in details.lower() or "is undefined" in details.lower() or "is null" in details.lower():
                suggested_fix = "Use optional chaining (e.g., 'object?.property') or check that the parent object exists."
            else:
                suggested_fix = "Inspect the variable state and ensure the target object/function is initialized."

        # HTTP Web errors (404, 500, CORS)
        if "404" in error_text:
            error_type = "HTTP_404_NotFound"
            explanation = "Requested web resource, API endpoint, or static asset could not be found."
            suggested_fix = "Verify the target URL route, asset filename path, or backend router registration."
        elif "CORS" in error_text or "Access-Control-Allow-Origin" in error_text:
            error_type = "CORS_Error"
            explanation = "Cross-Origin Resource Sharing policy blocked request from frontend."
            suggested_fix = "Add appropriate 'Access-Control-Allow-Origin' headers or configure CORS middleware in backend (e.g. CORSMiddleware in FastAPI)."
        elif "500" in error_text or "Internal Server Error" in error_text:
            error_type = "HTTP_500_InternalServerError"
            explanation = "Server-side unhandled exception during request processing."
            suggested_fix = "Inspect backend server logs and add error boundary or try/except handler."

        # Python ModuleNotFoundError
        if "ModuleNotFoundError" in error_text or "No module named" in error_text:
            mod_match = re.search(r"No module named ['\"]([^'\"]+)['\"]", error_text)
            mod_name = mod_match.group(1) if mod_match else "package"
            error_type = "ModuleNotFoundError"
            explanation = f"Required Python module '{mod_name}' is not installed in the active environment."
            suggested_fix = f"Install the missing dependency using: pip install {mod_name}"

        return {
            "detected": True,
            "error_type": error_type,
            "file": file_path,
            "line": line_num,
            "explanation": explanation,
            "suggested_fix": suggested_fix,
        }

    def verify_resolution(self, original_error: str, new_output_or_status: str) -> dict[str, Any]:
        """Verify whether an applied fix successfully cleared the original error."""
        if not new_output_or_status:
            return {"resolved": False, "reason": "No verification output provided."}

        # Check for success indicators
        success_indicators = ["success", "200 ok", "passed", "ok", "0 errors", "completed successfully"]
        is_success = any(ind in new_output_or_status.lower() for ind in success_indicators)

        # Check if the original error signature persists
        diag = self._extract_rule_based_diagnosis(original_error)
        original_type = diag["error_type"].lower()
        has_original_error = original_type in new_output_or_status.lower() if original_type != "genericerror" else False

        if is_success and not has_original_error:
            return {
                "resolved": True,
                "reason": "Execution completed without previous error signatures.",
            }
        elif has_original_error:
            return {
                "resolved": False,
                "reason": f"Original error '{diag['error_type']}' is still present in output.",
            }
        else:
            return {
                "resolved": not ("error" in new_output_or_status.lower() or "exception" in new_output_or_status.lower()),
                "reason": "Verification output evaluated.",
            }

    def analyze_website_error(self, url: str, console_logs: Optional[str] = None) -> dict[str, Any]:
        """Flagship demo: Diagnose errors on a website given URL and/or console output."""
        raw_error = console_logs or f"Inspecting website at {url}"
        diagnostic = self.diagnose_error(raw_error, context=f"Target URL: {url}")
        diagnostic["target_url"] = url
        return diagnostic
