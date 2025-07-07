
from typing import Any, Dict, Optional
import chromadb

class ChromaDB:
    def __init__(self, collection_name: str = "video_transcriptions", database_path: str = "./chroma_db"):
        """Initialize the transcription and ChromaDB integration."""
        # Configure ChromaDB to save data to disk
        self.client = chromadb.PersistentClient(path=database_path)
        self.collection_name = collection_name
        
        # Create or get the collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            print(f"Using existing collection: {collection_name}")
            print(f"Data saved to: {database_path}")
        except Exception:
            self.collection = self.client.create_collection(name=collection_name)
            print(f"Created new collection: {collection_name}")
            print(f"Data will be saved to: {database_path}")
    

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