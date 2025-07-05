#!/usr/bin/env python3
"""
Script to transcribe videos and store segments in ChromaDB for vector search.
Each segment from the transcription is stored as a separate document in the database.
"""

import asyncio
import os
import sys
import base64
import logging
from pathlib import Path
import chromadb
import datetime
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            segment_id = f"{result.get('video_id', 'unknown')}_segment_{i:04d}"

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
    
    def retrieve_video_from_database(self, video_id: str, output_path: str) -> str:
        """Retrieve video file from database and save to disk."""
        
        video_document_id = f"{video_id}_video_file"
        
        try:
            # Get the video document from database
            results = self.collection.get(ids=[video_document_id])
            
            if not results["documents"]:
                raise ValueError(f"Video not found in database: {video_id}")
            
            encoded_video = results["documents"][0]
            metadata = results["metadatas"][0]
            
            # Decode and save video
            decoded_path = self.decode_video_from_base64(encoded_video, output_path)
            
            logger.info(f"✓ Retrieved video from database: {decoded_path}")
            logger.info(f"  Original file: {metadata.get('video_path', 'unknown')}")
            logger.info(f"  File size: {metadata.get('file_size_bytes', 0)} bytes")
            
            return decoded_path
            
        except Exception as e:
            logger.error(f"Error retrieving video from database: {e}")
            raise
    
    def get_video_info_from_database(self, video_id: str) -> Dict[str, Any]:
        """Get information about a stored video without retrieving the full file."""
        
        video_document_id = f"{video_id}_video_file"
        
        try:
            results = self.collection.get(ids=[video_document_id])
            
            if not results["metadatas"]:
                return {"error": f"Video not found in database: {video_id}"}
            
            metadata = results["metadatas"][0]
            
            return {
                "video_id": video_id,
                "original_path": metadata.get("video_path", "unknown"),
                "file_size_bytes": metadata.get("file_size_bytes", 0),
                "file_extension": metadata.get("file_extension", "unknown"),
                "stored_timestamp": metadata.get("stored_timestamp", "unknown"),
                "document_id": video_document_id
            }
            
        except Exception as e:
            logger.error(f"Error getting video info from database: {e}")
            return {"error": str(e)}
    
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
        
        # Use where filter to get only segments, not video files
        base_where = {"data_type": "segment"}
        if where:
            # Combine with existing where conditions
            query_params["where"] = {
                "$and": [base_where, where]
            }
        else:
            query_params["where"] = base_where

        print(query_params)
        
        results = self.collection.query(**query_params)
        
        return {
            "query": query_text,
            "results": results
        }
    
    def get_segments_by_video(self, video_id: str) -> List[Dict[str, Any]]:
        """Get all segments for a specific video."""
        
        query_params = {
            "where": {
                "$and": [
                    {"video_id": video_id},
                    {"data_type": "segment"}
                ]
            }
        }
        results = self.collection.get(**query_params)
        
        segments = []
        for i in range(len(results["ids"])):
            segments.append({
                "segment_id": results["ids"][i],
                "text": results["documents"][i],
                "metadata": results["metadatas"][i]
            })
        
        return segments
    
    def get_video_by_id(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get video metadata and encoded content for a specific video ID."""
        
        video_document_id = f"{video_id}_video_file"
        
        query_params = {
            "ids": [video_document_id],
            "where": {"data_type": "video"}
        }
        
        results = self.collection.get(**query_params)
        
        if not results["documents"]:
            return None
            
        return {
            "video_id": video_id,
            "document_id": results["ids"][0],
            "encoded_content": results["documents"][0],
            "metadata": results["metadatas"][0]
        }
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""

        # Get all documents and separate by type
        all_results = self.collection.get(
            where={
                "$or": [
                    {"data_type": "video"},
                    {"data_type": "segment"}
                ]
            }
        )
        
        # Count videos and segments separately
        video_count = 0
        segment_count = 0
        video_ids = set()
        
        for metadata in all_results["metadatas"]:
            if metadata:
                if metadata.get("data_type") == "video":
                    video_count += 1
                elif metadata.get("data_type") == "segment":
                    segment_count += 1
                if "video_id" in metadata:
                    video_ids.add(metadata["video_id"])
        
        return {
            "total_segments": segment_count,
            "total_videos": video_count,
            "unique_videos": len(video_ids),
            "video_ids": list(video_ids),
            "total_documents": len(all_results["ids"])
        }

async def main():
    """Main function to demonstrate the transcription and storage."""
    
    collection_name = "video_transcriptions" # TODO - add collection name
    video_path = "data/video_short_2.mp4" # TODO - add path to video
    database_path = "output/database/test_db" # TODO - add path to database
    
    if not os.path.exists(video_path):
        print(f"Video file not found: {video_path}")
        print("Please provide a valid video file path.")
        return
    
    # Initialize the transcription and storage system
    transcriber = TranscriptionChromaDB(collection_name=collection_name, database_path=database_path)
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
        
        # Demonstrate video retrieval functionality
        print(f"\n" + "=" * 60)
        print("VIDEO RETRIEVAL DEMONSTRATION")
        print("=" * 60)
        
        video_id = result['video_id']
        
        # Get video information from database
        print(f"\nGetting video information for: {video_id}")
        video_info = transcriber.get_video_info_from_database(video_id)
        
        if "error" not in video_info:
            print(f"✓ Video information retrieved:")
            print(f"  Original path: {video_info['original_path']}")
            print(f"  File size: {video_info['file_size_bytes']} bytes")
            print(f"  File extension: {video_info['file_extension']}")
            print(f"  Stored timestamp: {video_info['stored_timestamp']}")
            
            # Retrieve video from database
            print(f"\nRetrieving video from database...")
            output_path = f"outputs/retrieved_{video_id.replace('/', '_')}.mp4"
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            try:
                retrieved_path = transcriber.retrieve_video_from_database(
                    video_id=video_id,
                    output_path=output_path
                )
                
                print(f"✓ Video retrieved successfully!")
                print(f"  Retrieved path: {retrieved_path}")
                
                # Verify the retrieved file
                if os.path.exists(retrieved_path):
                    original_size = os.path.getsize(video_path)
                    retrieved_size = os.path.getsize(retrieved_path)
                    print(f"  Original file size: {original_size} bytes")
                    print(f"  Retrieved file size: {retrieved_size} bytes")
                    print(f"  Files match: {original_size == retrieved_size}")
                    
                    if original_size == retrieved_size:
                        print(f"  ✓ Video retrieval successful - files are identical!")
                    else:
                        print(f"  ⚠ Warning: File sizes don't match")
                        
            except Exception as e:
                print(f"✗ Error retrieving video: {e}")
        else:
            print(f"✗ Error getting video info: {video_info['error']}")
        
        # Demonstrate search with video retrieval
        print(f"\n" + "=" * 60)
        print("SEARCH WITH VIDEO RETRIEVAL DEMONSTRATION")
        print("=" * 60)
        
        search_queries = ["hello", "test", "video"]
        
        for query in search_queries:
            print(f"\nSearching for: '{query}'")
            search_results = transcriber.search_segments(query, n_results=2)
            
            if search_results["results"]["documents"]:
                for i, (doc, metadata) in enumerate(zip(
                    search_results["results"]["documents"][0],
                    search_results["results"]["metadatas"][0]
                )):
                    print(f"  Result {i+1}: {doc[:80]}...")
                    print(f"    Video ID: {metadata.get('video_id', 'unknown')}")
                    print(f"    Timestamp: {metadata.get('timestamp_range', 'N/A')}")
                    
                    # Show video info for this result
                    result_video_id = metadata.get('video_id', 'unknown')
                    if result_video_id != 'unknown':
                        result_video_info = transcriber.get_video_info_from_database(result_video_id)
                        if "error" not in result_video_info:
                            print(f"    Video file: {result_video_info['original_path']}")
                            print(f"    Video size: {result_video_info['file_size_bytes']} bytes")
                            print(f"    Can retrieve: Yes")
                        else:
                            print(f"    Video info: Not available")
            else:
                print("  No results found")
        
        print(f"\n" + "=" * 60)
        print("COMPLETE WORKFLOW SUMMARY")
        print("=" * 60)
        print("✓ Video file stored in database")
        print("✓ Video transcribed and segments stored")
        print("✓ Video can be retrieved from database")
        print("✓ Search results link to original videos")
        print("✓ Complete video-transcription workflow demonstrated")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 