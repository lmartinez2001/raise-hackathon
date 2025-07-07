#!/usr/bin/env python3
"""
Script to transcribe videos and store segments in ChromaDB for vector search.
Each segment from the transcription is stored as a separate document in the database.
"""

import argparse
import asyncio
import os
import sys
import base64
import logging
from pathlib import Path
import datetime
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fix path for database module
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), ""))

from database import ChromaDB
from video.whisper_transcription_tool import WhisperTranscriptionTool


class TranscriptionChromaDB(ChromaDB):
    def __init__(self, database_path: str, collection_name: str):
        """Initialize the transcription and ChromaDB integration."""

        super().__init__(database_path=database_path, collection_name=collection_name) 

        self.transcription_tool = WhisperTranscriptionTool()
    
    async def transcribe_and_store_video(
        self,
        video_path: str,
        model_name: str = "base",
        language: Optional[str] = None,
        video_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        store_video: bool = False
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
            "total_segments": len(result.get("segments", [])),
            "source": video_path,
            "processing_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "file_creation_date": datetime.datetime.fromtimestamp(os.path.getmtime(video_path)).strftime("%Y-%m-%d %H:%M:%S")
        }
        base_metadata.update(metadata)
        
        # Store video file in database if requested
        video_storage_result = None
        if store_video:
            try:
                logger.info("Storing video file in database...")
                video_storage_result = await self.store_video_in_database(
                    video_path=video_path,
                    video_id=result.get("video_id"),
                    metadata=metadata
                )
                print(f"✓ Video file stored in database: {video_storage_result['document_id']}")
            except Exception as e:
                logger.error(f"Error storing video file: {e}")
                print(f"⚠ Warning: Could not store video file: {e}")
        
        # Store each segment in ChromaDB
        segments = result.get("segments", [])
        stored_segments = []
        
        for i, segment in enumerate(segments):
            segment_id = f"{result.get('video_id', 'unknown')}_segment_{i:06d}"

            segment_storage_result = await self.store_segment_in_database(
                segment=segment,
                segment_id=segment_id,
                segment_idx=i,
                base_metadata=base_metadata
            )
            
            stored_segments.append(segment_storage_result)
            print(f"  Stored segment {i+1}/{len(segments)}: {segment_id}")
        
        print(f"✓ Stored {len(stored_segments)} segments in ChromaDB")
        
        return {
            "video_path": video_path,
            "video_id": result.get("video_id"),
            "total_segments": len(stored_segments),
            "stored_segments": stored_segments,
            "full_transcription": result.get("text", ""),
            "video_stored": video_storage_result is not None,
            "video_storage_info": video_storage_result
        }
    
    def encode_video_to_base64(self, video_path: str) -> str:
        """Encode video file to base64 string."""
        try:
            with open(video_path, 'rb') as video_file:
                video_data = video_file.read()
                encoded_video = base64.b64encode(video_data).decode('utf-8')
                return encoded_video
        except Exception as e:
            logger.error(f"Error encoding video to base64: {e}")
            raise
    
    def decode_video_from_base64(self, encoded_video: str, output_path: str) -> str:
        """Decode base64 string back to video file."""
        try:
            video_data = base64.b64decode(encoded_video.encode('utf-8'))
            with open(output_path, 'wb') as video_file:
                video_file.write(video_data)
            return output_path
        except Exception as e:
            logger.error(f"Error decoding video from base64: {e}")
            raise

    async def store_segment_in_database(
        self,
        segment: Dict[str, Any],
        segment_id: str,
        segment_idx: int,
        base_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Store a segment in the database."""
        
        # Prepare segment metadata
        segment_metadata = {
            **base_metadata,
            "segment_index": segment_idx,
            "start_time": segment.get("start", 0),
            "end_time": segment.get("end", 0),
            "start_formatted": segment.get("start_formatted", ""),
            "end_formatted": segment.get("end_formatted", ""),
            "timestamp_range": segment.get("timestamp_range", ""),
            "data_type": "segment",
        }
        
        # Store in ChromaDB.
        self.collection.add(
            ids=[segment_id],
            documents=[segment.get("text", "").strip()],
            metadatas=[segment_metadata]
        )
        return {
            "segment_id": segment_idx,
            "text": segment.get("text", "").strip(),
            "timestamp": segment.get("timestamp_range", ""),
            "metadata": segment_metadata
        }
    
    async def store_video_in_database(
        self,
        video_path: str,
        video_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store the actual video file in the database."""
        
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Generate video ID if not provided
        if video_id is None:
            video_id = self._generate_video_id(video_path)
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        video_metadata = {
            "video_path": video_path,
            "video_id": video_id,
            "file_size_bytes": os.path.getsize(video_path),
            "file_extension": Path(video_path).suffix,
            "stored_timestamp": str(asyncio.get_event_loop().time()),
            "data_type": "video",
            **metadata
        }
        
        # Encode video to base64
        logger.info(f"Encoding video to base64: {video_path}")
        encoded_video = self.encode_video_to_base64(video_path)
        
        # Store in ChromaDB
        video_document_id = f"{video_id}_video_file"
        
        self.collection.add(
            ids=[video_document_id],
            documents=[encoded_video],  # Store base64 encoded video
            metadatas=[video_metadata]
        )
        
        logger.info(f"✓ Stored video file in database: {video_document_id}")
        
        return {
            "video_id": video_id,
            "document_id": video_document_id,
            "file_size_bytes": video_metadata["file_size_bytes"],
            "encoded_size_bytes": len(encoded_video.encode('utf-8'))
        }
    
    def _generate_video_id(self, video_path: str) -> str:
        """Generate a video ID from the video path."""
        try:
            path_obj = Path(video_path)
            if path_obj.is_absolute():
                try:
                    relative_path = path_obj.relative_to(Path.cwd())
                    return str(relative_path)
                except ValueError:
                    return path_obj.name
            else:
                return str(path_obj)
        except Exception:
            return Path(video_path).name

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Transcribe videos and store segments in ChromaDB for vector search.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        python transcribe_and_store.py --video data/video.mp4
        python transcribe_and_store.py --video data/video.mp4 --collection my_collection --database output/my_db
        python transcribe_and_store.py --video data/video.mp4 --model large --store-video
        """
    )
    
    parser.add_argument(
        "--video", "-v",
        type=str,
        required=True,
        help="Path to the video file to transcribe"
    )
    
    parser.add_argument(
        "--collection", "-c",
        type=str,
        required=True,
        help="ChromaDB collection name"
    )
    
    parser.add_argument(
        "--database", "-d",
        type=str,
        required=True,
        help="Path to ChromaDB database directory"
    )

    
    parser.add_argument(
        "--language", "-l",
        type=str,
        default=None,
        help="Language code for transcription (default: auto-detect)"
    )
    
    parser.add_argument(
        "--video-id", "-i",
        type=str,
        default=None,
        help="Custom video ID (default: auto-generate from path)"
    )
    
    parser.add_argument(
        "--store-video",
        action="store_true",
        help="Store the video file in the database (default: False)"
    )

    return parser.parse_args()

async def main():
    """Main function to demonstrate the transcription and storage."""
    
    # Parse command line arguments.
    args = parse_arguments()
    collection_name = args.collection
    video_path = args.video
    database_path = args.database
    
    assert os.path.exists(video_path), f"Video file not found: {video_path}"
    
    # Initialize the transcription and storage system.
    transcriber = TranscriptionChromaDB(collection_name=collection_name, database_path=database_path)        
    
    # Transcribe and store the video.
    print("=" * 60)
    print("TRANSCRIBING AND STORING VIDEO")
    print("=" * 60)
    
    result = await transcriber.transcribe_and_store_video(
        video_path=video_path,
        model_name="base",
        language=args.language,  # Auto-detect if None
        video_id=args.video_id,  # Auto-generate from path if None
        metadata=None,
        store_video=False  # Store the video file in database
    )
    
    print(f"\n✓ Transcription completed!")
    print(f"  Video ID: {result['video_id']}")
    print(f"  Total segments: {result['total_segments']}")
    print(f"  Language: {result.get('language', 'unknown')}")
    print(f"  Video stored: {result.get('video_stored', False)}")
    
    if result.get('video_stored'):
        video_info = result.get('video_storage_info', {})
        print(f"  Video document ID: {video_info.get('document_id', 'N/A')}")
        print(f"  Video file size: {video_info.get('file_size_bytes', 0)} bytes")
    
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
    
    print(f"\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(main()) 