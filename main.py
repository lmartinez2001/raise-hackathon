from smolagents import InferenceClientModel
from agents.coordinator_agent import CoordinatorAgent

def chat_loop():
    print("🤖 Transcript QA Assistant (CLI) — type 'exit' to quit")
    
    # Initialize the agent once at the beginning
    model = InferenceClientModel()
    agent = CoordinatorAgent(video_collection_name="video_transcriptions", video_database_path="output/database/meetings", slack_collection_name="slack_data", slack_database_path="output/database/slack")
    
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
