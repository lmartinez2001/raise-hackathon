from typing import Optional, Dict, Any, List, Tuple
from smolagents import CodeAgent, InferenceClientModel, tool

from transcribe_and_store import TranscriptionChromaDB

@tool
def query_database(
    database_path: str,
    collection_name: str,
    query_text: str,
    where: Optional[Dict[str, Any]] = None,
    n_results: int = 3,
) -> Tuple[List[str], List[str], List[int], List[str], List[float], List[float], List[str]]:
    """Query the database for segments matching the query text.
    
    Args:
        database_path: Path to the database
        collection_name: Name of the collection to query
        query_text: Text to search for
        where: Optional dictionary of metadata to filter by
        n_results: Number of results to return (default: 1)
        
    Returns:
        segment_texts: List of texts of the segments
        video_ids: List of ids of the video associated to the segments
        segment_idx: List of segment indices
        segment_ids: List of segment ids
        start_times: List of start times of the segments
        end_times: List of end times of the segments
        file_creation_date: List of file creation dates of the segments
    """

    transcriber = TranscriptionChromaDB(collection_name=collection_name, database_path=database_path)
    search_results = transcriber.search_segments(query_text, n_results=n_results, where=where)
    
    # Extract just the text content from the results
    documents = search_results["results"]
    segment_ids = documents["ids"][0]
    segment_texts = documents["documents"][0]
    metadatas = documents["metadatas"][0]
    video_ids = [metadata["video_id"] for metadata in metadatas]
    start_times = [metadata["start_time"] for metadata in metadatas]
    end_times = [metadata["end_time"] for metadata in metadatas]
    file_creation_date = [metadata["file_creation_date"] for metadata in metadatas]
    segment_idx = [metadata["segment_index"] for metadata in metadatas]


    return (
        segment_texts,
        video_ids,
        segment_idx,
        segment_ids,
        start_times,
        end_times,
        file_creation_date,
    )


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
    transcriber = TranscriptionChromaDB(collection_name=collection_name, database_path=database_path)
    
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
    transcriber = TranscriptionChromaDB(collection_name=collection_name, database_path=database_path)
    return transcriber.get_segment_by_id(segment_id)




if __name__ == "__main__":

    model = InferenceClientModel()
    agent = CodeAgent(
        model=model,
        name="video_agent",
        description="An agent to query the database for video transcription results.",
        tools=[query_database],
        max_steps=5,
    )

    # Run the agent and capture the result
    result = agent.run("Can you query the collection 'video_transcriptions' in the database at output/database/test_db to find if I have to convert my ongoing work?\
        Answer the question and summarise all the main informations about the database entry you used to answer the question.")# If returned, the database transcriptions are located in the 'documents' field of the result.")

    # Print the final result
    print("\n" + "="*60)
    print("AGENT RESULT:")
    print("="*60)
    print(f"Result: {result}")

