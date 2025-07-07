from smolagents import ToolCallingAgent, InferenceClientModel
import yaml
import importlib

FOLLOWUP_PROMPT = (
    "You are a helpful assistant that proposes follow-up questions based on a user's original question "
    "and the answer provided. Your output should be a list of 2-5 thoughtful, specific, and relevant questions FROM THE USERS PERSPECTIVE"
    "that encourage deeper understanding or exploration."
)

class FollowUpQuestionAgent(ToolCallingAgent):
    def __init__(self):
        model = InferenceClientModel()

        prompt_templates = yaml.safe_load(
            importlib.resources.files("smolagents.prompts").joinpath("toolcalling_agent.yaml").read_text()
        )
        prompt_templates["system_prompt"] += FOLLOWUP_PROMPT

        super().__init__(
            tools=[],
            model=model,
            name="followup_question_agent",
            description="Generates useful follow-up questions based on the current query and answer.",
            prompt_templates=prompt_templates
        )
