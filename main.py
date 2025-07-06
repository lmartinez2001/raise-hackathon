from smolagents import InferenceClientModel, ToolCallingAgent, PromptTemplates
from raise_hackathon.tools.chroma_tool import ChromaQueryTool
from raise_hackathon.tools.final_answer_tool import VideoFinalAnswerTool
# from raise_hackathon.prompts import system_prompt

# Use default HF-hosted model
model = InferenceClientModel()

agent = ToolCallingAgent(
    model=model,
    tools=[ChromaQueryTool(), VideoFinalAnswerTool()],
    # prompt_templates=PromptTemplates(system_prompt=system_prompt)
)

def chat_loop():
    print("🤖 Meeting Chatbot (CLI) — type 'exit' to quit")
    while True:
        user_input = input("\nYou: ")
        if user_input.strip().lower() in ("exit", "quit"):
            break
        answer = agent.run(user_input)
        print("\nBot:\n", answer)

if __name__ == "__main__":
    chat_loop()
