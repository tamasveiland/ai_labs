"""
Configuration settings for GraphRAG infrastructure deployment.
"""
import os
from typing import Optional

class Config:
    """Configuration class for infrastructure deployment."""
    
    def __init__(self):
        # Azure subscription and resource group
        self.subscription_id: Optional[str] = os.getenv('AZURE_SUBSCRIPTION_ID')
        self.resource_group_name: str = os.getenv('RESOURCE_GROUP_NAME', 'rg-graphrag-lab')
        self.location: str = os.getenv('AZURE_LOCATION', 'eastus')
        
        # Resource naming
        self.project_name: str = os.getenv('PROJECT_NAME', 'graphrag')
        self.environment: str = os.getenv('ENVIRONMENT', 'dev')
        
        # Cosmos DB Gremlin settings
        self.cosmos_account_name: str = os.getenv('COSMOS_ACCOUNT_NAME', 
                                                   f'cosmos-{self.project_name}-{self.environment}')
        self.cosmos_database_name: str = os.getenv('COSMOS_DATABASE_NAME', 'graphrag-db')
        self.cosmos_graph_name: str = os.getenv('COSMOS_GRAPH_NAME', 'knowledge-graph')
        self.cosmos_throughput: int = int(os.getenv('COSMOS_THROUGHPUT', '400'))
        
        # Azure AI Search settings
        self.search_service_name: str = os.getenv('SEARCH_SERVICE_NAME',
                                                   f'search-{self.project_name}-{self.environment}')
        self.search_sku: str = os.getenv('SEARCH_SKU', 'basic')
        self.search_index_name: str = os.getenv('SEARCH_INDEX_NAME', 'chunks-index')
        
        # Azure OpenAI settings
        self.openai_account_name: str = os.getenv('OPENAI_ACCOUNT_NAME',
                                                   f'oai-{self.project_name}-{self.environment}')
        self.openai_sku: str = os.getenv('OPENAI_SKU', 'S0')
        self.embedding_deployment_name: str = os.getenv('EMBEDDING_DEPLOYMENT_NAME', 
                                                        'text-embedding-3-large')
        self.embedding_model_name: str = os.getenv('EMBEDDING_MODEL_NAME',
                                                    'text-embedding-3-large')
        self.embedding_model_version: str = os.getenv('EMBEDDING_MODEL_VERSION', '1')
        
        # Storage settings
        self.storage_account_name: str = os.getenv('STORAGE_ACCOUNT_NAME',
                                                    f'st{self.project_name}{self.environment}')
        self.storage_container_name: str = os.getenv('STORAGE_CONTAINER_NAME', 'documents')
        
        # Tags
        self.tags = {
            'Environment': self.environment,
            'Project': self.project_name,
            'Purpose': 'GraphRAG Lab',
            'ManagedBy': 'Python'
        }
    
    def validate(self) -> bool:
        """Validate required configuration."""
        if not self.subscription_id:
            raise ValueError("AZURE_SUBSCRIPTION_ID environment variable is required")
        return True
    
    def display(self):
        """Display configuration settings."""
        print("=" * 80)
        print("GraphRAG Infrastructure Configuration")
        print("=" * 80)
        print(f"Subscription ID:        {self.subscription_id}")
        print(f"Resource Group:         {self.resource_group_name}")
        print(f"Location:              {self.location}")
        print(f"Environment:           {self.environment}")
        print()
        print(f"Cosmos DB Account:     {self.cosmos_account_name}")
        print(f"Cosmos Database:       {self.cosmos_database_name}")
        print(f"Cosmos Graph:          {self.cosmos_graph_name}")
        print()
        print(f"Search Service:        {self.search_service_name}")
        print(f"Search Index:          {self.search_index_name}")
        print()
        print(f"OpenAI Account:        {self.openai_account_name}")
        print(f"Embedding Deployment:  {self.embedding_deployment_name}")
        print()
        print(f"Storage Account:       {self.storage_account_name}")
        print(f"Storage Container:     {self.storage_container_name}")
        print("=" * 80)
