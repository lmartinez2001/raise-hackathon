import json
from typing import Dict, List, Any
from smolagents import CodeAgent, InferenceClientModel
from tools.chroma_tool import ChromaDBTool
from tools.md_scan_tool import MarkdownScanTool
from tools.file_tree_tool import FileTreeTool
from tools.slack_chroma_tools import SlackChromaTool


class ChatAgent:
    def __init__(
        self,
        drive_chroma_collection: str = "documents",
        slack_chroma_collection: str = "slack",
        chroma_persist_path: str = "./chroma_db",
        wiki_directory: str = "./wiki",
    ):

        self.model = InferenceClientModel()
        self.chroma_tool = ChromaDBTool(drive_chroma_collection, chroma_persist_path)
        self.slack_tool = SlackChromaDBTool(
            slack_chroma_collection, chroma_persist_path
        )
        self.markdown_tool = MarkdownScanTool(wiki_directory)
        self.file_tree_tool = FileTreeTool()

        self.agent = CodeAgent(
            tools=[self.chroma_tool, self.markdown_tool], model=self.model, max_steps=10
        )

    def process_query(self, user_query: str) -> Dict[str, Any]:
        agent_prompt = f"""
        You are a helpful research assistant. Answer the user's question using the available tools.
        
        Use chromadb_search to find relevant documents in the vector database.
        Use markdown_scan to search through wiki markdown files.
        
        Always gather information from both tools before providing your final answer.
        Format your response as a comprehensive answer with source links.
        
        User query: {user_query}
        """

        try:
            result = self.agent.run(agent_prompt)
            return self._format_response(result, user_query)
        except Exception as e:
            return {
                "answer": f"Error processing query: {str(e)}",
                "sources": [],
                "success": False,
            }

    def _format_response(
        self, agent_result: str, original_query: str
    ) -> Dict[str, Any]:
        sources = self._extract_sources_from_logs()

        return {
            "answer": agent_result,
            "sources": sources,
            "query": original_query,
            "success": True,
        }

    def _extract_sources_from_logs(self) -> List[Dict[str, str]]:
        sources = []

        if hasattr(self.agent, "logs"):
            for log in self.agent.logs:
                if isinstance(log, dict) and "tool_output" in log:
                    try:
                        tool_data = json.loads(log["tool_output"])
                        if "results" in tool_data:
                            for result in tool_data["results"]:
                                sources.append(
                                    {
                                        "link": result.get("source_link", ""),
                                        "title": result.get("metadata", {}).get(
                                            "file_name", "Document"
                                        ),
                                        "tool": tool_data.get("tool", "unknown"),
                                    }
                                )
                    except:
                        continue

        return list({s["link"]: s for s in sources}.values())
