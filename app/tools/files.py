import logging
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.security.policy import ActionCategory, ActionRequest, AuthorizationStatus, SecurityPolicy
from app.security.audit import AuditLogger

logger = logging.getLogger("BUTL-R.Tools.Files")


class SafeFileManager:
    """Safe, sandboxed file and folder assistant with path-traversal protection."""

    def __init__(
        self,
        allowed_roots: Optional[list[Path]] = None,
        security_policy: Optional[SecurityPolicy] = None,
        audit_logger: Optional[AuditLogger] = None,
    ):
        # Default sandbox roots: project root and project data directory
        self.allowed_roots = allowed_roots or [settings.ROOT_DIR]
        self.security_policy = security_policy if security_policy is not None else SecurityPolicy()
        self.audit_logger = audit_logger

    def _is_path_allowed(self, target_path: Path) -> bool:
        """Validate path resolves within approved sandbox boundaries."""
        try:
            resolved = target_path.resolve()
            return any(
                resolved == root.resolve() or root.resolve() in resolved.parents
                for root in self.allowed_roots
            )
        except Exception:
            return False

    def list_directory(self, dir_path: Optional[str] = None) -> tuple[bool, list[str]]:
        """List files and folders in an approved directory."""
        target = Path(dir_path) if dir_path else settings.ROOT_DIR
        if not self._is_path_allowed(target) or not target.is_dir():
            return False, []

        items = [f.name + ("/" if f.is_dir() else "") for f in target.iterdir()]
        return True, sorted(items)

    def read_text_file(self, file_path: str, max_chars: int = 10000) -> tuple[bool, str]:
        """Safely read content from an approved text file."""
        target = Path(file_path)
        if not self._is_path_allowed(target):
            msg = f"Security error: Access to path '{file_path}' is outside approved directories."
            logger.warning(msg)
            return False, msg

        if not target.is_file():
            return False, f"File not found: {file_path}"

        try:
            content = target.read_text(encoding="utf-8", errors="replace")
            return True, content[:max_chars]
        except Exception as error:
            return False, f"Failed to read file: {error}"

    def search_files(self, query: str, extension: Optional[str] = None) -> list[str]:
        """Search for filenames containing a query string within approved directories."""
        matches = []
        pattern = f"*{extension}" if extension else "*"

        for root in self.allowed_roots:
            if not root.exists():
                continue
            for path in root.rglob(pattern):
                if path.is_file() and query.lower() in path.name.lower():
                    matches.append(str(path.relative_to(root)))
                if len(matches) >= 50:  # Limit results
                    break

        return sorted(matches)
