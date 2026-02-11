#!/usr/bin/env python3
"""
Deploy Azure infrastructure for GraphRAG with Cosmos DB Gremlin and Azure AI Search.

This script creates:
- Azure Resource Group
- Cosmos DB account with Gremlin API
- Cosmos DB database and graph
- Azure AI Search service
- Azure OpenAI service with embedding deployment
- Azure Storage account with container
"""

import sys
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.cosmosdb import CosmosDBManagementClient
from azure.mgmt.cosmosdb.models import (
    DatabaseAccountCreateUpdateParameters,
    DatabaseAccountKind,
    Location,
    Capability,
    ConsistencyPolicy,
    DefaultConsistencyLevel,
    GremlinDatabaseCreateUpdateParameters,
    GremlinDatabaseResource,
    GremlinGraphCreateUpdateParameters,
    GremlinGraphResource,
    CreateUpdateOptions
)
from azure.mgmt.search import SearchManagementClient
from azure.mgmt.search.models import SearchService, Sku as SearchSku, Identity, IdentityType
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.mgmt.cognitiveservices.models import Account, Sku, AccountProperties, Deployment, DeploymentProperties, DeploymentModel
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.storage.models import (
    StorageAccountCreateParameters,
    Sku as StorageSku,
    Kind,
    BlobContainer
)
from config import Config
from dotenv import load_dotenv as loadenv

def create_resource_group(credential, config: Config):
    """Create Azure Resource Group."""
    print(f"\n[1/6] Creating Resource Group: {config.resource_group_name}")
    
    resource_client = ResourceManagementClient(credential, config.subscription_id)
    
    rg_result = resource_client.resource_groups.create_or_update(
        config.resource_group_name,
        {
            "location": config.location,
            "tags": config.tags
        }
    )
    
    print(f"✓ Resource Group created: {rg_result.name}")
    return rg_result

def create_cosmos_db_account(credential, config: Config):
    """Create Cosmos DB account with Gremlin API."""
    print(f"\n[2/6] Creating Cosmos DB Account: {config.cosmos_account_name}")
    
    cosmos_client = CosmosDBManagementClient(credential, config.subscription_id)
    
    # Create Cosmos DB account with Gremlin capability
    params = DatabaseAccountCreateUpdateParameters(
        location=config.location,
        locations=[Location(location_name=config.location, failover_priority=0)],
        kind=DatabaseAccountKind.GLOBAL_DOCUMENT_DB,
        capabilities=[Capability(name="EnableGremlin")],
        consistency_policy=ConsistencyPolicy(
            default_consistency_level=DefaultConsistencyLevel.SESSION
        ),
        enable_automatic_failover=False,
        enable_multiple_write_locations=False,
        tags=config.tags
    )
    
    print(f"  Creating Cosmos DB account (this may take 5-10 minutes)...")
    async_cosmosdb_create = cosmos_client.database_accounts.begin_create_or_update(
        config.resource_group_name,
        config.cosmos_account_name,
        params
    )
    
    cosmos_account = async_cosmosdb_create.result()
    print(f"✓ Cosmos DB account created: {cosmos_account.name}")
    
    return cosmos_account

def create_gremlin_database_and_graph(credential, config: Config):
    """Create Gremlin database and graph."""
    print(f"\n[3/6] Creating Gremlin Database and Graph")
    
    cosmos_client = CosmosDBManagementClient(credential, config.subscription_id)
    
    # Create Gremlin database
    print(f"  Creating database: {config.cosmos_database_name}")
    db_params = GremlinDatabaseCreateUpdateParameters(
        resource=GremlinDatabaseResource(id=config.cosmos_database_name),
        options=CreateUpdateOptions(throughput=config.cosmos_throughput)
    )
    
    async_db_create = cosmos_client.gremlin_resources.begin_create_update_gremlin_database(
        config.resource_group_name,
        config.cosmos_account_name,
        config.cosmos_database_name,
        db_params
    )
    
    gremlin_db = async_db_create.result()
    print(f"✓ Gremlin database created: {gremlin_db.name}")
    
    # Create Gremlin graph with partition key
    print(f"  Creating graph: {config.cosmos_graph_name}")
    graph_params = GremlinGraphCreateUpdateParameters(
        resource=GremlinGraphResource(
            id=config.cosmos_graph_name,
            partition_key={
                "paths": ["/tenant"],
                "kind": "Hash"
            }
        ),
        options=CreateUpdateOptions()
    )
    
    async_graph_create = cosmos_client.gremlin_resources.begin_create_update_gremlin_graph(
        config.resource_group_name,
        config.cosmos_account_name,
        config.cosmos_database_name,
        config.cosmos_graph_name,
        graph_params
    )
    
    gremlin_graph = async_graph_create.result()
    print(f"✓ Gremlin graph created: {gremlin_graph.name}")
    
    return gremlin_db, gremlin_graph

def create_search_service(credential, config: Config):
    """Create Azure AI Search service with system-assigned managed identity."""
    print(f"\n[4/6] Creating Azure AI Search Service: {config.search_service_name}")
    
    search_client = SearchManagementClient(credential, config.subscription_id)
    
    search_service = SearchService(
        location=config.location,
        sku=SearchSku(name=config.search_sku),
        replica_count=1,
        partition_count=1,
        identity=Identity(type=IdentityType.SYSTEM_ASSIGNED),
        tags=config.tags
    )
    
    print(f"  Creating search service with managed identity (this may take 3-5 minutes)...")
    async_search_create = search_client.services.begin_create_or_update(
        config.resource_group_name,
        config.search_service_name,
        search_service
    )
    
    search_result = async_search_create.result()
    print(f"✓ Search service created: {search_result.name}")
    if search_result.identity:
        print(f"  Managed Identity Principal ID: {search_result.identity.principal_id}")
    
    return search_result

