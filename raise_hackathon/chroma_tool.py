import json
from smolagents import Tool
from raise_hackathon.transcribe_and_store import TranscriptionChromaDB

class ChromaQueryTool(Tool):
    """
    Search for video transcript segments that match a user query using ChromaDB.

    Args:
        query (str): A natural language question or search string.

    Returns:
        str: A structured JSON string containing the most relevant video segments. Each result includes:
            - The transcript text of the matching segment
            - The segment's timestamp range within the video
            - A reference to the corresponding video segment file
            - The segment index
            - The similarity score indicating how closely it matched the query

    This is useful for retrieving precise clips from videos based on natural language questions.
    """

    name = "chroma_query"
    description = "Search video transcripts for relevant segments using ChromaDB."
    inputs = {
        "query": {
            "type": "string",
            "description": "A natural language question or search string."
        }
    }
    output_type = "string"

    def __init__(self, collection_name: str = "video_transcriptions", database_path: str = "./chroma_db"):
        super().__init__()
        self.transcriber = TranscriptionChromaDB(
            collection_name=collection_name,
            database_path=database_path,
        )
        

    def forward(self, query: str) -> str:
        results = self.transcriber.search_segments(query_text=query, n_results=3)
        hits = results.get("results", {})

        documents = hits.get("documents", [[]])[0]
        metadatas = hits.get("metadatas", [[]])[0]
        distances = hits.get("distances", [[]])[0]

        if not documents:
            return json.dumps({"query": query, "results": []}, indent=2)

        segments = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            segment_idx = meta.get("segment_index", 0)
            video_path = meta.get("video_path", "unknown.mp4")
            timestamp_range = meta.get("timestamp_range", "")
            clip_path = f"{video_path[:-4]}_segment_{segment_idx:04d}.mp4"
            text = doc.strip()
            score = dist

            segments.append({
                "segment_index": segment_idx,
                "timestamp_range": timestamp_range,
                "text": text,
                "video_segment_file": clip_path,
                "similarity_score": score
            })

        response = {
            "query": query,
            "results": segments
        }

        return json.dumps(response, indent=2)
