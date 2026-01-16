"""
Configuration module for the RAG application
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class AzureConfig:
    """Azure service configuration"""
    subscription_id: Optional[str] = None
    resource_group: Optional[str] = None
    location: str = "eastus"


@dataclass
class OpenAIConfig:
    """Azure OpenAI configuration"""
    endpoint: str
    deployment_name: str
    api_version: str = "2024-08-01-preview"
    api_key: Optional[str] = None


@dataclass
class SearchConfig:
    """Azure AI Search configuration"""
    endpoint: str
    index_name: str = "documents-index"
    api_key: Optional[str] = None


@dataclass
class AppConfig:
    """Application configuration"""
    azure: AzureConfig
    openai: OpenAIConfig
    search: SearchConfig
    use_managed_identity: bool = True
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Load configuration from environment variables"""
        return cls(
            azure=AzureConfig(
                subscription_id=os.getenv("AZURE_SUBSCRIPTION_ID"),
                resource_group=os.getenv("AZURE_RESOURCE_GROUP"),
                location=os.getenv("AZURE_LOCATION", "eastus")
            ),
            openai=OpenAIConfig(
                endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
                api_key=os.getenv("AZURE_OPENAI_API_KEY")
            ),
            search=SearchConfig(
                endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
                index_name=os.getenv("AZURE_SEARCH_INDEX", "documents-index"),
                api_key=os.getenv("AZURE_SEARCH_API_KEY")
            ),
            use_managed_identity=os.getenv("USE_MANAGED_IDENTITY", "true").lower() == "true"
        )