def create_openai_service(credential, config: Config):
    """Create Azure OpenAI service with embedding deployment."""
    print(f"\n[5/6] Creating Azure OpenAI Service: {config.openai_account_name}")
    
    cognitive_client = CognitiveServicesManagementClient(credential, config.subscription_id)
    
    # Create OpenAI account
    account_params = Account(
        location=config.location,
        sku=Sku(name=config.openai_sku),
        kind="OpenAI",
        properties=AccountProperties(
            custom_sub_domain_name=config.openai_account_name
        ),
        tags=config.tags
    )
    
    print(f"  Creating OpenAI account...")
    async_account_create = cognitive_client.accounts.begin_create(
        config.resource_group_name,
        config.openai_account_name,
        account_params
    )
    
    openai_account = async_account_create.result()
    print(f"✓ OpenAI account created: {openai_account.name}")
    
    # Create embedding model deployment
    print(f"  Creating embedding deployment: {config.embedding_deployment_name}")
    deployment_params = Deployment(
        sku=Sku(name="Standard", capacity=10),
        properties=DeploymentProperties(
            model=DeploymentModel(
                format="OpenAI",
                name=config.embedding_model_name,
                version=config.embedding_model_version
            )
        )
    )
    
    try:
        async_deployment_create = cognitive_client.deployments.begin_create_or_update(
            config.resource_group_name,
            config.openai_account_name,
            config.embedding_deployment_name,
            deployment_params
        )
        
        deployment_result = async_deployment_create.result()
        print(f"✓ Embedding deployment created: {deployment_result.name}")
    except Exception as e:
        print(f"  Warning: Could not create deployment. You may need to create it manually.")
        print(f"  Error: {str(e)}")
    
    return openai_account

def create_storage_account(credential, config: Config):
    """Create Azure Storage account with container."""
    print(f"\n[6/6] Creating Storage Account: {config.storage_account_name}")
    
    storage_client = StorageManagementClient(credential, config.subscription_id)
    
    # Create storage account
    storage_params = StorageAccountCreateParameters(
        sku=StorageSku(name="Standard_LRS"),
        kind=Kind.STORAGE_V2,
        location=config.location,
        tags=config.tags,
        allow_blob_public_access=False,
        minimum_tls_version="TLS1_2"
    )
    
    print(f"  Creating storage account...")
    async_storage_create = storage_client.storage_accounts.begin_create(
        config.resource_group_name,
        config.storage_account_name,
        storage_params
    )
    
    storage_account = async_storage_create.result()
    print(f"✓ Storage account created: {storage_account.name}")
    
    # Create blob container
    print(f"  Creating blob container: {config.storage_container_name}")
    container = storage_client.blob_containers.create(
        config.resource_group_name,
        config.storage_account_name,
        config.storage_container_name,
        BlobContainer()
    )
    
    print(f"✓ Blob container created: {container.name}")
    
    return storage_account

def main():
    """Main deployment function."""
    print("\n" + "=" * 80)
    print("GraphRAG Infrastructure Deployment")
    print("=" * 80)
    
    loadenv()  # Load environment variables from .env file if present

    # Load configuration
    config = Config()
    config.display()
    
    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        print(f"\n❌ Configuration error: {e}")
        print("\nPlease set the AZURE_SUBSCRIPTION_ID environment variable.")
        print("Example: export AZURE_SUBSCRIPTION_ID='your-subscription-id'")
        sys.exit(1)
    
    # Get Azure credentials
    print("\n🔐 Authenticating with Azure...")
    try:
        credential = DefaultAzureCredential()
        # Test the credential
        from azure.mgmt.subscription import SubscriptionClient
        sub_client = SubscriptionClient(credential)
        subscription = sub_client.subscriptions.get(config.subscription_id)
        print(f"✓ Authenticated to subscription: {subscription.display_name}")
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        print("\nPlease run 'az login' to authenticate with Azure.")
        sys.exit(1)
    
    # Deploy resources
    try:
        # Create resource group
        create_resource_group(credential, config)
        
        # Create Cosmos DB account with Gremlin
        create_cosmos_db_account(credential, config)
        
        # Create Gremlin database and graph
        create_gremlin_database_and_graph(credential, config)
        
        # Create Azure AI Search
        create_search_service(credential, config)
        
        # Create Azure OpenAI
        create_openai_service(credential, config)
        
        # Create Storage Account
        create_storage_account(credential, config)
        
        # Summary
        print("\n" + "=" * 80)
        print("✅ Deployment Complete!")
        print("=" * 80)
        print("\nCreated Resources:")
        print(f"  Resource Group:     {config.resource_group_name}")
        print(f"  Cosmos DB:          {config.cosmos_account_name}")
        print(f"  Gremlin Database:   {config.cosmos_database_name}")
        print(f"  Gremlin Graph:      {config.cosmos_graph_name}")
        print(f"  Search Service:     {config.search_service_name}")
        print(f"  OpenAI Service:     {config.openai_account_name}")
        print(f"  Storage Account:    {config.storage_account_name}")
        print("\nNext Steps:")
        print("  1. Run: python scripts/initialize_graph.py")
        print("  2. Run: python scripts/setup_search_index.py")
        print("  3. Run: python scripts/load_sample_data.py")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
