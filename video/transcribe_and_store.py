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
    def __init__(self, database_path: str, collection_name: str, query_mode: bool = True, chunk_size: int = 1):
        """Initialize the transcription and ChromaDB integration."""

        super().__init__(database_path=database_path, collection_name=collection_name, query_mode=query_mode) 

        self.transcription_tool = WhisperTranscriptionTool()
        self.chunk_size = chunk_size
    
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
        
        # Store segments in chunks, respecting sentence boundaries
        segments = result.get("segments", [])
        stored_segments = []
        
        # Process segments in chunks, ensuring each chunk ends with a sentence
        i = 0
        segment_idx = 0
        while i < len(segments):
            # Start with chunk_size segments
            chunk_size = self.chunk_size
            chunk_segments = segments[i:i+chunk_size]
            
            # Combine text to check sentence ending
            combined_text = " ".join([seg.get("text", "").strip() for seg in chunk_segments])
            sentence_endings = ['.', '!', '?', ':', ';']
            ends_with_sentence = any(combined_text.rstrip().endswith(ending) for ending in sentence_endings)
            
            # If we don't have a sentence ending and there are more segments, try to include more
            if not ends_with_sentence and i + chunk_size < len(segments):
                # Try to find a sentence ending by including more segments
                for extra_segments in range(1, self.chunk_size):  # Try more segments
                    if i + chunk_size + extra_segments <= len(segments):
                        extended_chunk = segments[i : i + chunk_size + extra_segments]
                        extended_text = " ".join([seg.get("text", "").strip() for seg in extended_chunk])
                        if any(extended_text.rstrip().endswith(ending) for ending in sentence_endings):
                            chunk_segments = extended_chunk
                            chunk_size += extra_segments
                            break
            
            segment_id = f"{result.get('video_id', 'unknown')}_segment_{segment_idx:06d}"
            
            segment_storage_result = await self.store_segment_chunk_in_database(
                segments=chunk_segments,
                segment_id=segment_id,
                segment_idx=segment_idx,
                base_metadata=base_metadata
            )
            
            stored_segments.append(segment_storage_result)
            print(f"  Stored segment {segment_idx+1}: {segment_id} ({len(chunk_segments)} segments)")
            
            # Move to next chunk
            i += len(chunk_segments)
            segment_idx += 1
        
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

    async def store_segment_chunk_in_database(
        self,
        segments: List[Dict[str, Any]],
        segment_id: str,
        segment_idx: int,
        base_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Store a chunk of segments in the database."""
        
        if not segments:
            return {"segment_id": segment_id, "text": "", "metadata": {}}
        
        # Combine text from all segments in the chunk
        combined_text = " ".join([segment.get("text", "").strip() for segment in segments])
        
        # Check if the combined text ends with a proper sentence ending
        sentence_endings = ['.', '!', '?', ':', ';']
        ends_with_sentence = any(combined_text.rstrip().endswith(ending) for ending in sentence_endings)
        
        # If it doesn't end with a sentence ending, try to include the next segment
        # This will be handled by the calling function by adjusting chunk boundaries
        if not ends_with_sentence and combined_text.strip():
            # Add a period if the text doesn't end with any sentence ending
            combined_text = combined_text.rstrip() + "."
        
        # Get timing information from first and last segment
        first_segment = segments[0]
        last_segment = segments[-1]
        
        start_time = first_segment.get("start", 0)
        end_time = last_segment.get("end", 0)
        
        # Format timestamps
        start_formatted = first_segment.get("start_formatted", "")
        end_formatted = last_segment.get("end_formatted", "")
        timestamp_range = f"[{start_formatted} - {end_formatted}]"
        
        # Prepare segment metadata
        segment_metadata = {
            **base_metadata,
            "segment_idx": segment_idx,
            "start_time": start_time,
            "end_time": end_time,
            "start_formatted": start_formatted,
            "end_formatted": end_formatted,
            "timestamp_range": timestamp_range,
            "data_type": "segment",
        }
        
        # Store in ChromaDB
        self.collection.add(
            ids=[segment_id],
            documents=[combined_text],
            metadatas=[segment_metadata]
        )
        
        return {
            "segment_id": segment_id,
            "text": combined_text,
            "timestamp": timestamp_range,
            "metadata": segment_metadata
        }

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
            "segment_idx": segment_idx,
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
        python transcribe_and_store.py --video data/video.mp4 --collection_name my_collection --database_path output/my_db
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
        "--collection_name", "-c",
        type=str,
        required=True,
        help="ChromaDB collection name"
    )
    
    parser.add_argument(
        "--database_path", "-d",
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

    parser.add_argument(
        "--chunk_size",
        type=int,
        default=1,
        help="Number of segments to store in each chunk (default: 2)"
    )

    return parser.parse_args()

async def main():
    """Main function to demonstrate the transcription and storage."""
    
    # Parse command line arguments.
    args = parse_arguments()
    collection_name = args.collection_name
    video_path = args.video
    database_path = args.database_path
    
    assert os.path.exists(video_path), f"Video file not found: {video_path}"
    
    # Initialize the transcription and storage system.
    transcriber = TranscriptionChromaDB(collection_name=collection_name, database_path=database_path, query_mode=False, chunk_size=args.chunk_size)        
    
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
                print(f"  Result {i+1}: {doc}")
                print(f"    Video: {metadata.get('video_id', 'unknown')}")
                print(f"    Timestamp: {metadata.get('timestamp_range', 'N/A')}")
        else:
            print("  No results found")
    
    print(f"\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(main()) 