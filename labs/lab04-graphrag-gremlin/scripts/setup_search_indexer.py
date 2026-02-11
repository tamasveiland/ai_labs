#!/usr/bin/env python3
"""
Set up Azure AI Search indexer for Cosmos DB Gremlin.

This script creates a data source, skillset, and indexer to automatically
pull chunk data from Cosmos DB Gremlin graph and index it in Azure AI Search
with vector embeddings.
"""

import os
import sys
import json
import time
import requests
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from azure.mgmt.search import SearchManagementClient
from azure.mgmt.cosmosdb import CosmosDBManagementClient
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.authorization.models import RoleAssignmentCreateParameters
import uuid
from dotenv import load_dotenv as loadenv


def get_search_admin_key(subscription_id: str, resource_group: str, service_name: str) -> str:
    """Get the admin key for Azure AI Search."""
    credential = DefaultAzureCredential()
    search_mgmt_client = SearchManagementClient(credential, subscription_id)
    admin_keys = search_mgmt_client.admin_keys.get(resource_group, service_name)
    return admin_keys.primary_key


def get_cosmos_connection_string(subscription_id: str, resource_group: str, account_name: str) -> str:
    """Get Cosmos DB connection string for Search indexer."""
    credential = DefaultAzureCredential()
    cosmos_client = CosmosDBManagementClient(credential, subscription_id)
    
    # Get connection strings
    conn_strings = cosmos_client.database_accounts.list_connection_strings(
        resource_group, account_name
    )
    
    # Get the primary connection string (SQL API endpoint for indexing)
    for conn in conn_strings.connection_strings:
        if "AccountEndpoint" in conn.connection_string:
            return conn.connection_string
    
    # Fallback: construct from keys
    keys = cosmos_client.database_accounts.list_keys(resource_group, account_name)
    account = cosmos_client.database_accounts.get(resource_group, account_name)
    
    return f"AccountEndpoint={account.document_endpoint};AccountKey={keys.primary_master_key};"


def get_openai_config(subscription_id: str, resource_group: str, account_name: str) -> dict:
    """Get Azure OpenAI endpoint and resource ID."""
    credential = DefaultAzureCredential()
    cognitive_client = CognitiveServicesManagementClient(credential, subscription_id)
    account = cognitive_client.accounts.get(resource_group, account_name)
    return {
        "endpoint": account.properties.endpoint,
        "resource_id": account.id
    }


def get_search_service_identity(subscription_id: str, resource_group: str, service_name: str) -> str:
    """Get the Search service's managed identity principal ID."""
    credential = DefaultAzureCredential()
    search_mgmt_client = SearchManagementClient(credential, subscription_id)
    search_service = search_mgmt_client.services.get(resource_group, service_name)
    
    if search_service.identity and search_service.identity.principal_id:
        return search_service.identity.principal_id
    else:
        raise ValueError(f"Search service '{service_name}' does not have a managed identity enabled. "
                        "Please enable system-assigned managed identity in the Azure Portal.")


def assign_cognitive_services_role(
    subscription_id: str,
    openai_resource_id: str,
    search_principal_id: str
) -> bool:
    """Assign 'Cognitive Services OpenAI User' role to Search service managed identity."""
    
    print(f"\n🔐 Assigning 'Cognitive Services OpenAI User' role to Search service...")
    
    credential = DefaultAzureCredential()
    auth_client = AuthorizationManagementClient(credential, subscription_id)
    
    # Cognitive Services OpenAI User role definition ID
    # This is a well-known GUID for this role
    role_definition_id = f"/subscriptions/{subscription_id}/providers/Microsoft.Authorization/roleDefinitions/5e0bd9bd-7b93-4f28-af87-19fc36ad61bd"
    
    # Check if role assignment already exists
    existing_assignments = auth_client.role_assignments.list_for_scope(
        scope=openai_resource_id,
        filter=f"principalId eq '{search_principal_id}'"
    )
    
    for assignment in existing_assignments:
        if assignment.role_definition_id.endswith("5e0bd9bd-7b93-4f28-af87-19fc36ad61bd"):
            print(f"✓ Role assignment already exists")
            return True
    
    # Create new role assignment
    role_assignment_name = str(uuid.uuid4())
    
    try:
        auth_client.role_assignments.create(
            scope=openai_resource_id,
            role_assignment_name=role_assignment_name,
            parameters=RoleAssignmentCreateParameters(
                role_definition_id=role_definition_id,
                principal_id=search_principal_id,
                principal_type="ServicePrincipal"
            )
        )
        print(f"✓ Role assignment created successfully")
        print(f"  Waiting 30 seconds for role assignment to propagate...")
        time.sleep(30)  # Wait for role assignment to propagate
        return True
    except Exception as e:
        if "RoleAssignmentExists" in str(e):
            print(f"✓ Role assignment already exists")
            return True
        print(f"❌ Failed to create role assignment: {e}")
        return False


