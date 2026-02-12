"""
GraphRAG Client - Main class orchestrating graph and search operations.

This module combines Azure AI Search and Cosmos DB Gremlin for GraphRAG queries.
"""

import re
from typing import List, Dict, Any, Set
from graph_operations import GraphOperations
from search_operations import SearchOperations
from embeddings import EmbeddingsClient


class GraphRAGClient:
    """Main client for GraphRAG operations."""
    
    def __init__(
        self,
        graph_ops: GraphOperations,
        search_ops: SearchOperations,
        embeddings_client: EmbeddingsClient
    ):
        """Initialize GraphRAG client."""
        self.graph = graph_ops
        self.search = search_ops
        self.embeddings = embeddings_client
    
    def extract_keywords(self, query: str) -> List[str]:
        """
        Extract keywords from query.
        
        This is a simple implementation. In production, you might use:
        - NLP libraries (spaCy, NLTK)
        - LLM-based extraction
        - Custom keyword extraction models
        """
        # Simple keyword extraction: lowercase, remove punctuation, split
        query_lower = query.lower()
        # Remove punctuation
        query_clean = re.sub(r'[^\w\s]', '', query_lower)
        # Split and remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'of', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were', 'what',
                     'how', 'when', 'where', 'who', 'which', 'this', 'that', 'these', 'those'}
        words = query_clean.split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return keywords
    
    def query(
        self,
        user_query: str,
        top_n: int = 5,
        use_graph_validation: bool = True,
        use_semantic_ranking: bool = False,
        tenant: str = "default"
    ) -> Dict[str, Any]:
        """
        Execute a GraphRAG query.
        
        Steps:
        1. Extract keywords from query
        2. Perform hybrid search (text + vector)
        3. Optionally validate with graph (keyword edges)
        4. Expand context using graph traversal
        5. Return top-N results with enriched context
        """
        print(f"\n🔍 Processing query: '{user_query}'")
        
        # Step 1: Extract keywords
        print("\n[Step 1/5] Extracting keywords...")
        keywords = self.extract_keywords(user_query)
        print(f"  Keywords: {keywords}")
        
        # Step 2: Generate embedding
        print("\n[Step 2/5] Generating query embedding...")
        query_embedding = self.embeddings.generate_embedding(user_query)
        print(f"  Embedding dimensions: {len(query_embedding)}")
        
        # Step 3: Hybrid search
        print("\n[Step 3/5] Performing hybrid search...")
        if use_semantic_ranking:
            search_results = self.search.search_with_semantic_ranking(
                user_query,
                query_embedding,
                top=50,
                filters=f"tenant eq '{tenant}'"
            )
        else:
            search_results = self.search.search_hybrid(
                user_query,
                query_embedding,
                top=50,
                filters=f"tenant eq '{tenant}'"
            )
        print(f"  Found {len(search_results)} candidates")
        
        # Step 4: Graph validation (optional)
        if use_graph_validation and keywords:
            print("\n[Step 4/5] Validating with graph (keyword edges)...")
            validated_results = []
            for result in search_results:
                chunk_id = result['chunkId']
                # Check if chunk has any of the query keywords
                has_keyword = False
                for keyword in keywords:
                    if self.graph.verify_keyword_edge(chunk_id, keyword):
                        has_keyword = True
                        break
                
                if has_keyword:
                    result['validated'] = True
                    validated_results.append(result)
            
            print(f"  Validated {len(validated_results)} chunks with keyword edges")
            # Use validated results if we have enough, otherwise fall back to search results
            if len(validated_results) >= top_n:
                search_results = validated_results
        else:
            print("\n[Step 4/5] Skipping graph validation")
        
        # Step 5: Graph expansion
        print("\n[Step 5/5] Expanding context via graph...")
        enriched_results = []
        for i, result in enumerate(search_results[:top_n]):
            chunk_id = result['chunkId']
            
            # Expand context from graph
            context = self.graph.expand_context_from_chunk(chunk_id, tenant)
            
            # Get full chunk text from graph
            chunk_text = self.graph.get_chunk_text(chunk_id)
            
            enriched_result = {
                **result,
                'text': chunk_text if chunk_text else result.get('text', ''),
                'graphContext': {
                    'relatedChunks': context.get('relatedChunks', []),
                    'section': context.get('section', {}),
                    'document': context.get('document', {}),
                    'keywords': context.get('keywords', [])
                }
            }
            enriched_results.append(enriched_result)
        
        print(f"  Enriched {len(enriched_results)} results with graph context")
        
        return {
            'query': user_query,
            'extractedKeywords': keywords,
            'totalCandidates': len(search_results),
            'results': enriched_results
        }
    
    def get_document_chunks(self, doc_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a specific document."""
        return self.graph.find_chunks_by_document(doc_id)
    
    def close(self):
        """Close all client connections."""
        self.graph.close()
        self.search.close()
