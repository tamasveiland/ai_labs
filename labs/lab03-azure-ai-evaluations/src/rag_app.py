"""
Simple RAG Application for Azure AI Evaluations Lab
Demonstrates integration with Azure OpenAI and Azure AI Search
"""
import os
from typing import Dict, List, Optional
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from openai import AzureOpenAI


class RAGApplication:
    """
    Retrieval-Augmented Generation application using Azure OpenAI and Azure AI Search.
    """
    
    def __init__(
        self,
        openai_endpoint: str,
        openai_deployment: str,
        search_endpoint: str,
        search_index: str,
        use_api_key: bool = False
    ):
        """
        Initialize the RAG application.
        
        Args:
            openai_endpoint: Azure OpenAI endpoint URL
            openai_deployment: OpenAI deployment name
            search_endpoint: Azure AI Search endpoint URL
            search_index: Search index name
            use_api_key: Whether to use API key authentication (default: managed identity)
        """
        self.deployment = openai_deployment
        
        # Initialize Azure OpenAI client
        if use_api_key:
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            self.openai_client = AzureOpenAI(
                api_key=api_key,
                api_version="2024-08-01-preview",
                azure_endpoint=openai_endpoint
            )
        else:
            credential = DefaultAzureCredential()
            self.openai_client = AzureOpenAI(
                azure_ad_token_provider=lambda: credential.get_token(
                    "https://cognitiveservices.azure.com/.default"
                ).token,
                api_version="2024-08-01-preview",
                azure_endpoint=openai_endpoint
            )
        
        # Initialize Search client
        if use_api_key:
            from azure.core.credentials import AzureKeyCredential
            search_key = os.getenv("AZURE_SEARCH_API_KEY")
            search_credential = AzureKeyCredential(search_key)
        else:
            search_credential = DefaultAzureCredential()
            
        self.search_client = SearchClient(
            endpoint=search_endpoint,
            index_name=search_index,
            credential=search_credential
        )
    
    def retrieve_documents(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Retrieve relevant documents from Azure AI Search.
        
        Args:
            query: User query
            top_k: Number of documents to retrieve
            
        Returns:
            List of retrieved documents with content and metadata
        """
        try:
            results = self.search_client.search(
                search_text=query,
                top=top_k,
                select=["content", "title", "url"]
            )
            
            documents = []
            for result in results:
                documents.append({
                    "content": result.get("content", ""),
                    "title": result.get("title", "Untitled"),
                    "url": result.get("url", ""),
                    "score": result.get("@search.score", 0.0)
                })
            
            return documents
        except Exception as e:
            print(f"Error retrieving documents: {e}")
            return []
    
    def generate_response(
        self,
        query: str,
        context_documents: List[Dict],
        temperature: float = 0.7
    ) -> str:
        """
        Generate response using Azure OpenAI with retrieved context.
        
        Args:
            query: User query
            context_documents: Retrieved documents for context
            temperature: Sampling temperature for generation
            
        Returns:
            Generated response
        """
        # Build context from retrieved documents
        context = "\n\n".join([
            f"Document {i+1} ({doc['title']}):\n{doc['content']}"
            for i, doc in enumerate(context_documents)
        ])
        
        # Create system message with context
        system_message = f"""You are a helpful AI assistant. Answer the user's question based on the following context.
If the answer cannot be found in the context, say so clearly.
Always cite which document(s) you used to answer the question.

Context:
{context}
"""
        
        # Generate response
        try:
            response = self.openai_client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": query}
                ],
                temperature=temperature,
                max_tokens=800
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating response: {e}"
    
    def query(self, user_query: str, top_k: int = 3) -> Dict:
        """
        Main query method - retrieves documents and generates response.
        
        Args:
            user_query: User's question
            top_k: Number of documents to retrieve
            
        Returns:
            Dictionary with query, response, context, and citations
        """
        # Retrieve relevant documents
        documents = self.retrieve_documents(user_query, top_k=top_k)
        
        # Generate response with context
        response = self.generate_response(user_query, documents)
        
        # Format context for evaluation
        context = "\n\n".join([
            f"{doc['title']}: {doc['content']}"
            for doc in documents
        ])
        
        # Extract citations
        citations = [
            {
                "title": doc["title"],
                "url": doc["url"],
                "score": doc["score"]
            }
            for doc in documents
        ]
        
        return {
            "query": user_query,
            "response": response,
            "context": context,
            "citations": citations,
            "num_documents_retrieved": len(documents)
        }


def main():
    """Example usage of the RAG application."""
    from dotenv import load_dotenv
    load_dotenv()
    
    # Initialize RAG application
    app = RAGApplication(
        openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        openai_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
        search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        search_index=os.getenv("AZURE_SEARCH_INDEX", "documents-index"),
        use_api_key=False  # Use managed identity
    )
    
    # Example query
    result = app.query("What is Azure AI Foundry?")
    
    print(f"Query: {result['query']}")
    print(f"\nResponse: {result['response']}")
    print(f"\nCitations: {result['citations']}")
    print(f"\nDocuments Retrieved: {result['num_documents_retrieved']}")


if __name__ == "__main__":
    main()
