import importlib
from smolagents import ToolCallingAgent, InferenceClientModel
import yaml
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), ""))

from video.agent_transcriber import ChromaQueryDatabaseTool
from slack.agent_slack import SlackQueryDatabaseTool
from smolagents import FinalAnswerTool
from typing import Dict, Any

RETRIEVAL_PROMPT = (
    f"You are an intelligent agent tasked with retrieving relevant video transcriptions or slack data"
    f"from a vector database. Based on the a user query:\n\n"
    f"You should:\n"
    f"1. Search the video transcriptions and slack ChromaDB databases using this query or related terms.\n"
    f"2. Decide which (if any) of the retrieved documents are relevant.\n"
    f"3. Return only those relevant documents in structured form.\n\n"
    f"Begin by issuing the appropriate tool calls to retrieve and process results."
)

class DocumentRetrievalAgent(ToolCallingAgent):
    """
    Agent that:
    1. Queries relevant documents from a ChromaDB collection using a natural language query.
    2. Decides which of the retrieved documents (if any) are relevant.
    3. Returns all relevant documents via the output tool.
    """

    def __init__(
        self,
        video_collection_name:str,
        video_database_path:str,
        slack_collection_name:str,
        slack_database_path:str,
        model_id: str = "meta-llama/Llama-3.3-70B-Instruct"
    ):
        # Inference model for DocumentRetrievalAgent.
        model = InferenceClientModel(model_id=model_id)
        
        # Agent tools for DocumentRetrievalAgent.
        self.video_transcription_tool = ChromaQueryDatabaseTool(collection_name=video_collection_name, database_path=video_database_path)
        self.slack_tool = SlackQueryDatabaseTool(collection_name=slack_collection_name, database_path=slack_database_path)
        
        # Formatter and prompt templates for DocumentRetrievalAgent.
        self.formatter = DocumentRetrievalFinalAnswerTool()
        prompt_templates = yaml.safe_load(
            importlib.resources.files("smolagents.prompts").joinpath("toolcalling_agent.yaml").read_text()
        )
        prompt_templates["system_prompt"] += RETRIEVAL_PROMPT
        
        # Instantiate agent.
        super().__init__(
            tools=[self.video_transcription_tool, self.slack_tool, self.formatter],
            model=model,
            name="document_retrieval_agent",
            description=(
                "Retrieves slack messages and transcript segments relevant to a user query, "
                "and returns structured information for use in downstream tasks."
            ),
            prompt_templates=prompt_templates
        )


class DocumentRetrievalFinalAnswerTool(FinalAnswerTool):
    description: str = (
        "Collects and returns a list of relevant documents. Each document should be a dictionary "
        "with structured fields such as 'document_id', 'text', 'score', 'id' etc."
        "Each document that is returned should be returned in full."
    )
    inputs: Dict[str, Any] = {
        "answer": {
            "type": "array",
            "description": "A list of relevant documents, each represented as a dictionary with structured fields."
        }
    }
    output_type: str = "array"


def test_document_retrieval_agent():
    """Unit tests for DocumentRetrievalAgent."""
    # Initialize test agent
    agent = DocumentRetrievalAgent(
        video_collection_name="database_oliver",
        video_database_path="output/database/test_db_oliver",
        slack_collection_name="slack_data",
        slack_database_path="output/database/slack"
    )
    
    # Test basic query
    test_query = "Find information about the project timeline"
    try:
        results = agent.run(test_query)
        assert isinstance(results, list), "Results should be a list"
        if len(results) > 0:
            assert isinstance(results[0], dict), "Each result should be a dictionary"
    except Exception as e:
        print(f"Basic query test failed: {str(e)}")
        raise

    # Test empty query - the agent may still return results for generic queries
    try:
        results = agent.run("")
        assert isinstance(results, list), "Empty query should return a list"
        # Note: Empty queries may still return results as the agent interprets them as generic queries
        print(f"Empty query returned {len(results)} results")
    except Exception as e:
        print(f"Empty query test failed: {str(e)}")
        raise

    # Test formatter tool
    formatter = DocumentRetrievalFinalAnswerTool()
    test_docs = [
        {"id": "1", "text": "test text", "score": 0.8},
        {"id": "2", "text": "more text", "score": 0.7}
    ]
    try:
        formatted = formatter.forward(test_docs)
        assert formatted == test_docs, "Formatter should return documents unchanged"
    except Exception as e:
        print(f"Formatter test failed: {str(e)}")
        raise

    print("All DocumentRetrievalAgent tests passed!")


if __name__ == "__main__":
    test_document_retrieval_agent()