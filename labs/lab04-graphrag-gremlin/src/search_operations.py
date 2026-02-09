"""
Search operations for Azure AI Search.

This module provides functions for searching and ranking chunks using Azure AI Search.
"""

from typing import List, Dict, Any, Optional
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery


class SearchOperations:
    """Handle Azure AI Search operations."""
    
    def __init__(self, endpoint: str, index_name: str, api_key: str):
        """Initialize Search client."""
        self.client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(api_key)
        )
    
    def search_text(
        self,
        query: str,
        top: int = 10,
        filters: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Perform full-text search."""
        results = self.client.search(
            search_text=query,
            top=top,
            filter=filters,
            select=["chunkId", "documentId", "text", "keywords"]
        )
        
        return [
            {
                'chunkId': result['chunkId'],
                'documentId': result['documentId'],
                'text': result['text'],
                'keywords': result.get('keywords', []),
                'score': result['@search.score']
            }
            for result in results
        ]
    
    def search_vector(
        self,
        query_vector: List[float],
        top: int = 10,
        filters: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Perform vector similarity search."""
        vector_query = VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=top,
            fields="embedding"
        )
        
        results = self.client.search(
            vector_queries=[vector_query],
            top=top,
            filter=filters,
            select=["chunkId", "documentId", "text", "keywords"]
        )
        
        return [
            {
                'chunkId': result['chunkId'],
                'documentId': result['documentId'],
                'text': result['text'],
                'keywords': result.get('keywords', []),
                'score': result['@search.score']
            }
            for result in results
        ]
    
    def search_hybrid(
        self,
        query: str,
        query_vector: List[float],
        top: int = 10,
        filters: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search combining text and vector search."""
        vector_query = VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=50,  # Get more candidates for reranking
            fields="embedding"
        )
        
        results = self.client.search(
            search_text=query,
            vector_queries=[vector_query],
            top=top,
            filter=filters,
            select=["chunkId", "documentId", "text", "keywords", "position"]
        )
        
        return [
            {
                'chunkId': result['chunkId'],
                'documentId': result['documentId'],
                'text': result['text'],
                'keywords': result.get('keywords', []),
                'position': result.get('position', 0),
                'score': result['@search.score']
            }
            for result in results
        ]
    
    def search_with_semantic_ranking(
        self,
        query: str,
        query_vector: List[float],
        top: int = 10,
        filters: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search with semantic ranking."""
        vector_query = VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=50,
            fields="embedding"
        )
        
        results = self.client.search(
            search_text=query,
            vector_queries=[vector_query],
            query_type="semantic",
            semantic_configuration_name="semantic-config",
            top=top,
            filter=filters,
            select=["chunkId", "documentId", "text", "keywords"]
        )
        
        return [
            {
                'chunkId': result['chunkId'],
                'documentId': result['documentId'],
                'text': result['text'],
                'keywords': result.get('keywords', []),
                'score': result['@search.score'],
                'rerankerScore': result.get('@search.reranker_score', 0)
            }
            for result in results
        ]
    
    def get_document_by_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific document by chunk ID."""
        try:
            result = self.client.get_document(key=chunk_id)
            return result
        except Exception:
            return None
    
    def close(self):
        """Close the search client connection."""
        if self.client:
            self.client.close()
