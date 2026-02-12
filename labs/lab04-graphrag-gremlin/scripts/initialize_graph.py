#!/usr/bin/env python3
"""
Initialize the Gremlin graph database schema.

This script connects to the Cosmos DB Gremlin API and creates sample vertices and edges
to demonstrate the GraphRAG data model.
"""

import os
import sys
from gremlin_python.driver import client, serializer
from gremlin_python.driver.protocol import GremlinServerError
from azure.identity import DefaultAzureCredential
from azure.mgmt.cosmosdb import CosmosDBManagementClient
from dotenv import load_dotenv as loadenv

def get_gremlin_connection_info(subscription_id: str, resource_group: str, account_name: str):
    """Get Gremlin connection information from Azure."""
    credential = DefaultAzureCredential()
    cosmos_client = CosmosDBManagementClient(credential, subscription_id)
    
    # Get account keys
    keys = cosmos_client.database_accounts.list_keys(resource_group, account_name)
    
    # Construct Gremlin endpoint from account name
    # Format: wss://{account_name}.gremlin.cosmos.azure.com:443/
    gremlin_endpoint = f"wss://{account_name}.gremlin.cosmos.azure.com:443/"
    
    return {
        'endpoint': gremlin_endpoint,
        'key': keys.primary_master_key
    }

def create_gremlin_client(endpoint: str, database: str, graph: str, key: str):
    """Create Gremlin client connection."""
    # Endpoint is already in format: wss://{account}.gremlin.cosmos.azure.com:443/
    # Just use it directly
    return client.Client(
        endpoint,
        'g',
        username=f"/dbs/{database}/colls/{graph}",
        password=key,
        message_serializer=serializer.GraphSONSerializersV2d0()
    )

def execute_query(gremlin_client, query: str):
    """Execute a Gremlin query."""
    try:
        callback = gremlin_client.submitAsync(query)
        result_set = callback.result()
        # Convert ResultSet to list for subscripting
        return list(result_set)
    except GremlinServerError as e:
        print(f"Error executing query: {e}")
        return None

