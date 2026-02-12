#!/usr/bin/env python3
"""
Custom Query interface for GraphRAG - Two-Phase Approach.

This script demonstrates a clear two-phase query approach:
1. Phase 1: Semantic search in Azure AI Search
2. Phase 2: Graph exploration in Cosmos DB Gremlin based on search results
"""

import os
import sys
import json
import argparse
from typing import List, Dict, Any
from azure.identity import DefaultAzureCredential
from azure.mgmt.search import SearchManagementClient
from azure.mgmt.cosmosdb import CosmosDBManagementClient
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient

from graph_operations import GraphOperations
from search_operations import SearchOperations
from embeddings import EmbeddingsClient

from dotenv import load_dotenv as loadenv


def get_cosmos_config(subscription_id: str, resource_group: str, account_name: str) -> dict:
    """Get Cosmos DB Gremlin connection configuration."""
    credential = DefaultAzureCredential()
    cosmos_client = CosmosDBManagementClient(credential, subscription_id)
    
    keys = cosmos_client.database_accounts.list_keys(resource_group, account_name)
    gremlin_endpoint = f"wss://{account_name}.gremlin.cosmos.azure.com:443/"
    
    return {
        'endpoint': gremlin_endpoint,
        'key': keys.primary_master_key
    }


def get_search_config(subscription_id: str, resource_group: str, service_name: str) -> dict:
    """Get Azure AI Search configuration."""
    credential = DefaultAzureCredential()
    search_client = SearchManagementClient(credential, subscription_id)
    
    admin_keys = search_client.admin_keys.get(resource_group, service_name)
    
    return {
        'endpoint': f"https://{service_name}.search.windows.net",
        'key': admin_keys.primary_key
    }


def get_openai_config(subscription_id: str, resource_group: str, account_name: str) -> dict:
    """Get Azure OpenAI configuration."""
    credential = DefaultAzureCredential()
    cognitive_client = CognitiveServicesManagementClient(credential, subscription_id)
    
    account = cognitive_client.accounts.get(resource_group, account_name)
    keys = cognitive_client.accounts.list_keys(resource_group, account_name)
    
    return {
        'endpoint': account.properties.endpoint,
        'key': keys.key1
    }


