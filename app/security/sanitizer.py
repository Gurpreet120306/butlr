import re

# Prompt injection signatures to protect against model hijacking
PROMPT_INJECTION_PATTERNS = [
    r"ignore (all )?(previous|prior) (instructions|directions|prompts)",
    r"disregard (all )?(previous|prior) (instructions|directions|prompts)",
    r"system prompt override",
    r"you are now (in )?(developer|dan|jailbreak|root|sudo) mode",
    r"bypass (all )?(safety|security|content) filters",
    r"reveal (your |the )?(system prompt|initial prompt|core instructions)",
    r"print (your |the )?(system prompt|hidden prompt)",
]

# Sensitive patterns to redact
REDACTION_PATTERNS = [
    (r"(?i)(api[_-]?key|access[_-]?token|secret[_-]?key|password|passwd|pin)\s*[:=]\s*['\"]?([^\s'\"]+)['\"]?", r"\1: [REDACTED]"),
    (r"\b[A-Za-z0-9_-]{32,}\b", "[REDACTED_TOKEN]"),  # Long high-entropy tokens
    (r"\b(?:\d{4}[ -]?){3}\d{4}\b", "[REDACTED_CARD]"),  # Credit card numbers
]

SENSITIVE_KEY_NAMES = {
    "password", "passwd", "secret", "token", "api_key",
    "apikey", "pin", "auth", "credential", "private_key",
}


def detect_prompt_injection(text: str) -> tuple[bool, str]:
    """Check text for known prompt injection attempts.
    
    Returns:
        (is_injection, reason)
    """
    if not isinstance(text, str) or not text.strip():
        return False, ""

    normalized = text.lower().strip()

    for pattern in PROMPT_INJECTION_PATTERNS:
        match = re.search(pattern, normalized)
        if match:
            return True, f"Detected potential prompt injection pattern: '{match.group(0)}'"

    return False, ""


def sanitize_text(text: str) -> str:
    """Redact passwords, secrets, and high-entropy tokens from text."""
    if not isinstance(text, str):
        return text

    sanitized = text
    for pattern, replacement in REDACTION_PATTERNS:
        sanitized = re.sub(pattern, replacement, sanitized)

    return sanitized


def sanitize_parameters(params: dict) -> dict:
    """Recursively scrub sensitive keys and values from parameter dictionaries."""
    if not isinstance(params, dict):
        return {}

    cleaned = {}
    for key, value in params.items():
        key_lower = str(key).lower()
        if any(sensitive in key_lower for sensitive in SENSITIVE_KEY_NAMES):
            cleaned[key] = "[REDACTED]"
        elif isinstance(value, dict):
            cleaned[key] = sanitize_parameters(value)
        elif isinstance(value, str):
            cleaned[key] = sanitize_text(value)
        else:
            cleaned[key] = value

    return cleaned