def initialize_graph_schema(gremlin_client):
    """Initialize the graph schema with sample data."""
    
    print("\n📊 Initializing Graph Schema...")
    
    # Drop all existing data (optional - for clean start)
    print("  Cleaning existing data...")
    execute_query(gremlin_client, "g.V().drop()")
    
    # Create Document vertices
    print("  Creating Document vertices...")
    doc_queries = [
        "g.addV('document').property('id', 'doc-001').property('docId', 'doc-001')" +
        ".property('title', 'Azure AI Services Overview').property('author', 'Microsoft')" +
        ".property('tenant', 'default').property('createdAt', '2024-01-15')",
        
        "g.addV('document').property('id', 'doc-002').property('docId', 'doc-002')" +
        ".property('title', 'Graph Databases and RAG').property('author', 'Research Team')" +
        ".property('tenant', 'default').property('createdAt', '2024-02-01')",
    ]
    
    for query in doc_queries:
        execute_query(gremlin_client, query)
    
    # Create Section vertices
    print("  Creating Section vertices...")
    section_queries = [
        "g.addV('section').property('id', 'sec-001').property('sectionId', 'sec-001')" +
        ".property('order', 1).property('title', 'Introduction').property('docId', 'doc-001')" +
        ".property('tenant', 'default')",
        
        "g.addV('section').property('id', 'sec-002').property('sectionId', 'sec-002')" +
        ".property('order', 2).property('title', 'Key Features').property('docId', 'doc-001')" +
        ".property('tenant', 'default')",
        
        "g.addV('section').property('id', 'sec-003').property('sectionId', 'sec-003')" +
        ".property('order', 1).property('title', 'Graph Theory Basics').property('docId', 'doc-002')" +
        ".property('tenant', 'default')",
    ]
    
    for query in section_queries:
        execute_query(gremlin_client, query)
    
    # Create Chunk vertices
    print("  Creating Chunk vertices...")
    chunk_queries = [
        "g.addV('chunk').property('id', 'chunk-001').property('chunkId', 'chunk-001')" +
        ".property('position', 1).property('textHash', 'hash001')" +
        ".property('text', 'Azure AI Services provides comprehensive AI capabilities including OpenAI models.')" +
        ".property('docId', 'doc-001').property('tenant', 'default')",
        
        "g.addV('chunk').property('id', 'chunk-002').property('chunkId', 'chunk-002')" +
        ".property('position', 2).property('textHash', 'hash002')" +
        ".property('text', 'Azure AI Search enables vector search and hybrid retrieval for RAG applications.')" +
        ".property('docId', 'doc-001').property('tenant', 'default')",
        
        "g.addV('chunk').property('id', 'chunk-003').property('chunkId', 'chunk-003')" +
        ".property('position', 3).property('textHash', 'hash003')" +
        ".property('text', 'Semantic ranking and scoring help improve search relevance for AI applications.')" +
        ".property('docId', 'doc-001').property('tenant', 'default')",
        
        "g.addV('chunk').property('id', 'chunk-004').property('chunkId', 'chunk-004')" +
        ".property('position', 1).property('textHash', 'hash004')" +
        ".property('text', 'Graph databases store data as vertices and edges representing relationships.')" +
        ".property('docId', 'doc-002').property('tenant', 'default')",
    ]
    
    for query in chunk_queries:
        execute_query(gremlin_client, query)
    
    # Create Keyword vertices
    print("  Creating Keyword vertices...")
    keyword_queries = [
        "g.addV('keyword').property('id', 'kw-azure').property('term', 'azure').property('frequency', 10).property('tenant', 'default')",
        "g.addV('keyword').property('id', 'kw-ai').property('term', 'ai').property('frequency', 8).property('tenant', 'default')",
        "g.addV('keyword').property('id', 'kw-search').property('term', 'search').property('frequency', 6).property('tenant', 'default')",
        "g.addV('keyword').property('id', 'kw-graph').property('term', 'graph').property('frequency', 5).property('tenant', 'default')",
        "g.addV('keyword').property('id', 'kw-rag').property('term', 'rag').property('frequency', 7).property('tenant', 'default')",
    ]
    
    for query in keyword_queries:
        execute_query(gremlin_client, query)
    
    # Create edges: hasSection (Document -> Section)
    print("  Creating hasSection edges...")
    has_section_queries = [
        "g.V().has('document', 'docId', 'doc-001').addE('hasSection').to(g.V().has('section', 'sectionId', 'sec-001'))",
        "g.V().has('document', 'docId', 'doc-001').addE('hasSection').to(g.V().has('section', 'sectionId', 'sec-002'))",
        "g.V().has('document', 'docId', 'doc-002').addE('hasSection').to(g.V().has('section', 'sectionId', 'sec-003'))",
    ]
    
    for query in has_section_queries:
        execute_query(gremlin_client, query)
    
    # Create edges: hasChunk (Section -> Chunk)
    print("  Creating hasChunk edges...")
    has_chunk_queries = [
        "g.V().has('section', 'sectionId', 'sec-001').addE('hasChunk').to(g.V().has('chunk', 'chunkId', 'chunk-001'))",
        "g.V().has('section', 'sectionId', 'sec-002').addE('hasChunk').to(g.V().has('chunk', 'chunkId', 'chunk-002'))",
        "g.V().has('section', 'sectionId', 'sec-002').addE('hasChunk').to(g.V().has('chunk', 'chunkId', 'chunk-003'))",
        "g.V().has('section', 'sectionId', 'sec-003').addE('hasChunk').to(g.V().has('chunk', 'chunkId', 'chunk-004'))",
    ]
    
    for query in has_chunk_queries:
        execute_query(gremlin_client, query)
    
    # Create edges: hasKeyword (Keyword -> Chunk)
    print("  Creating hasKeyword edges...")
    has_keyword_queries = [
        "g.V().has('keyword', 'term', 'azure').addE('hasKeyword').to(g.V().has('chunk', 'chunkId', 'chunk-001'))",
        "g.V().has('keyword', 'term', 'azure').addE('hasKeyword').to(g.V().has('chunk', 'chunkId', 'chunk-002'))",
        "g.V().has('keyword', 'term', 'ai').addE('hasKeyword').to(g.V().has('chunk', 'chunkId', 'chunk-001'))",
        "g.V().has('keyword', 'term', 'search').addE('hasKeyword').to(g.V().has('chunk', 'chunkId', 'chunk-002'))",
        "g.V().has('keyword', 'term', 'rag').addE('hasKeyword').to(g.V().has('chunk', 'chunkId', 'chunk-002'))",
        "g.V().has('keyword', 'term', 'graph').addE('hasKeyword').to(g.V().has('chunk', 'chunkId', 'chunk-004'))",
    ]
    
    for query in has_keyword_queries:
        execute_query(gremlin_client, query)
    
    # Create edges: relatedTo (Chunk -> Chunk)
    print("  Creating relatedTo edges...")
    related_to_queries = [
        "g.V().has('chunk', 'chunkId', 'chunk-001').addE('relatedTo').to(g.V().has('chunk', 'chunkId', 'chunk-002'))",
        "g.V().has('chunk', 'chunkId', 'chunk-002').addE('relatedTo').to(g.V().has('chunk', 'chunkId', 'chunk-003'))",
    ]
    
    for query in related_to_queries:
        execute_query(gremlin_client, query)
    
    print("✓ Graph schema initialized successfully!")