def create_data_source(
    search_endpoint: str,
    admin_key: str,
    data_source_name: str,
    cosmos_connection_string: str,
    database_name: str,
    collection_name: str
):
    """Create Cosmos DB Gremlin data source for Azure AI Search."""
    
    print(f"\n📊 Creating data source: {data_source_name}")
    
    # For Cosmos DB Gremlin, we use the SQL API to access vertex data
    # The query selects only 'chunk' vertices with required properties
    # Note: @HighWaterMark is required when using change detection with custom query
    # Note: _ts must be in SELECT clause for change detection to work
    # Note: Gremlin stores properties as arrays, use [0]._value to extract scalar values
    data_source_definition = {
        "name": data_source_name,
        "type": "cosmosdb",
        "credentials": {
            "connectionString": cosmos_connection_string
        },
        "container": {
            "name": collection_name,
            "query": "SELECT c.id, c.position[0]._value AS position, c.text[0]._value AS text, c.docId[0]._value AS documentId, c.tenant[0]._value AS tenant, c._ts FROM c WHERE c.label = 'chunk' AND c._ts > @HighWaterMark ORDER BY c._ts"
        },
        "dataChangeDetectionPolicy": {
            "@odata.type": "#Microsoft.Azure.Search.HighWaterMarkChangeDetectionPolicy",
            "highWaterMarkColumnName": "_ts"
        }
    }
    
    # Add database account in connection string
    if "Database=" not in cosmos_connection_string:
        data_source_definition["credentials"]["connectionString"] = (
            f"{cosmos_connection_string}Database={database_name};"
        )
    
    url = f"{search_endpoint}/datasources/{data_source_name}?api-version=2024-07-01"
    headers = {
        "Content-Type": "application/json",
        "api-key": admin_key
    }
    
    response = requests.put(url, headers=headers, json=data_source_definition)
    
    if response.status_code in [200, 201]:
        print(f"✓ Data source created: {data_source_name}")
        return True
    else:
        print(f"❌ Failed to create data source: {response.status_code}")
        print(f"   Error: {response.text}")
        return False


def create_skillset(
    search_endpoint: str,
    admin_key: str,
    skillset_name: str,
    openai_endpoint: str,
    embedding_deployment: str
):
    """Create skillset with Azure OpenAI embedding skill using managed identity."""
    
    print(f"\n🧠 Creating skillset: {skillset_name}")
    
    skillset_definition = {
        "name": skillset_name,
        "description": "Skillset for generating embeddings from chunk text using managed identity",
        "skills": [
            {
                "@odata.type": "#Microsoft.Skills.Text.AzureOpenAIEmbeddingSkill",
                "name": "generate-embeddings",
                "description": "Generate embeddings using Azure OpenAI with managed identity",
                "context": "/document",
                "resourceUri": openai_endpoint.rstrip('/'),
                "deploymentId": embedding_deployment,
                "modelName": embedding_deployment,
                "dimensions": 3072,
                "inputs": [
                    {
                        "name": "text",
                        "source": "/document/text"
                    }
                ],
                "outputs": [
                    {
                        "name": "embedding",
                        "targetName": "embedding"
                    }
                ]
            }
        ]
    }
    
    url = f"{search_endpoint}/skillsets/{skillset_name}?api-version=2024-07-01"
    headers = {
        "Content-Type": "application/json",
        "api-key": admin_key
    }
    
    response = requests.put(url, headers=headers, json=skillset_definition)
    
    if response.status_code in [200, 201]:
        print(f"✓ Skillset created: {skillset_name}")
        return True
    else:
        print(f"❌ Failed to create skillset: {response.status_code}")
        print(f"   Error: {response.text}")
        return False


