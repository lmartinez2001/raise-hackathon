import yaml
import importlib
from typing import Any, List, Dict
from smolagents import ToolCallingAgent, InferenceClientModel, FinalAnswerTool
from agent.agents.answer_synthesizer_agent import AnswerSynthesizerAgent
from agent.agents.document_retrival_agent import DocumentRetrievalAgent
from agent.agents.followup_agent import FollowUpQuestionAgent
from agent.agents.segement_summarizer import SummarizerAgent


COORDINATOR_PROMPT = (
    "You are an intelligent agent that coordinates other agents to answer a user question. "
    "Your task:\n"
    "1. Use the DocumentRetrievalAgent to gather relevant transcript segments (potentially multiple times).)\n"
    "2. Use the SummarizerAgent to summarize each relevant transcript segment.\n"
    "3. Use the AnswerSynthesizerAgent to generate a detailed answer from the summaries.\n"
    "4. Use the FollowUpQuestionAgent to suggest follow-up questions.\n"
    "5. Format everything using OurFinalAnswerTool.\n"
)

class CoordinatorAgent(ToolCallingAgent):
    def __init__(self, collection_name:str, database_path:str):
        model = InferenceClientModel()
        self.final_formatter = OurFinalAnswerTool()
        
        prompt_templates = yaml.safe_load(
            importlib.resources.files("smolagents.prompts").joinpath("toolcalling_agent.yaml").read_text()
        )
        prompt_templates["system_prompt"] += COORDINATOR_PROMPT
    
        super().__init__(
            tools=[self.final_formatter],
            managed_agents=[DocumentRetrievalAgent(collection_name, database_path), SummarizerAgent(), AnswerSynthesizerAgent(), FollowUpQuestionAgent()],
            model=model,
            name="coordinator_agent",
            description="Coordinates all agents to answer a user query and format the final output.",
            prompt_templates=prompt_templates
        )

class OurFinalAnswerTool(FinalAnswerTool):
    """
    A tool that formats a final answer with an explanation, references to relevant documents (eg video segments, 
    and video links with timestamps, or slack messages with links etc)

    Args:
        answer (str): The generated explanation text.
        segments (List[Dict[str, Any]]): A list of dictionaries, each containing information about a document( eg video segment,
                                          including 'video_segment_file', 'timestamp_range', and 'text'.)
        followups (List[str]): a list of followup questions.

    Returns:
        str: A formatted string containing the final answer with references and links and follow up questions.

    Example:
        answer = "The primary purpose of the meeting was to discuss the new project timeline."
        segments = [
            {
                "video_segment_file": "data/video_short_2_segment_0062.mp4",
                "timestamp_range": "[02:33 - 02:35]",
                "text": "In order to make the connection."
            },
            {
                "video_segment_file": "data/video_short_2_segment_0067.mp4",
                "timestamp_range": "[02:46 - 02:49]",
                "text": "That we now have initialized a session."
            }
        ]
        followups = ["What else was discussed in the meeting?", "What were the conclusions?"]
    """
    name = "final_answer"
    description = (
        "Formats the final answer with explanation, segment references, "
        "timestamps, and video segment links."
    )
    inputs = {
        "answer": {"type": "string", "description": "Generated explanation text"},
        "segments": {
            "type": "array",
            "description": "List of segment dicts including video_segment_file, timestamp_range, text"
        },
        "followups": {"type": "array", "description": "List of follow up questions based on the query"}
    }
    output_type = "string"

    def forward(self, answer: str, segments: List[Dict[str, Any]], followups: List[str]) -> str:
        output = [f"**Answer:** {answer}", "", "**References & Evidence:**"]
        for seg in segments:
            file = seg["video_segment_file"]
            time = seg.get("timestamp_range", "")
            text = seg.get("text", "")
            note = f'- 📹 `{file}` {time}\n    • "{text}"'
            output.append(note)

        output.append("\n**Suggested Follow-up Questions:**")
        for q in followups:
            output.append(f"- {q}")

        return "\n".join(output)
