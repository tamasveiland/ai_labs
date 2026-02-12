#!/usr/bin/env python3
"""
Set up Azure AI Search index for GraphRAG chunks.

This script creates a search index with vector search capabilities for the chunk data.
"""

import os
import sys
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch
)
from azure.mgmt.search import SearchManagementClient
from dotenv import load_dotenv as loadenv


def get_search_admin_key(subscription_id: str, resource_group: str, service_name: str) -> str:
    """Get the admin key for Azure AI Search."""
    credential = DefaultAzureCredential()
    search_mgmt_client = SearchManagementClient(credential, subscription_id)
    
    admin_keys = search_mgmt_client.admin_keys.get(resource_group, service_name)
    return admin_keys.primary_key

def create_chunks_index(index_client: SearchIndexClient, index_name: str, embedding_dimensions: int = 3072):
    """Create the chunks search index with vector search.
    
    Args:
        index_client: The SearchIndexClient instance
        index_name: Name of the index to create
        embedding_dimensions: Dimensions for the embedding vector (default: 3072 for text-embedding-3-large)
    """
    
    print(f"\n📊 Creating search index: {index_name}")
    
    # Define fields - aligned with Cosmos DB Gremlin chunk vertex properties
    # The indexer will pull: id (→chunkId), docId (→documentId), text, tenant, position
    # The skillset will generate: embedding
    fields = [
        SimpleField(
            name="chunkId",
            type=SearchFieldDataType.String,
            key=True,
            filterable=True,
            sortable=True
        ),
        SimpleField(
            name="documentId",
            type=SearchFieldDataType.String,
            filterable=True,
            sortable=True
        ),
        SearchableField(
            name="text",
            type=SearchFieldDataType.String,
            analyzer_name="en.microsoft"
        ),
        SearchField(
            name="embedding",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=embedding_dimensions,
            vector_search_profile_name="embedding-profile"
        ),
        SimpleField(
            name="tenant",
            type=SearchFieldDataType.String,
            filterable=True
        ),
        SimpleField(
            name="position",
            type=SearchFieldDataType.Int32,
            filterable=True,
            sortable=True
        )
    ]
    
    # Configure vector search
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="hnsw-algorithm",
                parameters={
                    "m": 4,
                    "efConstruction": 400,
                    "efSearch": 500,
                    "metric": "cosine"
                }
            )
        ],
        profiles=[
            VectorSearchProfile(
                name="embedding-profile",
                algorithm_configuration_name="hnsw-algorithm"
            )
        ]
    )
    
    # Configure semantic search
    semantic_config = SemanticConfiguration(
        name="semantic-config",
        prioritized_fields=SemanticPrioritizedFields(
            content_fields=[
                SemanticField(field_name="text")
            ]
        )
    )
    
    semantic_search = SemanticSearch(
        configurations=[semantic_config]
    )
    
    # Create the index
    index = SearchIndex(
        name=index_name,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search
    )
    
    try:
        result = index_client.create_or_update_index(index)
        print(f"✓ Search index created: {result.name}")
        print(f"  Fields: {len(result.fields)}")
        print(f"  Vector search: Enabled ({embedding_dimensions} dimensions)")
        print(f"  Semantic search: Enabled")
        return result
    except Exception as e:
        print(f"❌ Error creating index: {e}")
        raise

def main():
    """Main function."""
    print("\n" + "=" * 80)
    print("GraphRAG - Setup Azure AI Search Index")
    print("=" * 80)

    loadenv()  # Load environment variables from .env file if present
    
    # Get configuration from environment
    subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
    resource_group = os.getenv('RESOURCE_GROUP_NAME', 'rg-graphrag-lab')
    search_service_name = os.getenv('SEARCH_SERVICE_NAME', 'search-graphrag-dev')
    index_name = os.getenv('SEARCH_INDEX_NAME', 'chunks-index')
    
    if not subscription_id:
        print("\n❌ Error: AZURE_SUBSCRIPTION_ID environment variable not set")
        print("Please run: export AZURE_SUBSCRIPTION_ID='your-subscription-id'")
        sys.exit(1)
    
    print(f"\nConfiguration:")
    embedding_model = os.getenv('EMBEDDING_MODEL_NAME', 'text-embedding-3-large')
    # text-embedding-3-large uses 3072 dimensions, text-embedding-3-small uses 1536
    embedding_dimensions = 3072 if 'large' in embedding_model else 1536
    
    print(f"  Subscription:      {subscription_id}")
    print(f"  Resource Group:    {resource_group}")
    print(f"  Search Service:    {search_service_name}")
    print(f"  Index Name:        {index_name}")
    print(f"  Embedding Model:   {embedding_model}")
    print(f"  Embedding Dims:    {embedding_dimensions}")
    
    try:
        # Get search admin key
        print("\n🔐 Getting Azure AI Search admin key...")
        admin_key = get_search_admin_key(subscription_id, resource_group, search_service_name)
        
        # Create index client
        search_endpoint = f"https://{search_service_name}.search.windows.net"
        credential = AzureKeyCredential(admin_key)
        index_client = SearchIndexClient(search_endpoint, credential)
        
        # Create index
        create_chunks_index(index_client, index_name, embedding_dimensions)
        
        print("\n" + "=" * 80)
        print("✅ Search Index Setup Complete!")
        print("=" * 80)
        print("\nIndex Details:")
        print(f"  Name: {index_name}")
        print(f"  Endpoint: {search_endpoint}")
        print("\nNext Steps:")
        print("  1. Run: python scripts/setup_search_indexer.py  # Set up automatic indexing")
        print("  2. Test queries with: python src/query_graphrag.py")
        print("\nAlternatively, for manual data loading:")
        print("  python scripts/load_sample_data.py")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
