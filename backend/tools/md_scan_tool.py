import os
import json
from pathlib import Path
from smolagents import Tool
from typing import Dict, List, Any


class MarkdownScanTool(Tool):
    name = "markdown_scan"
    description = (
        "Recursively scan markdown files in a directory for relevant content. "
        "Args:\n"
        "  query (str): search terms to match in markdown files.\n"
        "  max_results (int): maximum number of matching sections to return.\n"
        "Returns:\n"
        "  JSON string with matched sections, including file metadata."
    )
    inputs: Dict[str, Dict[str, Any]] = {
        "query": {
            "type": "string",
            "description": "Terms to search for in markdown content.",
        },
        "max_results": {
            "type": "integer",
            "description": "Maximum number of sections to return.",
        },
    }
    output_type = "object"

    def __init__(self, wiki_directory: str = "./wiki"):
        super().__init__()
        self.wiki_dir = Path(wiki_directory)

    def setup(self):
        # No heavy resources to initialize, but defined for future-proofing
        print(f"[markdown_scan] Initialized scanning directory: {self.wiki_dir}")

    def forward(self, query: str, max_results: int) -> str:
        print(f"[markdown_scan] Searching for '{query}' with limit {max_results}")
        results = []
        query_lower = query.lower()

        for md_file in self.wiki_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
            except Exception as e:
                print(f"[markdown_scan] Skipping {md_file}: {e}")
                continue

            if any(term in content.lower() for term in query_lower.split()):
                sections = self._extract_sections(content, query_lower)
                for section in sections[:max_results]:
                    results.append(
                        {
                            "content": section,
                            "metadata": {
                                "file_path": str(md_file.resolve()),
                                "file_name": md_file.name,
                            },
                            "source_link": f"file://{md_file.resolve()}",
                        }
                    )
                    if len(results) >= max_results:
                        break
            if len(results) >= max_results:
                break

        output = {
            "tool": self.name,
            "query": query,
            "results": results,
            "count": len(results),
        }
        return output

    def _extract_sections(self, content: str, query_lower: str) -> List[str]:
        lines = content.split("\n")
        sections, current = [], []

        def flush():
            text = "\n".join(current)
            if any(q in text.lower() for q in query_lower.split()):
                sections.append(text)

        for line in lines:
            if line.startswith("#"):
                if current:
                    flush()
                current = [line]
            else:
                current.append(line)
        if current:
            flush()

        return sections or [content[:500]]  # fallback snippet


# TEST
if __name__ == "__main__":
    md_tool = MarkdownScanTool("backend/docs")
    query = input("Enter your query: ")
    max_results = input("Max results: ")
    response = md_tool.forward(query, int(max_results))
    print(type(response))
