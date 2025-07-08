from smolagents import InferenceClientModel

from agents.coordinator_agent import CoordinatorAgent

# from agent.agents.coordinator_agent import CoordinatorAgent


def chat_loop():
    print("🤖 Transcript QA Assistant (CLI) — type 'exit' to quit")

    # Initialize the agent once at the beginning
    agent = CoordinatorAgent(
        collection_name="database_oliver",
        database_path="output/database/test_db_oliver",
    )

    while True:
        user_input = input("\nYou: ")
        if user_input.strip().lower() in ("exit", "quit"):
            break

        try:
            print("\n🤖 Thinking...")
            response = agent.run(user_input)
            print("\nBot:\n", response)
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    chat_loop()