class TwoPhaseGraphRAG:
    """Two-phase GraphRAG query implementation."""
    
    def __init__(
        self,
        graph_ops: GraphOperations,
        search_ops: SearchOperations,
        embeddings_client: EmbeddingsClient
    ):
        """Initialize the two-phase GraphRAG client."""
        self.graph = graph_ops
        self.search = search_ops
        self.embeddings = embeddings_client
    
    def phase1_semantic_search(
        self,
        query: str,
        top: int = 10
    ) -> Dict[str, Any]:
        """
        Phase 1: Perform semantic search in Azure AI Search.
        
        Uses vector embeddings to find semantically similar chunks.
        """
        print("\n" + "=" * 80)
        print("PHASE 1: SEMANTIC SEARCH (Azure AI Search)")
        print("=" * 80)
        
        # Generate embedding for the query
        print(f"\n📝 Query: '{query}'")
        print("🔄 Generating query embedding...")
        query_embedding = self.embeddings.generate_embedding(query)
        print(f"   Embedding dimensions: {len(query_embedding)}")
        
        # Perform hybrid search (text + vector) with semantic ranking
        print("\n🔍 Performing hybrid search...")
        results = self.search.search_hybrid(
            query=query,
            query_vector=query_embedding,
            top=top,
            filters=None  # No tenant filter for broader search
        )
        
        print(f"\n✅ Found {len(results)} matching chunks")
        
        # Format results
        phase1_results = {
            'query': query,
            'total_results': len(results),
            'chunks': []
        }
        
        for i, result in enumerate(results, 1):
            chunk_info = {
                'rank': i,
                'chunkId': result['chunkId'],
                'documentId': result['documentId'],
                'text': result['text'],
                'score': result['score']
            }
            phase1_results['chunks'].append(chunk_info)
            
            print(f"\n  [{i}] Chunk: {result['chunkId']}")
            print(f"      Document: {result['documentId']}")
            print(f"      Score: {result['score']:.4f}")
            print(f"      Text: {result['text'][:100]}..." if len(result['text']) > 100 else f"      Text: {result['text']}")
        
        return phase1_results
    
    def phase2_graph_exploration(
        self,
        chunk_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Phase 2: Explore graph relationships for the found chunks.
        
        For each chunk from Phase 1, find:
        - Related chunks (via relatedTo edges)
        - Parent section and document
        - Associated keywords
        """
        print("\n" + "=" * 80)
        print("PHASE 2: GRAPH EXPLORATION (Cosmos DB Gremlin)")
        print("=" * 80)
        
        print(f"\n🔗 Exploring graph relationships for {len(chunk_ids)} chunks...")
        
        phase2_results = {
            'explored_chunks': len(chunk_ids),
            'graph_data': [],
            'all_related_chunks': set(),
            'all_documents': set(),
            'all_keywords': set()
        }
        
        for chunk_id in chunk_ids:
            print(f"\n  📊 Chunk: {chunk_id}")
            
            # Get related chunks
            related_chunks = self._get_related_chunks(chunk_id)
            print(f"     Related chunks: {len(related_chunks)}")
            
            # Get parent document info
            document_info = self._get_document_info(chunk_id)
            if document_info:
                print(f"     Document: {document_info.get('title', 'Unknown')}")
            
            # Get section info
            section_info = self._get_section_info(chunk_id)
            if section_info:
                print(f"     Section: {section_info.get('title', 'Unknown')}")
            
            # Get keywords
            keywords = self._get_chunk_keywords(chunk_id)
            print(f"     Keywords: {', '.join(keywords) if keywords else 'None'}")
            
            # Aggregate data
            chunk_graph_data = {
                'chunkId': chunk_id,
                'relatedChunks': related_chunks,
                'document': document_info,
                'section': section_info,
                'keywords': keywords
            }
            phase2_results['graph_data'].append(chunk_graph_data)
            
            # Collect aggregates
            phase2_results['all_related_chunks'].update(related_chunks)
            if document_info and document_info.get('docId'):
                phase2_results['all_documents'].add(document_info.get('docId'))
            phase2_results['all_keywords'].update(keywords)
        
        # Convert sets to lists for JSON serialization
        phase2_results['all_related_chunks'] = list(phase2_results['all_related_chunks'])
        phase2_results['all_documents'] = list(phase2_results['all_documents'])
        phase2_results['all_keywords'] = list(phase2_results['all_keywords'])
        
        # Print summary
        print("\n" + "-" * 40)
        print("GRAPH EXPLORATION SUMMARY")
        print("-" * 40)
        print(f"  Total related chunks found: {len(phase2_results['all_related_chunks'])}")
        print(f"  Unique documents: {len(phase2_results['all_documents'])}")
        print(f"  Unique keywords: {len(phase2_results['all_keywords'])}")
        
        if phase2_results['all_keywords']:
            print(f"\n  Keywords: {', '.join(sorted(phase2_results['all_keywords']))}")
        
        return phase2_results
    
    def _get_related_chunks(self, chunk_id: str) -> List[str]:
        """Get related chunks via graph edges."""
        query = (
            f"g.V().hasLabel('chunk').has('chunkId', '{chunk_id}')"
            f".both('relatedTo').values('chunkId')"
        )
        result = self.graph.execute_query(query)
        return self._flatten_result(result)
    
    def _get_document_info(self, chunk_id: str) -> Dict[str, Any]:
        """Get parent document information."""
        query = (
            f"g.V().hasLabel('chunk').has('chunkId', '{chunk_id}')"
            f".in('hasChunk').in('hasSection').valueMap(true)"
        )
        result = self.graph.execute_query(query)
        if result:
            return self._parse_value_map(result)
        return {}
    
    def _get_section_info(self, chunk_id: str) -> Dict[str, Any]:
        """Get parent section information."""
        query = (
            f"g.V().hasLabel('chunk').has('chunkId', '{chunk_id}')"
            f".in('hasChunk').valueMap(true)"
        )
        result = self.graph.execute_query(query)
        if result:
            return self._parse_value_map(result)
        return {}
    
    def _get_chunk_keywords(self, chunk_id: str) -> List[str]:
        """Get keywords associated with a chunk."""
        query = (
            f"g.V().hasLabel('chunk').has('chunkId', '{chunk_id}')"
            f".in('hasKeyword').values('term')"
        )
        result = self.graph.execute_query(query)
        return self._flatten_result(result)
    
    def _flatten_result(self, result: List) -> List[str]:
        """Flatten nested list results from Gremlin."""
        flat = []
        for item in result:
            if isinstance(item, list):
                flat.extend(self._flatten_result(item))
            else:
                flat.append(str(item))
        return flat
    
    def _parse_value_map(self, value_map) -> Dict[str, Any]:
        """Parse Gremlin valueMap result to simple dict."""
        # Handle nested list from Gremlin
        if isinstance(value_map, list):
            if len(value_map) == 0:
                return {}
            # Take first element if it's a list
            value_map = value_map[0]
            # Recurse if still a list
            if isinstance(value_map, list):
                return self._parse_value_map(value_map)
        
        # If not a dict at this point, return empty
        if not isinstance(value_map, dict):
            return {}
        
        parsed = {}
        for key, value in value_map.items():
            if key in ['id', 'label']:
                parsed[key] = value
            elif isinstance(value, list) and len(value) > 0:
                # Gremlin returns properties as lists
                parsed[key] = value[0] if len(value) == 1 else value
            else:
                parsed[key] = value
        return parsed
    
    def query(self, query_text: str, top: int = 5) -> Dict[str, Any]:
        """
        Execute the full two-phase query.
        
        Returns combined results from both phases.
        """
        # Phase 1: Semantic Search
        phase1 = self.phase1_semantic_search(query_text, top=top)
        
        # Extract chunk IDs for Phase 2
        chunk_ids = [chunk['chunkId'] for chunk in phase1['chunks']]
        
        # Phase 2: Graph Exploration
        phase2 = self.phase2_graph_exploration(chunk_ids)
        
        return {
            'phase1_search': phase1,
            'phase2_graph': phase2
        }
    
    def close(self):
        """Close connections."""
        self.graph.close()


def print_final_summary(results: Dict[str, Any]):
    """Print a final summary of both phases."""
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    phase1 = results['phase1_search']
    phase2 = results['phase2_graph']
    
    print(f"\n📝 Query: '{phase1['query']}'")
    print(f"\n🔍 Phase 1 - Semantic Search Results:")
    print(f"   • Chunks found: {phase1['total_results']}")
    
    print(f"\n🔗 Phase 2 - Graph Exploration Results:")
    print(f"   • Related chunks discovered: {len(phase2['all_related_chunks'])}")
    print(f"   • Documents involved: {len(phase2['all_documents'])}")
    print(f"   • Keywords extracted: {len(phase2['all_keywords'])}")
    
    if phase2['all_keywords']:
        print(f"\n   📌 All Keywords: {', '.join(sorted(phase2['all_keywords']))}")
    
    if phase2['all_related_chunks']:
        print(f"\n   🔗 Related Chunks: {', '.join(phase2['all_related_chunks'][:10])}")
        if len(phase2['all_related_chunks']) > 10:
            print(f"      ... and {len(phase2['all_related_chunks']) - 10} more")
    
    print("\n" + "=" * 80)


def main():
    loadenv()
    
    parser = argparse.ArgumentParser(
        description='Two-Phase GraphRAG Query: Semantic Search + Graph Exploration'
    )
    parser.add_argument(
        '--query', '-q',
        required=True,
        help='Query text to search for'
    )
    parser.add_argument(
        '--top', '-t',
        type=int,
        default=5,
        help='Number of top results from semantic search (default: 5)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results in JSON format'
    )
    
    args = parser.parse_args()
    
    # Get configuration from environment
    subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
    resource_group = os.getenv('RESOURCE_GROUP_NAME', 'rg-graphrag-lab')
    cosmos_account = os.getenv('COSMOS_ACCOUNT_NAME', 'cosmos-graphrag-dev')
    cosmos_database = os.getenv('COSMOS_DATABASE_NAME', 'graphrag-db')
    cosmos_graph = os.getenv('COSMOS_GRAPH_NAME', 'knowledge-graph')
    search_service = os.getenv('SEARCH_SERVICE_NAME', 'search-graphrag-dev')
    search_index = os.getenv('SEARCH_INDEX_NAME', 'chunks-index')
    openai_account = os.getenv('OPENAI_ACCOUNT_NAME', 'oai-graphrag-dev')
    embedding_deployment = os.getenv('EMBEDDING_DEPLOYMENT_NAME', 'text-embedding-3-large')
    
    if not subscription_id:
        print("\n❌ Error: AZURE_SUBSCRIPTION_ID environment variable not set")
        print("Please run: export AZURE_SUBSCRIPTION_ID='your-subscription-id'")
        sys.exit(1)
    
    try:
        # Get service configurations
        print("🔐 Authenticating and retrieving service configurations...")
        cosmos_config = get_cosmos_config(subscription_id, resource_group, cosmos_account)
        search_config = get_search_config(subscription_id, resource_group, search_service)
        openai_config = get_openai_config(subscription_id, resource_group, openai_account)
        
        # Initialize clients
        print("🔧 Initializing Two-Phase GraphRAG client...")
        graph_ops = GraphOperations(
            cosmos_config['endpoint'],
            cosmos_database,
            cosmos_graph,
            cosmos_config['key']
        )
        
        search_ops = SearchOperations(
            search_config['endpoint'],
            search_index,
            search_config['key']
        )
        
        embeddings_client = EmbeddingsClient(
            openai_config['endpoint'],
            openai_config['key'],
            embedding_deployment
        )
        
        # Create two-phase client
        client = TwoPhaseGraphRAG(graph_ops, search_ops, embeddings_client)
        
        # Execute query
        results = client.query(args.query, top=args.top)
        
        # Display results
        if args.json:
            print("\n" + "=" * 80)
            print("JSON OUTPUT")
            print("=" * 80)
            print(json.dumps(results, indent=2, default=str))
        else:
            print_final_summary(results)
        
        # Cleanup
        client.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
