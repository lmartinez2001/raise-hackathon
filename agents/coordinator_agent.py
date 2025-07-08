import yaml
import importlib
from typing import Any, List, Dict
from smolagents import ToolCallingAgent, InferenceClientModel, FinalAnswerTool
from .answer_synthesizer_agent import AnswerSynthesizerAgent
from .document_retrival_agent import DocumentRetrievalAgent
from .followup_agent import FollowUpQuestionAgent
from .segement_summarizer import SummarizerAgent


COORDINATOR_PROMPT = (
    "You are an intelligent agent that coordinates other agents to answer a user question. "
    "Your task:\n"
    "1. Use the DocumentRetrievalAgent to gather relevant transcript segments (potentially multiple times).)\n"
    "2. Use the SummarizerAgent to summarize each relevant transcript segment or slack message.\n"
    "3. Use the AnswerSynthesizerAgent to generate a detailed answer from the summaries.\n"
    "4. Use the FollowUpQuestionAgent to suggest follow-up questions.\n"
    "5. Answer the question and in a SEPARATE step use OurFinalAnswerTool to return a structured overview of the database entries relevant to the question.\n"
)

class CoordinatorAgent(ToolCallingAgent):
    def __init__(self, video_collection_name:str, video_database_path: str, slack_database_path: str, slack_collection_name: str, model_id: str = "meta-llama/Llama-3.3-70B-Instruct"):
        model = InferenceClientModel(model_id=model_id)
        self.final_formatter = OurFinalAnswerTool()
        
        # Initialize agents
        agents = [
            DocumentRetrievalAgent(video_collection_name, video_database_path, slack_collection_name, slack_database_path, model_id=model_id), 
            SummarizerAgent(model_id=model_id),
            AnswerSynthesizerAgent(model_id=model_id), 
            FollowUpQuestionAgent(model_id=model_id)
        ]
        
        prompt_templates = yaml.safe_load(
            importlib.resources.files("smolagents.prompts").joinpath("toolcalling_agent.yaml").read_text()
        )
        prompt_templates["system_prompt"] += COORDINATOR_PROMPT
    
        super().__init__(
            tools=[self.final_formatter],
            managed_agents=agents,
            model=model,
            name="coordinator_agent",
            description="Coordinates all agents to answer a user query and format the final output.",
            prompt_templates=prompt_templates
        )

class OurFinalAnswerTool(FinalAnswerTool):
    """
    A tool that formats a final answer with an explanation, references to relevant documents (eg video segments, 
    slack messages, and video links with timestamps, or slack messages with links etc)

    Args:
        answer (str): The generated explanation text.
        database_content (List[Dict[str, Any]]): A list of dictionaries, each containing information about a document.
                                         For video segments: 'id', 'segment_idx', 'timestamp_range', 'data_type=segment' and 'text'.
                                         For Slack messages: 'channel_name', 'username', 'timestamp', 'data_type=slack_message' and 'text'.
        followups (List[str]): a list of followup questions.

    Returns:
        str: A formatted string containing the final answer with references and links and follow up questions.

    Example:
        answer = "The primary purpose of the meeting was to discuss the new project timeline."
        database_content = [
            {
                "id": "data/video_short_2_segment_0062.mp4",
                "timestamp_range": "[02:33 - 02:35]",
                "text": "In order to make the connection.",
                "data_type": "segment"
            },
            {
                "channel_name": "general",
                "username": "john_doe",
                "timestamp": "1234567890.123456",
                "text": "We need to discuss the project timeline",
                "data_type": "slack_message"
            }
        ]
        followups = ["What else was discussed in the meeting?", "What were the conclusions?"]
    """
    name = "final_answer"
    description = (
        "Formats the final answer with explanation, along with segment references, "
        "timestamps, and video segment links for videos, or message reference, username, channel name and timestamp for slack content"
    )
    inputs = {
        "answer": {"type": "string", "description": "Generated explanation text"},
        "database_content": {
            "type": "array",
            "description": "List of database entry dicts including id, timestamp_range, data_type=segment and text for videos OR channel_name, username, timestamp, data_type=slack_message and text for Slack messages"
        },
        "followups": {"type": "array", "description": "List of follow up questions based on the query"}
    }
    output_type = "string"

    def forward(self, answer: str, database_content: List[Dict[str, Any]], followups: List[str]) -> str:
        output = [f"**Answer:** {answer}", "", "**References & Evidence:**"]
        
        for content in database_content:
            # Check if this is a video segment (has video_segment_file)
            if content.get("data_type", "") == "segment":
                file = content["id"]
                time = content.get("timestamp_range", "")
                text = content.get("text", "")
                note = f'- 📹 `{file}` {time}\n    • "{text}"'
                output.append(note)
            
            elif content.get("data_type", "") == "slack_message":
                channel = content.get("channel_name", "Unknown")
                username = content.get("username", "Unknown")
                timestamp = content.get("timestamp", "")
                text = content.get("text", "")
                # Format timestamp if available
                time_display = ""
                if timestamp:
                    try:
                        # Convert Slack timestamp to readable format
                        import datetime
                        ts_float = float(timestamp)
                        dt = datetime.datetime.fromtimestamp(ts_float)
                        time_display = f" [{dt.strftime('%Y-%m-%d %H:%M:%S')}]"
                    except:
                        time_display = f" [{timestamp}]"
                
                # Create the note.
                note = f'- 💬 `#{channel}` {username}{time_display}\n    • "{text}"'
                output.append(note)
            
            # Fallback for unknown format
            else:
                text = content.get("text", "")
                note = f'- 📄 "{text}"'
                output.append(note)

        output.append("\n**Suggested Follow-up Questions:**")
        for q in followups:
            output.append(f"- {q}")

        return "\n".join(output)
