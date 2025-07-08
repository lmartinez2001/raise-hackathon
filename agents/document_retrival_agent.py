import importlib
from smolagents import ToolCallingAgent, InferenceClientModel
import yaml
from video.agent_transcriber import ChromaQueryDatabaseTool
from smolagents import FinalAnswerTool

RETRIEVAL_PROMPT = (
    f"You are an intelligent agent tasked with retrieving relevant transcript segments "
    f"from a vector database. Based on the a user query:\n\n"
    f"You should:\n"
    f"1. Search the ChromaDB using this query or related terms.\n"
    f"2. Decide which (if any) of the retrieved documents are relevant.\n"
    f"3. Return only those relevant documents in structured form.\n\n"
    f"Begin by issuing the appropriate tool calls to retrieve and process results."
)

class DocumentRetrievalAgent(ToolCallingAgent):
    """
    Agent that:
    1. Queries relevant segments from a ChromaDB collection using a natural language query.
    2. Decides which of the retrieved documents (if any) are relevant.
    3. Returns all relevant documents via the output tool.
    """

    def __init__(self, collection_name:str, database_path:str, model_id: str = "Qwen/Qwen2.5-Coder-32B-Instruct"):
        model = InferenceClientModel(model_id=model_id)
        self.chroma_tool = ChromaQueryDatabaseTool(collection_name=collection_name, database_path=database_path)
        self.formatter = DocumentRetrievalFinalAnswerTool()
        prompt_templates = yaml.safe_load(
            importlib.resources.files("smolagents.prompts").joinpath("toolcalling_agent.yaml").read_text()
        )
        prompt_templates["system_prompt"] += RETRIEVAL_PROMPT
        super().__init__(
            tools=[self.chroma_tool, self.formatter],
            model=model,
            name="document_retrieval_agent",
            description=(
                "Retrieves transcript segments relevant to a user query, "
                "and returns structured information for use in downstream tasks."
            ),
            prompt_templates=prompt_templates
        )


class DocumentRetrievalFinalAnswerTool(FinalAnswerTool):
    description = (
        "Collects and returns a list of relevant documents. Each document should be a dictionary "
        "with structured fields such as 'document_id', 'text', 'score', video id etc."
        "Each document that is returned should be returned in full."
    )
    inputs = {
        "answer": {
            "type": "array",
            "description": "A list of relevant documents, each represented as a dictionary with structured fields."
        }
    }
    output_type = "array"
