#!/usr/bin/env python3
"""
Script to transcribe videos and store segments in ChromaDB for vector search.
Each segment from the transcription is stored as a separate document in the database.
"""

import os
import sys
import logging
import chromadb
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class ChromaDB:
    def __init__(self, database_path: str, collection_name: str, query_mode: bool = True):
        """Initialize the transcription and ChromaDB integration."""

        # Configure ChromaDB to save data to disk
        assert os.path.exists(database_path) or not query_mode, f"Database path does not exist: {database_path}"
        self.client = chromadb.PersistentClient(path=database_path)
        self.collection_name = collection_name
        print(f"Loading dataset from: {collection_name}")

        if query_mode:
            assert collection_name in [col.name for col in self.client.list_collections()], f"Collection '{collection_name}' does not exist in database"
            self.collection = self.client.get_collection(name=collection_name)
            print(f"Using existing collection: {collection_name}")
        else:
            if collection_name in [col.name for col in self.client.list_collections()]:
                self.collection = self.client.get_collection(name=collection_name)
                print(f"Using existing collection: {collection_name}")
            else:
                self.collection = self.client.create_collection(name=collection_name)
                print(f"Created new collection: {collection_name}")
    
    def retrieve_video_from_database(self, video_id: str, output_path: str) -> str:
        """Retrieve video file from database and save to disk."""
        
        video_document_id = f"{video_id}_video_file"
        
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
    
    def get_video_info_from_database(self, video_id: str) -> Dict[str, Any]:
        """Get information about a stored video without retrieving the full file."""
        
        video_document_id = f"{video_id}_video_file"
        
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