def create_indexer(
    search_endpoint: str,
    admin_key: str,
    indexer_name: str,
    data_source_name: str,
    index_name: str,
    skillset_name: str
):
    """Create indexer to pull from Cosmos DB and index to search."""
    
    print(f"\n🔄 Creating indexer: {indexer_name}")
    
    indexer_definition = {
        "name": indexer_name,
        "description": "Indexer for Cosmos DB Gremlin chunk data",
        "dataSourceName": data_source_name,
        "targetIndexName": index_name,
        "skillsetName": skillset_name,
        "schedule": {
            "interval": "PT1H",  # Run every hour
            "startTime": "2024-01-01T00:00:00Z"
        },
        "parameters": {
            "batchSize": 100,
            "maxFailedItems": 10,
            "maxFailedItemsPerBatch": 5
        },
        "fieldMappings": [
            {
                "sourceFieldName": "id",
                "targetFieldName": "chunkId"
            }
        ],
        "outputFieldMappings": [
            {
                "sourceFieldName": "/document/embedding",
                "targetFieldName": "embedding"
            }
        ]
    }
    
    url = f"{search_endpoint}/indexers/{indexer_name}?api-version=2024-07-01"
    headers = {
        "Content-Type": "application/json",
        "api-key": admin_key
    }
    
    response = requests.put(url, headers=headers, json=indexer_definition)
    
    if response.status_code in [200, 201]:
        print(f"✓ Indexer created: {indexer_name}")
        return True
    else:
        print(f"❌ Failed to create indexer: {response.status_code}")
        print(f"   Error: {response.text}")
        return False


def run_indexer(search_endpoint: str, admin_key: str, indexer_name: str):
    """Trigger indexer run."""
    
    print(f"\n▶️  Running indexer: {indexer_name}")
    
    url = f"{search_endpoint}/indexers/{indexer_name}/run?api-version=2024-07-01"
    headers = {
        "Content-Type": "application/json",
        "api-key": admin_key
    }
    
    response = requests.post(url, headers=headers)
    
    if response.status_code in [202, 204]:
        print(f"✓ Indexer started successfully")
        return True
    else:
        print(f"❌ Failed to start indexer: {response.status_code}")
        print(f"   Error: {response.text}")
        return False


