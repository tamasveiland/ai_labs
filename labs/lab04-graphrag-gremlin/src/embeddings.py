"""
Embeddings module for Azure OpenAI.

This module provides functions for generating embeddings using Azure OpenAI.
"""

from typing import List
from openai import AzureOpenAI


class EmbeddingsClient:
    """Handle Azure OpenAI embeddings."""
    
    def __init__(self, endpoint: str, api_key: str, deployment_name: str, api_version: str = "2024-02-01"):
        """Initialize OpenAI client."""
        self.client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint
        )
        self.deployment_name = deployment_name
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        response = self.client.embeddings.create(
            input=text,
            model=self.deployment_name
        )
        return response.data[0].embedding
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        response = self.client.embeddings.create(
            input=texts,
            model=self.deployment_name
        )
        return [item.embedding for item in response.data]
