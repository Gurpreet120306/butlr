import time
from typing import Any, Callable


class CPUBenchmarker:
    """Measures local CPU AI inference speed and resource efficiency."""

    @staticmethod
    def benchmark_inference(func: Callable[[str], str], test_prompt: str = "Explain sorting in 2 sentences.") -> dict[str, Any]:
        """Benchmark execution time and estimate generation speed."""
        start_time = time.perf_counter()
        response = func(test_prompt)
        elapsed = time.perf_counter() - start_time

        words = len(response.split()) if isinstance(response, str) else 0
        approx_tokens = int(words * 1.3)
        tokens_per_second = approx_tokens / elapsed if elapsed > 0 else 0

        return {
            "elapsed_seconds": round(elapsed, 3),
            "estimated_tokens": approx_tokens,
            "tokens_per_second": round(tokens_per_second, 2),
            "response_preview": response[:80] if isinstance(response, str) else "",
        }