def verify_graph(gremlin_client):
    """Verify the graph structure."""
    print("\n🔍 Verifying Graph Structure...")
    
    # Count vertices by label
    labels = ['document', 'section', 'chunk', 'keyword']
    for label in labels:
        result = execute_query(gremlin_client, f"g.V().hasLabel('{label}').count()")
        count = result[0] if result else 0
        print(f"  {label.capitalize()} vertices: {count}")
    
    # Count edges by label
    edge_labels = ['hasSection', 'hasChunk', 'hasKeyword', 'relatedTo']
    for label in edge_labels:
        result = execute_query(gremlin_client, f"g.E().hasLabel('{label}').count()")
        count = result[0] if result else 0
        print(f"  {label} edges: {count}")

def main():
    """Main function."""
    print("\n" + "=" * 80)
    print("GraphRAG - Initialize Gremlin Graph")
    print("=" * 80)

    loadenv()
    
    # Get configuration from environment
    subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
    resource_group = os.getenv('RESOURCE_GROUP_NAME', 'rg-graphrag-lab')
    account_name = os.getenv('COSMOS_ACCOUNT_NAME', 'cosmos-graphrag-dev')
    database_name = os.getenv('COSMOS_DATABASE_NAME', 'graphrag-db')
    graph_name = os.getenv('COSMOS_GRAPH_NAME', 'knowledge-graph')
    
    if not subscription_id:
        print("\n❌ Error: AZURE_SUBSCRIPTION_ID environment variable not set")
        print("Please run: export AZURE_SUBSCRIPTION_ID='your-subscription-id'")
        sys.exit(1)
    
    print(f"\nConfiguration:")
    print(f"  Subscription:     {subscription_id}")
    print(f"  Resource Group:   {resource_group}")
    print(f"  Cosmos Account:   {account_name}")
    print(f"  Database:         {database_name}")
    print(f"  Graph:            {graph_name}")
    
    try:
        # Get connection info
        print("\n🔐 Getting Cosmos DB connection information...")
        conn_info = get_gremlin_connection_info(subscription_id, resource_group, account_name)
        
        # Create Gremlin client
        print("🔌 Connecting to Gremlin graph...")
        gremlin_client = create_gremlin_client(
            conn_info['endpoint'],
            database_name,
            graph_name,
            conn_info['key']
        )
        
        # Initialize graph
        initialize_graph_schema(gremlin_client)
        
        # Verify graph
        verify_graph(gremlin_client)
        
        # Close the client connection
        gremlin_client.close()
        
        print("\n" + "=" * 80)
        print("✅ Graph Initialization Complete!")
        print("=" * 80)
        print("\nNext Steps:")
        print("  1. Run: python scripts/setup_search_index.py")
        print("  2. Run: python scripts/setup_search_indexer.py  # Auto-sync from Cosmos DB")
        print("  3. Test queries with: python src/query_graphrag.py")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
