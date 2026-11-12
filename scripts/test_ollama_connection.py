import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.assistant.models import Message
from app.assistant.ollama_provider import OllamaProvider


def main():
    print("=" * 50)
    print("       BUTL-R PYTHON AI CONNECTION TEST")
    print("=" * 50)

    provider = OllamaProvider(
        model="gemma3:4b",
        timeout=180,
    )

    message = Message(
        role="user",
        content="Reply with exactly: BUTL-R online"
    )

    print("\nSending a short request to Gemma 3...", flush=True)

    start_time = time.perf_counter()

    try:
        response = provider.generate_reply([message])

        elapsed = time.perf_counter() - start_time

        print("\nBUTL-R:", flush=True)
        print(response, flush=True)
        print(f"\nResponse time: {elapsed:.2f} seconds")
        print("\nAI CONNECTION: SUCCESS")

    except Exception as error:
        print(f"\nAI CONNECTION FAILED: {error}")

    print("=" * 50)


if __name__ == "__main__":
    main()