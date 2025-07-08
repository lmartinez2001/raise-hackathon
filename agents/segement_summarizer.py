import importlib
from smolagents import ToolCallingAgent, InferenceClientModel
import yaml

SUMMARIZER_PROMPT = (
            f"Given a question and database entry, summarize the database entry:\n\n"
            "Summary:"
        )

class SummarizerAgent(ToolCallingAgent):
    """
    Agent that summarizes a database entry in the context of a user question.
    
    Both the database entry (with all its context and metadata) and question should be provided.
    """
    def __init__(self, model_id: str = "meta-llama/Llama-3.3-70B-Instruct"):
        model = InferenceClientModel(model_id=model_id)
        prompt_templates = yaml.safe_load(
            importlib.resources.files("smolagents.prompts").joinpath("toolcalling_agent.yaml").read_text()
        )
        prompt_templates["system_prompt"] += SUMMARIZER_PROMPT
        super().__init__(
            tools=[],
            model=model,
            name="summarizer_agent",
            description=(
                "An agent that summarizes individual database entries in the context of a user question. "
                "It is designed to extract the most relevant information from each database entry based on the query, "
                "preserving key context and metadata to support downstream synthesis. Pass a single database entry into it"
            ),
            prompt_templates=prompt_templates
        )


