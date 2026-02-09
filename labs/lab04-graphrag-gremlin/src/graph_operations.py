"""
Graph operations for Cosmos DB Gremlin API.

This module provides functions for querying and traversing the knowledge graph.
"""

import re
from typing import List, Dict, Any
from gremlin_python.driver import client, serializer
from gremlin_python.driver.protocol import GremlinServerError


def sanitize_input(value: str) -> str:
    """
    Sanitize input to prevent Gremlin injection.
    
    Allows only alphanumeric characters, hyphens, and underscores.
    This prevents special characters that could be used for injection.
    """
    if not value:
        return ""
    # Only allow alphanumeric, hyphens, underscores, and spaces
    sanitized = re.sub(r'[^a-zA-Z0-9\-_\s]', '', value)
    return sanitized


class GraphOperations:
    """Handle Gremlin graph operations."""
    
    def __init__(self, endpoint: str, database: str, graph: str, key: str):
        """Initialize Gremlin client."""
        # Extract host from endpoint
        host = endpoint.replace('https://', '').replace(':443/', '')
        
        self.client = client.Client(
            f'wss://{host}:443/',
            'g',
            username=f"/dbs/{database}/colls/{graph}",
            password=key,
            message_serializer=serializer.GraphSONSerializersV2d0()
        )
    
    def execute_query(self, query: str) -> List[Any]:
        """Execute a Gremlin query."""
        try:
            callback = self.client.submitAsync(query)
            result = callback.result()
            return list(result)
        except GremlinServerError as e:
            print(f"Error executing query: {e}")
            return []
    
    def get_chunks_by_keyword(self, keyword: str, tenant: str = "default") -> List[str]:
        """Get chunk IDs that have a specific keyword."""
        # Sanitize inputs to prevent injection
        keyword = sanitize_input(keyword)
        tenant = sanitize_input(tenant)
        
        query = (
            f"g.V().hasLabel('keyword').has('term', '{keyword}')"
            f".out('hasKeyword').has('tenant', '{tenant}')"
            f".values('chunkId')"
        )
        return self.execute_query(query)
    
    def expand_context_from_chunk(self, chunk_id: str, tenant: str = "default") -> Dict[str, Any]:
        """
        Expand context from a chunk by traversing the graph.
        
        Returns:
        - Related chunks (via relatedTo edges)
        - Parent section
        - Parent document
        - Associated keywords
        """
        # Sanitize inputs to prevent injection
        chunk_id = sanitize_input(chunk_id)
        tenant = sanitize_input(tenant)
        
        # Get related chunks
        related_chunks_query = (
            f"g.V().hasLabel('chunk').has('chunkId', '{chunk_id}')"
            f".both('relatedTo').values('chunkId')"
        )
        related_chunks = self.execute_query(related_chunks_query)
        
        # Get parent section
        section_query = (
            f"g.V().hasLabel('chunk').has('chunkId', '{chunk_id}')"
            f".in('hasChunk').valueMap()"
        )
        section_result = self.execute_query(section_query)
        section = section_result[0] if section_result else {}
        
        # Get parent document
        document_query = (
            f"g.V().hasLabel('chunk').has('chunkId', '{chunk_id}')"
            f".in('hasChunk').in('hasSection').valueMap()"
        )
        document_result = self.execute_query(document_query)
        document = document_result[0] if document_result else {}
        
        # Get associated keywords
        keywords_query = (
            f"g.V().hasLabel('chunk').has('chunkId', '{chunk_id}')"
            f".in('hasKeyword').values('term')"
        )
        keywords = self.execute_query(keywords_query)
        
        return {
            'chunkId': chunk_id,
            'relatedChunks': related_chunks,
            'section': section,
            'document': document,
            'keywords': keywords
        }
    
    def verify_keyword_edge(self, chunk_id: str, keyword: str) -> bool:
        """Verify if a chunk has a specific keyword edge."""
        # Sanitize inputs to prevent injection
        chunk_id = sanitize_input(chunk_id)
        keyword = sanitize_input(keyword)
        
        query = (
            f"g.V().hasLabel('keyword').has('term', '{keyword}')"
            f".out('hasKeyword').has('chunkId', '{chunk_id}').count()"
        )
        result = self.execute_query(query)
        return result[0] > 0 if result else False
    
    def get_chunk_text(self, chunk_id: str) -> str:
        """Get the text content of a chunk."""
        # Sanitize inputs to prevent injection
        chunk_id = sanitize_input(chunk_id)
        
        query = (
            f"g.V().hasLabel('chunk').has('chunkId', '{chunk_id}')"
            f".values('text')"
        )
        result = self.execute_query(query)
        return result[0] if result else ""
    
    def get_neighboring_chunks(self, chunk_id: str, max_distance: int = 2) -> List[str]:
        """Get chunks within a certain graph distance."""
        # Sanitize inputs to prevent injection
        chunk_id = sanitize_input(chunk_id)
        # Validate max_distance is an integer and within reasonable bounds
        max_distance = max(1, min(int(max_distance), 10))
        
        query = (
            f"g.V().hasLabel('chunk').has('chunkId', '{chunk_id}')"
            f".repeat(both().simplePath()).times({max_distance})"
            f".hasLabel('chunk').dedup().values('chunkId')"
        )
        return self.execute_query(query)
    
    def find_chunks_by_document(self, doc_id: str) -> List[Dict[str, Any]]:
        """Find all chunks for a specific document."""
        # Sanitize inputs to prevent injection
        doc_id = sanitize_input(doc_id)
        
        query = (
            f"g.V().hasLabel('document').has('docId', '{doc_id}')"
            f".out('hasSection').out('hasChunk').valueMap()"
        )
        return self.execute_query(query)
    
    def close(self):
        """Close the Gremlin client connection."""
        if self.client:
            self.client.close()
