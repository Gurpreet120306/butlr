from pathlib import Path
from typing import Optional


class DocumentAssistant:
    """Reads, analyzes, and extracts key insights from local supported documents."""

    SUPPORTED_EXTENSIONS = {".txt", ".md", ".json", ".csv", ".py", ".log"}

    def summarize_document(self, file_path: str, max_chars: int = 2000) -> dict:
        """Analyze a document and extract basic metrics and preview."""
        path = Path(file_path)
        if not path.is_file():
            return {"error": f"File '{file_path}' not found."}

        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return {"error": f"Unsupported document type: {path.suffix}"}

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            words = content.split()
            lines = content.splitlines()

            # Generate structured summary metrics
            return {
                "file_name": path.name,
                "file_size_bytes": path.stat().st_size,
                "line_count": len(lines),
                "word_count": len(words),
                "preview": content[:max_chars],
            }
        except Exception as error:
            return {"error": f"Error reading document: {error}"}

    def search_in_document(self, file_path: str, search_query: str) -> list[tuple[int, str]]:
        """Find matching lines and line numbers containing search_query."""
        path = Path(file_path)
        if not path.is_file():
            return []

        matches = []
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            for idx, line in enumerate(lines, start=1):
                if search_query.lower() in line.lower():
                    matches.append((idx, line.strip()))
            return matches
        except Exception:
            return []
