#!/usr/bin/env python3
"""
Query interface for GraphRAG.

This script provides a command-line interface for querying the GraphRAG system.
"""

import os
import sys
import json
import argparse
from azure.identity import DefaultAzureCredential
from azure.mgmt.search import SearchManagementClient
from azure.mgmt.cosmosdb import CosmosDBManagementClient
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient

from graph_operations import GraphOperations
from search_operations import SearchOperations
from embeddings import EmbeddingsClient
from graphrag_client import GraphRAGClient

from dotenv import load_dotenv as loadenv


def get_cosmos_config(subscription_id: str, resource_group: str, account_name: str) -> dict:
    """Get Cosmos DB Gremlin connection configuration."""
    credential = DefaultAzureCredential()
    cosmos_client = CosmosDBManagementClient(credential, subscription_id)
    
    keys = cosmos_client.database_accounts.list_keys(resource_group, account_name)
    
    # Construct Gremlin endpoint from account name
    # Format: wss://{account-name}.gremlin.cosmos.azure.com:443/
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


def print_results(response: dict, verbose: bool = False):
    """Print query results in a formatted way."""
    print("\n" + "=" * 80)
    print("QUERY RESULTS")
    print("=" * 80)
    
    print(f"\nQuery: {response['query']}")
    print(f"Extracted Keywords: {', '.join(response['extractedKeywords'])}")
    print(f"Total Candidates: {response['totalCandidates']}")
    print(f"Top Results: {len(response['results'])}")
    
    for i, result in enumerate(response['results'], 1):
        print("\n" + "-" * 80)
        print(f"Result #{i}")
        print("-" * 80)
        print(f"Chunk ID:    {result['chunkId']}")
        print(f"Document ID: {result['documentId']}")
        print(f"Score:       {result['score']:.4f}")
        
        if 'rerankerScore' in result:
            print(f"Reranker:    {result['rerankerScore']:.4f}")
        
        if result.get('validated'):
            print(f"Validated:   ✓ (keyword edge verified)")
        
        print(f"\nText:\n{result['text']}")
        
        if verbose:
            # Show graph context
            context = result.get('graphContext', {})
            
            if context.get('keywords'):
                print(f"\nKeywords: {', '.join(context['keywords'])}")
            
            if context.get('relatedChunks'):
                print(f"Related Chunks: {', '.join(context['relatedChunks'])}")
            
            if context.get('document'):
                doc = context['document']
                if doc:
                    # Extract values from Gremlin valueMap format
                    title = doc.get('title', [['Unknown']])[0] if 'title' in doc else 'Unknown'
                    print(f"Document: {title}")
    
    print("\n" + "=" * 80)


def main():

    loadenv()  # Load environment variables from .env file if present

    """Main function."""
    parser = argparse.ArgumentParser(
        description='Query GraphRAG system with Cosmos DB Gremlin and Azure AI Search'
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
        help='Number of top results to return (default: 5)'
    )
    parser.add_argument(
        '--no-graph-validation',
        action='store_true',
        help='Disable graph validation of keyword edges'
    )
    parser.add_argument(
        '--semantic',
        action='store_true',
        help='Enable semantic ranking (requires Standard tier Search service)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed graph context information'
    )
    parser.add_argument(
        '--tenant',
        default='default',
        help='Tenant ID for multi-tenancy (default: default)'
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
        print("🔧 Initializing GraphRAG client...")
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
        
        graphrag_client = GraphRAGClient(graph_ops, search_ops, embeddings_client)
        
        # Execute query
        response = graphrag_client.query(
            user_query=args.query,
            top_n=args.top,
            use_graph_validation=not args.no_graph_validation,
            use_semantic_ranking=args.semantic,
            tenant=args.tenant
        )
        
        # Display results
        if args.json:
            print(json.dumps(response, indent=2))
        else:
            print_results(response, verbose=args.verbose)
        
        # Cleanup
        graphrag_client.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
