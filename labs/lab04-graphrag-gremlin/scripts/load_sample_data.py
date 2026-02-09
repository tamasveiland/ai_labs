#!/usr/bin/env python3
"""
Load sample data into Azure AI Search index.

This script generates embeddings and loads chunk data into the search index.
"""

import os
import sys
from typing import List, Dict
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.mgmt.search import SearchManagementClient
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from openai import AzureOpenAI

def get_search_admin_key(subscription_id: str, resource_group: str, service_name: str) -> str:
    """Get the admin key for Azure AI Search."""
    credential = DefaultAzureCredential()
    search_mgmt_client = SearchManagementClient(credential, subscription_id)
    admin_keys = search_mgmt_client.admin_keys.get(resource_group, service_name)
    return admin_keys.primary_key

def get_openai_config(subscription_id: str, resource_group: str, account_name: str) -> Dict[str, str]:
    """Get OpenAI endpoint and key."""
    credential = DefaultAzureCredential()
    cognitive_client = CognitiveServicesManagementClient(credential, subscription_id)
    
    # Get account
    account = cognitive_client.accounts.get(resource_group, account_name)
    endpoint = account.properties.endpoint
    
    # Get keys
    keys = cognitive_client.accounts.list_keys(resource_group, account_name)
    
    return {
        'endpoint': endpoint,
        'key': keys.key1
    }

def generate_embedding(openai_client: AzureOpenAI, text: str, deployment: str) -> List[float]:
    """Generate embedding for text using Azure OpenAI."""
    response = openai_client.embeddings.create(
        input=text,
        model=deployment
    )
    return response.data[0].embedding

def get_sample_chunks() -> List[Dict]:
    """Get sample chunk data."""
    return [
        {
            "chunkId": "chunk-001",
            "documentId": "doc-001",
            "sectionId": "sec-001",
            "text": "Azure AI Services provides comprehensive AI capabilities including OpenAI models.",
            "keywords": ["azure", "ai", "openai", "services"],
            "tenant": "default",
            "position": 1,
            "metadata": '{"source": "azure-docs", "category": "overview"}'
        },
        {
            "chunkId": "chunk-002",
            "documentId": "doc-001",
            "sectionId": "sec-002",
            "text": "Azure AI Search enables vector search and hybrid retrieval for RAG applications.",
            "keywords": ["azure", "search", "vector", "rag", "hybrid"],
            "tenant": "default",
            "position": 2,
            "metadata": '{"source": "azure-docs", "category": "search"}'
        },
        {
            "chunkId": "chunk-003",
            "documentId": "doc-001",
            "sectionId": "sec-002",
            "text": "Semantic ranking and scoring help improve search relevance for AI applications.",
            "keywords": ["semantic", "ranking", "search", "ai", "relevance"],
            "tenant": "default",
            "position": 3,
            "metadata": '{"source": "azure-docs", "category": "search"}'
        },
        {
            "chunkId": "chunk-004",
            "documentId": "doc-002",
            "sectionId": "sec-003",
            "text": "Graph databases store data as vertices and edges representing relationships.",
            "keywords": ["graph", "database", "vertices", "edges", "relationships"],
            "tenant": "default",
            "position": 1,
            "metadata": '{"source": "graph-theory", "category": "concepts"}'
        }
    ]

def load_data_to_search(
    search_client: SearchClient,
    openai_client: AzureOpenAI,
    embedding_deployment: str,
    chunks: List[Dict]
):
    """Load chunk data with embeddings to search index."""
    
    print(f"\n📤 Loading {len(chunks)} chunks to search index...")
    
    documents = []
    for i, chunk in enumerate(chunks, 1):
        print(f"  Processing chunk {i}/{len(chunks)}: {chunk['chunkId']}")
        
        # Generate embedding
        embedding = generate_embedding(openai_client, chunk['text'], embedding_deployment)
        
        # Create document
        document = {
            **chunk,
            'embedding': embedding
        }
        documents.append(document)
    
    # Upload to search index
    print(f"\n  Uploading documents to search index...")
    result = search_client.upload_documents(documents=documents)
    
    succeeded = sum(1 for r in result if r.succeeded)
    failed = sum(1 for r in result if not r.succeeded)
    
    print(f"✓ Upload complete: {succeeded} succeeded, {failed} failed")
    
    return succeeded

def main():
    """Main function."""
    print("\n" + "=" * 80)
    print("GraphRAG - Load Sample Data")
    print("=" * 80)
    
    # Get configuration from environment
    subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
    resource_group = os.getenv('RESOURCE_GROUP_NAME', 'rg-graphrag-lab')
    search_service_name = os.getenv('SEARCH_SERVICE_NAME', 'search-graphrag-dev')
    index_name = os.getenv('SEARCH_INDEX_NAME', 'chunks-index')
    openai_account_name = os.getenv('OPENAI_ACCOUNT_NAME', 'oai-graphrag-dev')
    embedding_deployment = os.getenv('EMBEDDING_DEPLOYMENT_NAME', 'text-embedding-3-large')
    
    if not subscription_id:
        print("\n❌ Error: AZURE_SUBSCRIPTION_ID environment variable not set")
        print("Please run: export AZURE_SUBSCRIPTION_ID='your-subscription-id'")
        sys.exit(1)
    
    print(f"\nConfiguration:")
    print(f"  Subscription:           {subscription_id}")
    print(f"  Resource Group:         {resource_group}")
    print(f"  Search Service:         {search_service_name}")
    print(f"  Index Name:             {index_name}")
    print(f"  OpenAI Account:         {openai_account_name}")
    print(f"  Embedding Deployment:   {embedding_deployment}")
    
    try:
        # Get search admin key
        print("\n🔐 Getting Azure AI Search admin key...")
        search_key = get_search_admin_key(subscription_id, resource_group, search_service_name)
        
        # Get OpenAI config
        print("🔐 Getting Azure OpenAI configuration...")
        openai_config = get_openai_config(subscription_id, resource_group, openai_account_name)
        
        # Create clients
        search_endpoint = f"https://{search_service_name}.search.windows.net"
        search_client = SearchClient(
            search_endpoint,
            index_name,
            AzureKeyCredential(search_key)
        )
        
        openai_client = AzureOpenAI(
            api_key=openai_config['key'],
            api_version="2024-02-01",
            azure_endpoint=openai_config['endpoint']
        )
        
        # Get sample data
        chunks = get_sample_chunks()
        
        # Load data
        count = load_data_to_search(search_client, openai_client, embedding_deployment, chunks)
        
        print("\n" + "=" * 80)
        print("✅ Data Loading Complete!")
        print("=" * 80)
        print(f"\nLoaded {count} chunks to index: {index_name}")
        print("\nNext Steps:")
        print("  1. Test search queries:")
        print("     python src/query_graphrag.py --query 'azure ai services'")
        print("  2. View data in Azure Portal:")
        print(f"     https://portal.azure.com/#@/resource/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Search/searchServices/{search_service_name}")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
