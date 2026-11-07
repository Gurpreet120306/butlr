
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
    print("Current mode: QUALITY")
    print("\nCommands:")
    print("  fast     - Switch to Fast Mode")
    print("  quality  - Switch to Quality Mode")
    print("  mode     - Show current mode")
    print("  new      - Start a new conversation")
    print("  exit     - End conversation\n")

    while True:
        user_input = input("YOU: ").strip()

        if user_input.lower() in {"exit", "quit", "bye"}:
            print("\nBUTL-R: Goodbye! Talk to you soon.")
            break

        if not user_input:
            print("Please enter a message.")
            continue

        command = user_input.lower()

        if command in {"fast", "quality"}:
            try:
                model = assistant.set_mode(command)

                print(
                    f"\nBUTL-R: Switched to "
                    f"{command.upper()} MODE ({model}).\n"
                )

            except Exception as error:
                print(f"\nBUTL-R ERROR: {error}\n")

            continue

        if command == "mode":
            print(
                f"\nBUTL-R: Current mode is "
                f"{assistant.get_mode().upper()}.\n"
            )
            continue

        if command == "new":
            conversation_id = assistant.start_conversation()
            print("\nBUTL-R: Started a new conversation.\n")
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
