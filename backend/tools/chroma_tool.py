import chromadb
from smolagents import Tool
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction


class ChromaDBTool(Tool):
    name = "chromadb_search"
    description = (
        "Search for relevant documents in a ChromaDB vector database.\n"
        "Inputs:\n"
        "  query (string): the search query.\n"
        "  n_results (integer): number of top documents to return (>=1).\n"
        "Output:\n"
        "  JSON string with 'tool', 'query', 'count', and 'results':\n"
        "    results: list of {content, metadata, source_link}"
    )
    inputs = {
        "query": {"type": "string", "description": "Search query string."},
        "n_results": {
            "type": "integer",
            "description": "Number of results to return, must be >= 1.",
        },
    }
    output_type = "string"

    def __init__(
        self, collection_name: str = "documents", persist_path: str = "./chroma_db"
    ):
        super().__init__()
        self._client = None
        self._collection = None
        self.collection_name = collection_name
        self.persist_path = persist_path

    def _init(self):
        if self._client is None:
            self._client = chromadb.PersistentClient(path=self.persist_path)
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2"
                ),
            )

    def forward(self, query: str, n_results: int) -> str:
        print(f"[{self.name}] Called with query={query!r}, n_results={n_results}")
        if not query:
            raise ValueError("`query` must be a non-empty string.")
        if not isinstance(n_results, int) or n_results < 1:
            raise ValueError("`n_results` must be an integer >= 1.")

        self._init()
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents", "metadatas"],
            )
        except Exception as e:
            err = f"[{self.name}] ChromaDB query failed: {e}"
            print(err)
            raise RuntimeError(err)

        docs = results["documents"][0]
        metas = results["metadatas"][0]
        formatted = []
        for doc, meta in zip(docs, metas):
            formatted.append(
                {
                    "content": doc,
                    "metadata": meta,
                    "source_link": meta.get("source_url", "No link available"),
                }
            )

        output = {
            "tool": self.name,
            "query": query,
            "count": len(formatted),
            "results": formatted,
        }
        return output
