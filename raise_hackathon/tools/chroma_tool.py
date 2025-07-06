import json
from smolagents import Tool
from raise_hackathon.transcribe_and_store import TranscriptionChromaDB

class ChromaQueryTool(Tool):
    """
    Search video transcript segments with a natural language query using ChromaDB.

    This tool returns the top matching transcript segments, including the text,
    timestamp, video segment file, segment index, and similarity score. It is
    designed to help the assistant locate exact clips in pre-processed meeting videos.

    Args:
        query (str): A natural language query string (e.g. "budget discussion", "project decision").

    Returns:
        str: A JSON-formatted string with the query key and a list of up to 3 result segments.
             Each result contains:
             - segment_index (int): The index of the segment in the video.
             - timestamp_range (str): Human-readable time span, e.g. "[03:26 - 03:29]".
             - text (str): Transcript snippet for the matched segment.
             - video_segment_file (str): Path to the saved video clip file.
             - similarity_score (float): Numeric score indicating match relevance.

    Raises:
        ValueError: If ChromaDB returns incomplete results or unexpected formats.

    Example:
        >>> tool = ChromaQueryTool()
        >>> result = tool.forward("What was decided about the deadline?")
        >>> print(result)
        {
          "query": "What was decided about the deadline?",
          "results": [
            {
              "segment_index": 45,
              "timestamp_range": "[05:12 - 05:15]",
              "text": "We agreed to extend the deadline to next Monday.",
              "video_segment_file": "meeting1_segment_0045.mp4",
              "similarity_score": 0.82
            }
          ]
        }
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
