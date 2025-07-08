import argparse
from typing import Optional, Dict, Any, List, Tuple
from smolagents import CodeAgent, InferenceClientModel, Tool

from database import ChromaDB
from video.transcribe_and_store import TranscriptionChromaDB

class ChromaQueryDatabaseTool(Tool):
    """
    Query ChromaDB for transcript segments matching a natural language query.

    This tool performs a semantic search over a video transcription database,
    returning metadata-rich results like timestamps, segment IDs, and file info.

    Args:
        query_text (str): Natural language search query.

    Returns:
        Dict[str, List]: A dictionary with:
            - texts: List of transcript texts
            - ids: List of video IDs
            - segment_idx: List of segment indices
            - segment_ids: List of segment unique IDs
            - timestamp_start: List of segment start times
            - timestamp_end: List of segment end times
            - file_creation_date: List of file creation dates
            - data_type: List of data types
    """

    name = "video_transcription_query_database"
    description = "Search ChromaDB for transcript segments using natural language queries and optional metadata filters."
    inputs = {
        "query_text": {
            "type": "string",
            "description": "Natural language text to search for."
        },
    }
    output_type = "object"

    def __init__(self, collection_name: str, database_path: str):
        super().__init__()
        self.collection_name = collection_name
        self.database_path = database_path
        self.transcriber_database = TranscriptionChromaDB(
            database_path=self.database_path,
            collection_name=self.collection_name,
        )

    def forward(
        self,
        query_text: str,
    ) -> Dict[str, List]:
        # Initialize the database.

        # Query the database.
        search_results = self.transcriber_database.search_segments(
            query_text, n_results=3, where=None
        )

        # Extract the results.
        documents = search_results["results"]
        segment_ids = documents["ids"][0]
        segment_texts = documents["documents"][0]
        metadatas = documents["metadatas"][0]
        video_ids = [metadata["video_id"] for metadata in metadatas]
        timestamp_start = [metadata["start_time"] for metadata in metadatas]
        timestamp_end = [metadata["end_time"] for metadata in metadatas]
        file_creation_date = [metadata["file_creation_date"] for metadata in metadatas]
        segment_idx = [metadata["segment_index"] for metadata in metadatas]

        return {
            "texts": segment_texts,
            "ids": video_ids,
            "segment_idx": segment_idx,
            "segment_ids": segment_ids,
            "timestamp_start": timestamp_start,
            "timestamp_end": timestamp_end,
            "file_creation_date": file_creation_date,
            "data_type": ["segment"] * len(segment_texts),
        }


def get_context_segments(
    database_path: str,
    collection_name: str,
    segment_id: str,
    context_window: int = 1
) -> Dict[str, List[str]]:
    """Get surrounding context segments for a given segment ID.
    
    Args:
        database_path: Path to the database
        collection_name: Name of the collection
        segment_id: ID of the segment to get context for
        context_window: Number of segments before and after to retrieve (default: 1)
        
    Returns:
        Dictionary containing previous and next segments
    """
    transcriber = ChromaDB(database_path=database_path, collection_name=collection_name, query_mode=True)
    
    # Get the segments before and after
    prev_segments = transcriber.get_previous_segments(segment_id, n_segments=context_window)
    next_segments = transcriber.get_next_segments(segment_id, n_segments=context_window)
    
    return {
        "previous_segments": prev_segments,
        "next_segments": next_segments
    }


def get_segment_by_id(
    database_path: str,
    collection_name: str,
    segment_id: str
) -> Dict[str, Any]:
    """Get a specific segment by its ID.
    
    Args:
        database_path: Path to the database
        collection_name: Name of the collection
        segment_id: ID of the segment to retrieve
        
    Returns:
        Dictionary containing the segment data
    """
    transcriber = ChromaDB(collection_name=collection_name, database_path=database_path, query_mode=True)
    return transcriber.get_segment_by_id(segment_id)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="SmolAgent for querying video transcription database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        python smolagent_transcriber.py --database output/meetings_db --collection meetings --query "What was discussed about AI?"
        python smolagent_transcriber.py --database output/meetings_db --collection meetings --query "Find information about testing" --max-steps 10
        """
    )
    
    parser.add_argument(
        "--database_path", "-d",
        type=str,
        required=True,
        help="Path to ChromaDB database directory"
    )
    
    parser.add_argument(
        "--collection_name", "-c",
        type=str,
        required=True,
        help="ChromaDB collection name"
    )
    
    parser.add_argument(
        "--query", "-q",
        type=str,
        required=True,
        help="Query to ask the agent"
    )
    
    parser.add_argument(
        "--max-steps", "-s",
        type=int,
        default=5,
        help="Maximum number of agent steps (default: 5)"
    )

    parser.add_argument(
        "--model-id", "-m",
        type=str,
        default="meta-llama/Llama-3.3-70B-Instruct",
        help="Model ID"
    )

    return parser.parse_args()


if __name__ == "__main__":
    import os

    # Parse command line arguments
    args = parse_arguments()
    
    # Extract arguments
    database_path = args.database_path
    collection_name = args.collection_name
    query = args.query
    max_steps = args.max_steps

    # Initialize model and agent
    model = InferenceClientModel(model_id=args.model_id)
    agent = CodeAgent(
        model=model,
        name="video_agent", 
        description="An agent to query the database for video transcription results.",
        tools=[query_database],
        max_steps=max_steps,
    )

    # Run the agent and capture the result
    agent_query = f"First query the collection '{collection_name}' in the database at '{database_path}' to find '{query}'.\
        In your answer, include the segment you used to answer the question, its original video id, its transcription, and its timestamps."
    result = agent.run(agent_query)

    # Print the final result
    print("\n" + "="*60)
    print("AGENT RESULT:")
    print("="*60) 
    print(f"Result: {result}")
