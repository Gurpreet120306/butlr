from app.assistant.engine import ButlrAssistant
from app.assistant.ollama_provider import OllamaProvider


def main():
    print("=" * 55)
    print("          BUTL-R PERSONAL AI ASSISTANT")
    print("=" * 55)

    provider = OllamaProvider(
        model="gemma3:4b",
        timeout=180,
    )

    assistant = ButlrAssistant(provider=provider)

    conversation_id = assistant.start_conversation()

    print("\nBUTL-R is online!")
    print("Type 'exit' to end the conversation.\n")

    while True:
        user_input = input("YOU: ").strip()

        if user_input.lower() in {"exit", "quit", "bye"}:
            print("\nBUTL-R: Goodbye! Talk to you soon.")
            break

        if not user_input:
            print("Please enter a message.")
            continue

        try:
            reply = assistant.send_message(
                conversation_id,
                user_input,
            )

            print(f"\nBUTL-R: {reply}\n")

        except Exception as error:
            print(f"\nBUTL-R ERROR: {error}\n")


if __name__ == "__main__":
    main()