def get_indexer_status(search_endpoint: str, admin_key: str, indexer_name: str):
    """Get indexer status."""
    
    url = f"{search_endpoint}/indexers/{indexer_name}/status?api-version=2024-07-01"
    headers = {
        "Content-Type": "application/json",
        "api-key": admin_key
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        status = response.json()
        return status
    else:
        return None


def main():
    """Main function."""
    print("\n" + "=" * 80)
    print("GraphRAG - Setup Azure AI Search Indexer")
    print("=" * 80)

    loadenv()  # Load environment variables from .env file if present
    
    # Get configuration from environment
    subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
    resource_group = os.getenv('RESOURCE_GROUP_NAME', 'rg-graphrag-lab')
    search_service_name = os.getenv('SEARCH_SERVICE_NAME', 'search-graphrag-dev')
    index_name = os.getenv('SEARCH_INDEX_NAME', 'chunks-index')
    cosmos_account_name = os.getenv('COSMOS_ACCOUNT_NAME', 'cosmos-graphrag-dev')
    cosmos_database_name = os.getenv('COSMOS_DATABASE_NAME', 'graphrag-db')
    cosmos_graph_name = os.getenv('COSMOS_GRAPH_NAME', 'knowledge-graph')
    openai_account_name = os.getenv('OPENAI_ACCOUNT_NAME', 'oai-graphrag-dev')
    embedding_deployment = os.getenv('EMBEDDING_DEPLOYMENT_NAME', 'text-embedding-3-large')
    
    # Indexer resource names
    data_source_name = os.getenv('SEARCH_DATA_SOURCE_NAME', 'cosmosdb-gremlin-chunks')
    skillset_name = os.getenv('SEARCH_SKILLSET_NAME', 'chunks-embedding-skillset')
    indexer_name = os.getenv('SEARCH_INDEXER_NAME', 'chunks-indexer')
    
    if not subscription_id:
        print("\n❌ Error: AZURE_SUBSCRIPTION_ID environment variable not set")
        print("Please run: export AZURE_SUBSCRIPTION_ID='your-subscription-id'")
        sys.exit(1)
    
    print(f"\nConfiguration:")
    print(f"  Subscription:           {subscription_id}")
    print(f"  Resource Group:         {resource_group}")
    print(f"  Search Service:         {search_service_name}")
    print(f"  Index Name:             {index_name}")
    print(f"  Cosmos Account:         {cosmos_account_name}")
    print(f"  Cosmos Database:        {cosmos_database_name}")
    print(f"  Cosmos Graph:           {cosmos_graph_name}")
    print(f"  OpenAI Account:         {openai_account_name}")
    print(f"  Embedding Deployment:   {embedding_deployment}")
    print(f"  Data Source Name:       {data_source_name}")
    print(f"  Skillset Name:          {skillset_name}")
    print(f"  Indexer Name:           {indexer_name}")
    
    try:
        # Get credentials
        print("\n🔐 Getting credentials...")
        search_key = get_search_admin_key(subscription_id, resource_group, search_service_name)
        cosmos_conn_string = get_cosmos_connection_string(subscription_id, resource_group, cosmos_account_name)
        openai_config = get_openai_config(subscription_id, resource_group, openai_account_name)
        
        # Get Search service managed identity for RBAC
        search_principal_id = get_search_service_identity(subscription_id, resource_group, search_service_name)
        print(f"✓ Search service principal ID: {search_principal_id}")
        
        search_endpoint = f"https://{search_service_name}.search.windows.net"
        
        print(f"✓ Search endpoint: {search_endpoint}")
        print(f"✓ OpenAI endpoint: {openai_config['endpoint']}")
        
        # Assign Cognitive Services OpenAI User role to Search service
        if not assign_cognitive_services_role(
            subscription_id,
            openai_config['resource_id'],
            search_principal_id
        ):
            print("⚠️  Warning: Could not assign role. Skillset may fail if role is not already assigned.")
        
        # Create data source
        if not create_data_source(
            search_endpoint,
            search_key,
            data_source_name,
            cosmos_conn_string,
            cosmos_database_name,
            cosmos_graph_name
        ):
            sys.exit(1)
        
        # Create skillset (uses managed identity - no API key needed)
        if not create_skillset(
            search_endpoint,
            search_key,
            skillset_name,
            openai_config['endpoint'],
            embedding_deployment
        ):
            sys.exit(1)
        
        # Create indexer
        if not create_indexer(
            search_endpoint,
            search_key,
            indexer_name,
            data_source_name,
            index_name,
            skillset_name
        ):
            sys.exit(1)
        
        # Run indexer
        run_indexer(search_endpoint, search_key, indexer_name)
        
        print("\n" + "=" * 80)
        print("✅ Indexer Setup Complete!")
        print("=" * 80)
        print("\nCreated Resources:")
        print(f"  Data Source: {data_source_name}")
        print(f"  Skillset:    {skillset_name}")
        print(f"  Indexer:     {indexer_name}")
        print("\nThe indexer will automatically:")
        print("  1. Pull chunk vertices from Cosmos DB Gremlin")
        print("  2. Generate embeddings using Azure OpenAI")
        print("  3. Index documents to the search index")
        print("\nSchedule: Runs every hour (PT1H)")
        print("\nTo check indexer status:")
        print(f"  python -c \"import requests; print(requests.get('{search_endpoint}/indexers/{indexer_name}/status?api-version=2024-07-01', headers={{'api-key': '{search_key[:8]}...'}}).json())\"")
        print("\nOr view in Azure Portal:")
        print(f"  https://portal.azure.com/#@/resource/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Search/searchServices/{search_service_name}/indexers")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
