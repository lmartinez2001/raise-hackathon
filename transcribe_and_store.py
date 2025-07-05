#!/usr/bin/env python3
"""
Script to transcribe videos and store segments in ChromaDB for vector search.
Each segment from the transcription is stored as a separate document in the database.
"""

import asyncio
import os
import sys
from pathlib import Path
import chromadb
from typing import List, Dict, Any, Optional

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from whisper_transcription_tool import WhisperTranscriptionTool

class TranscriptionChromaDB:
    def __init__(self, collection_name: str = "video_transcriptions", database_path: str = "./chroma_db"):
        """Initialize the transcription and ChromaDB integration."""
        # Configure ChromaDB to save data to disk
        self.client = chromadb.PersistentClient(path=database_path)
        self.collection_name = collection_name
        self.transcription_tool = WhisperTranscriptionTool()
        
        # Create or get the collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            print(f"Using existing collection: {collection_name}")
            print(f"Data saved to: {database_path}")
        except Exception:
            self.collection = self.client.create_collection(name=collection_name)
            print(f"Created new collection: {collection_name}")
            print(f"Data will be saved to: {database_path}")
    
    async def transcribe_and_store_video(
        self,
        video_path: str,
        model_name: str = "base",
        language: Optional[str] = None,
        video_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Transcribe a video and store each segment in ChromaDB."""
        
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        print(f"Transcribing video: {video_path}")
        
        # Transcribe the video
        result = await self.transcription_tool.transcribe_video(
            video_path=video_path,
            model_name=model_name,
            language=language,
            output_format="json",
            include_timestamps=True,
            video_id=video_id
        )
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        base_metadata = {
            "video_path": video_path,
            "video_id": result.get("video_id", "unknown"),
            "language": result.get("language", "unknown"),
            "model_name": model_name,
            "total_segments": len(result.get("segments", []))
        }
        base_metadata.update(metadata)
        
        # Store each segment in ChromaDB
        segments = result.get("segments", [])
        stored_segments = []
        
        for i, segment in enumerate(segments):
            segment_id = f"{result.get('video_id', 'unknown')}_segment_{i:04d}"
            
            # Prepare segment metadata
            segment_metadata = {
                **base_metadata,
                "segment_index": i,
                "start_time": segment.get("start", 0),
                "end_time": segment.get("end", 0),
                "start_formatted": segment.get("start_formatted", ""),
                "end_formatted": segment.get("end_formatted", ""),
                "timestamp_range": segment.get("timestamp_range", "")
            }
            
            # Store in ChromaDB
            self.collection.add(
                ids=[segment_id],
                documents=[segment.get("text", "").strip()],
                metadatas=[segment_metadata]
            )
            
            stored_segments.append({
                "segment_id": segment_id,
                "text": segment.get("text", "").strip(),
                "timestamp": segment.get("timestamp_range", ""),
                "metadata": segment_metadata
            })
            
            print(f"  Stored segment {i+1}/{len(segments)}: {segment_id}")
        
        print(f"✓ Stored {len(stored_segments)} segments in ChromaDB")
        
        return {
            "video_path": video_path,
            "video_id": result.get("video_id"),
            "total_segments": len(stored_segments),
            "stored_segments": stored_segments,
            "full_transcription": result.get("text", "")
        }
    
    def search_segments(
        self,
        query_text: str,
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Search for segments in ChromaDB."""
        
        query_params = {
            "query_texts": [query_text],
            "n_results": n_results
        }
        
        if where:
            query_params["where"] = where
        
        results = self.collection.query(**query_params)
        
        return {
            "query": query_text,
            "results": results
        }
    
    def get_segments_by_video(self, video_id: str) -> List[Dict[str, Any]]:
        """Get all segments for a specific video."""
        
        results = self.collection.get(
            where={"video_id": video_id}
        )
        
        segments = []
        for i in range(len(results["ids"])):
            segments.append({
                "segment_id": results["ids"][i],
                "text": results["documents"][i],
                "metadata": results["metadatas"][i]
            })
        
        return segments
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        
        # Get all documents to count
        all_results = self.collection.get()
        
        # Count unique videos
        video_ids = set()
        for metadata in all_results["metadatas"]:
            if metadata and "video_id" in metadata:
                video_ids.add(metadata["video_id"])
        
        return {
            "total_segments": len(all_results["ids"]),
            "unique_videos": len(video_ids),
            "video_ids": list(video_ids)
        }

async def main():
    """Main function to demonstrate the transcription and storage."""
    
    # Initialize the transcription and storage system
    transcriber = TranscriptionChromaDB(database_path="output/database/test_video")
    
    # Example video path - replace with your actual video file
    # video_path = "data/video_short_1.mp4"  # Replace with your video file
    video_path = "data/test_video.mp4"  # Replace with your video file
    
    if not os.path.exists(video_path):
        print(f"Video file not found: {video_path}")
        print("Please provide a valid video file path.")
        return
    
    try:
        # Transcribe and store the video
        print("=" * 60)
        print("TRANSCRIBING AND STORING VIDEO")
        print("=" * 60)
        
        result = await transcriber.transcribe_and_store_video(
            video_path=video_path,
            model_name="base",
            language=None,  # Auto-detect
            video_id=None,  # Auto-generate from path
            metadata={
                "source": "test_video",
                "processing_date": "2024-01-15"
            }
        )
        
        print(f"\n✓ Transcription completed!")
        print(f"  Video ID: {result['video_id']}")
        print(f"  Total segments: {result['total_segments']}")
        print(f"  Language: {result.get('language', 'unknown')}")
        
        # Show collection statistics
        print("\n" + "=" * 60)
        print("COLLECTION STATISTICS")
        print("=" * 60)
        
        stats = transcriber.get_collection_stats()
        print(f"Total segments in database: {stats['total_segments']}")
        print(f"Unique videos: {stats['unique_videos']}")
        print(f"Video IDs: {stats['video_ids']}")
        
        # Demonstrate search functionality
        print("\n" + "=" * 60)
        print("SEARCH DEMONSTRATION")
        print("=" * 60)
        
        # Search for segments containing specific words
        search_queries = [
            "hello",
            "test",
            "video"
        ]
        
        for query in search_queries:
            print(f"\nSearching for: '{query}'")
            search_results = transcriber.search_segments(query, n_results=3)
            
            if search_results["results"]["documents"]:
                for i, (doc, metadata) in enumerate(zip(
                    search_results["results"]["documents"][0],
                    search_results["results"]["metadatas"][0]
                )):
                    print(f"  Result {i+1}: {doc[:100]}...")
                    print(f"    Video: {metadata.get('video_id', 'unknown')}")
                    print(f"    Timestamp: {metadata.get('timestamp_range', 'N/A')}")
            else:
                print("  No results found")
        
        # Get segments for the specific video
        print(f"\n" + "=" * 60)
        print(f"SEGMENTS FOR VIDEO: {result['video_id']}")
        print("=" * 60)
        
        video_segments = transcriber.get_segments_by_video(result['video_id'])
        print(f"Found {len(video_segments)} segments for this video:")
        
        for i, segment in enumerate(video_segments[:5]):  # Show first 5
            print(f"  Segment {i+1}: {segment['text'][:100]}...")
            print(f"    Timestamp: {segment['metadata'].get('timestamp_range', 'N/A')}")
        
        if len(video_segments) > 5:
            print(f"  ... and {len(video_segments) - 5} more segments")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 