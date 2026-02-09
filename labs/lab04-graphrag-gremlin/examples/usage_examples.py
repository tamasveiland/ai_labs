#!/usr/bin/env python3
"""
Example: Using GraphRAG Client programmatically.

This script demonstrates how to use the GraphRAG client as a library
in your own applications.
"""

import os
import sys

# Add parent directory to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from azure.identity import DefaultAzureCredential
from azure.mgmt.search import SearchManagementClient
from azure.mgmt.cosmosdb import CosmosDBManagementClient
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient

from graph_operations import GraphOperations
from search_operations import SearchOperations
from embeddings import EmbeddingsClient
from graphrag_client import GraphRAGClient


def get_service_configs(subscription_id: str, resource_group: str):
    """Get configuration for all services."""
    credential = DefaultAzureCredential()
    
    # Cosmos DB config
    cosmos_client = CosmosDBManagementClient(credential, subscription_id)
    cosmos_account_name = os.getenv('COSMOS_ACCOUNT_NAME', 'cosmos-graphrag-dev')
    cosmos_keys = cosmos_client.database_accounts.list_keys(resource_group, cosmos_account_name)
    cosmos_account = cosmos_client.database_accounts.get(resource_group, cosmos_account_name)
    
    # Search config
    search_mgmt = SearchManagementClient(credential, subscription_id)
    search_service_name = os.getenv('SEARCH_SERVICE_NAME', 'search-graphrag-dev')
    search_keys = search_mgmt.admin_keys.get(resource_group, search_service_name)
    
    # OpenAI config
    cognitive_client = CognitiveServicesManagementClient(credential, subscription_id)
    openai_account_name = os.getenv('OPENAI_ACCOUNT_NAME', 'oai-graphrag-dev')
    openai_account = cognitive_client.accounts.get(resource_group, openai_account_name)
    openai_keys = cognitive_client.accounts.list_keys(resource_group, openai_account_name)
    
    return {
        'cosmos': {
            'endpoint': cosmos_account.gremlin_endpoint,
            'key': cosmos_keys.primary_master_key,
            'database': os.getenv('COSMOS_DATABASE_NAME', 'graphrag-db'),
            'graph': os.getenv('COSMOS_GRAPH_NAME', 'knowledge-graph')
        },
        'search': {
            'endpoint': f"https://{search_service_name}.search.windows.net",
            'key': search_keys.primary_key,
            'index': os.getenv('SEARCH_INDEX_NAME', 'chunks-index')
        },
        'openai': {
            'endpoint': openai_account.properties.endpoint,
            'key': openai_keys.key1,
            'deployment': os.getenv('EMBEDDING_DEPLOYMENT_NAME', 'text-embedding-3-large')
        }
    }


def example_basic_query():
    """Example: Basic GraphRAG query."""
    print("\n" + "=" * 80)
    print("Example 1: Basic Query")
    print("=" * 80)
    
    # Get configuration
    subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
    resource_group = os.getenv('RESOURCE_GROUP_NAME', 'rg-graphrag-lab')
    
    configs = get_service_configs(subscription_id, resource_group)
    
    # Initialize clients
    graph_ops = GraphOperations(
        configs['cosmos']['endpoint'],
        configs['cosmos']['database'],
        configs['cosmos']['graph'],
        configs['cosmos']['key']
    )
    
    search_ops = SearchOperations(
        configs['search']['endpoint'],
        configs['search']['index'],
        configs['search']['key']
    )
    
    embeddings_client = EmbeddingsClient(
        configs['openai']['endpoint'],
        configs['openai']['key'],
        configs['openai']['deployment']
    )
    
    # Create GraphRAG client
    client = GraphRAGClient(graph_ops, search_ops, embeddings_client)
    
    # Execute query
    response = client.query(
        user_query="What is Azure AI Search?",
        top_n=3,
        use_graph_validation=True
    )
    
    # Display results
    print(f"\nQuery: {response['query']}")
    print(f"Keywords: {', '.join(response['extractedKeywords'])}")
    print(f"Results: {len(response['results'])}\n")
    
    for i, result in enumerate(response['results'], 1):
        print(f"{i}. [{result['score']:.4f}] {result['text'][:100]}...")
    
    # Cleanup
    client.close()


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("GraphRAG Client - Usage Examples")
    print("=" * 80)
    
    # Check environment
    if not os.getenv('AZURE_SUBSCRIPTION_ID'):
        print("\n❌ Error: AZURE_SUBSCRIPTION_ID environment variable not set")
        sys.exit(1)
    
    try:
        # Run examples
        example_basic_query()
        
        print("\n" + "=" * 80)
        print("✅ All Examples Completed")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
