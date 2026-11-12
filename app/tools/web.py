import json
import logging
import urllib.parse
import urllib.request
from typing import Optional

from app.security.policy import ActionCategory, ActionRequest, AuthorizationStatus, SecurityPolicy
from app.security.privacy import PrivacyManager
from app.security.sanitizer import sanitize_text

logger = logging.getLogger("BUTL-R.Tools.Web")


class WebSearchAssistant:
    """Safe internet research assistant strictly gated by privacy and security policies."""

    def __init__(
        self,
        privacy_manager: Optional[PrivacyManager] = None,
        security_policy: Optional[SecurityPolicy] = None,
        timeout: int = 10,
    ):
        self.privacy_manager = privacy_manager if privacy_manager is not None else PrivacyManager()
        self.security_policy = security_policy if security_policy is not None else SecurityPolicy()
        self.timeout = timeout

    def search(self, query: str, user_confirmed: bool = False) -> tuple[bool, str]:
        """Perform an authorized web query only when privacy permits and user confirms."""
        clean_query = query.strip()
        if not clean_query:
            return False, "Search query cannot be empty."

        # Privacy Check: If in local-only mode, internet access is strictly blocked
        if not self.privacy_manager.is_cloud_allowed():
            msg = "Privacy Policy: Internet access is blocked in Local-Only Mode. Enable cloud/network access in settings first."
            logger.warning(msg)
            return False, msg

        # Security Authorization Check
        request = ActionRequest(
            action_type="send_network_request",
            category=ActionCategory.NETWORK,
            target="web_search",
            parameters={"query": clean_query},
            requested_by="ai",
        )
        auth = self.security_policy.authorize(request)

        if auth.status == AuthorizationStatus.DENIED:
            return False, f"Permission denied: {auth.reason}"

        if auth.status == AuthorizationStatus.REQUIRES_CONFIRMATION and not user_confirmed:
            return False, f"Confirmation required: {auth.confirmation_prompt}"

        # Safe DuckDuckGo Instant Answer API (No tracking, no API key needed)
        encoded = urllib.parse.quote_plus(clean_query)
        url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "BUTL-R-Assistant/0.1.0"},
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            abstract = data.get("AbstractText", "")
            if abstract:
                return True, sanitize_text(abstract)

            # Fallback to related topics
            topics = data.get("RelatedTopics", [])
            if topics and isinstance(topics[0], dict) and "Text" in topics[0]:
                return True, sanitize_text(topics[0]["Text"])

            return True, f"Search completed for '{clean_query}', but no instant answer summary was found."

        except Exception as err:
            logger.error(f"Web query error: {err}")
            return False, f"Network error during web research: {err}"
