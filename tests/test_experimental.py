import base64
import unittest
from pathlib import Path

from app.experimental.multimodal import MultimodalVisionAssistant
from app.experimental.multi_agent import AgentOrchestrator, SpecializedAgent
from app.experimental.optimization import CPUBenchmarker


class TestExperimentalSubsystem(unittest.TestCase):

    def test_vision_image_encoder(self):
        """Image encoder converts local image files into base64 string."""
        assistant = MultimodalVisionAssistant()
        # Create a small dummy file to test encoding
        dummy_file = Path(__file__).resolve().parent / "test_dummy.png"
        dummy_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")

        try:
            b64_str = assistant.encode_image(str(dummy_file))
            decoded = base64.b64decode(b64_str)
            self.assertEqual(decoded[:4], b"\x89PNG")
        finally:
            if dummy_file.exists():
                dummy_file.unlink()

    def test_multi_agent_orchestration(self):
        """Orchestrator routes requests to specialized personas."""
        orchestrator = AgentOrchestrator()

        coder_result = orchestrator.route_task("coder", "Refactor database query")
        self.assertIn("coder", coder_result.lower())

        research_result = orchestrator.route_task("researcher", "Find papers on neural TTS")
        self.assertIn("researcher", research_result.lower())

    def test_cpu_benchmarker(self):
        """Benchmarker measures latency and estimates token rate."""
        def dummy_model(prompt):
            return "Python is a versatile programming language used for web development, data science, and AI."

        metrics = CPUBenchmarker.benchmark_inference(dummy_model, "What is Python?")
        self.assertIn("elapsed_seconds", metrics)
        self.assertGreater(metrics["estimated_tokens"], 5)
        self.assertGreaterEqual(metrics["tokens_per_second"], 0)


if __name__ == "__main__":
    unittest.main()
