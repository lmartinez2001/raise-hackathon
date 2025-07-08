from smolagents import ToolCallingAgent, InferenceClientModel
import yaml
import importlib

ANSWER_SYNTHESIZER_PROMPT = (
    "You are a summarization agent that takes multiple summarized transcript segments with a query "
    "and produces a cohesive, natural-language answer to the user's query.\n"
    "Input: a user query and a list of summarized segments.\n"
    "Output: a detailed, logically structured answer that addresses the question clearly."
)

class AnswerSynthesizerAgent(ToolCallingAgent):
    def __init__(self, model_id: str = "Qwen/Qwen2.5-Coder-32B-Instruct"):
        model = InferenceClientModel(model_id=model_id)
        
        prompt_templates = yaml.safe_load(
            importlib.resources.files("smolagents.prompts").joinpath("toolcalling_agent.yaml").read_text()
        )
        prompt_templates["system_prompt"] += ANSWER_SYNTHESIZER_PROMPT

        super().__init__(
            tools=[],
            model=model,
            name="answer_synthesizer_agent",
            description="Synthesizes a complete answer from a list of summarized segments.",
            prompt_templates=prompt_templates
        )
