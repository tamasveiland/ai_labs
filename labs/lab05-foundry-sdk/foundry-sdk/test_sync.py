#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from azure.ai.projects import AIProjectClient

load_dotenv()

def test_sync_connection():
    """Test with synchronous client instead of async"""
    
    endpoint = os.environ.get("AZURE_AI_PROJECT_ENDPOINT")
    
    # Create credential
    try:
        credential = ClientSecretCredential(
            tenant_id=os.environ.get("AZURE_TENANT_ID"),
            client_id=os.environ.get("AZURE_CLIENT_ID"),
            client_secret=os.environ.get("AZURE_CLIENT_SECRET")
        )
    except:
        credential = DefaultAzureCredential()
    
    print("🔍 Testing Synchronous Connection")
    print("=" * 40)
    
    # Use synchronous client
    with AIProjectClient(
        endpoint=endpoint,
        credential=credential,
        api_version="2025-11-15-preview"
    ) as project_client:
        
        print("✅ Sync project client created")
        
        # List deployments
        deployments = list(project_client.deployments.list())
        for deployment in deployments:
            print(f"📋 Deployment: {deployment.name} (model: {deployment.model_name})")
        
        # Try with sync OpenAI client
        try:
            with project_client.get_openai_client() as openai_client:
                print(f"✅ Sync OpenAI client: {type(openai_client)}")
                
                # Simple test call
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=10
                )
                
                print(f"✅ SUCCESS! Model: {response.model}")
                print(f"   Response: {response.choices[0].message.content}")
                
        except Exception as e:
            print(f"❌ Sync OpenAI Error: {e}")
            
            # Try directly with model deployment name
            try:
                print("🔄 Trying with different client configuration...")
                
                # Maybe the issue is with the model name - try without async context
                response = openai_client.chat.completions.create(
                    model=deployments[0].name,  # Use exact deployment name
                    messages=[{"role": "user", "content": "Test"}],
                    max_tokens=5
                )
                print(f"✅ SUCCESS with deployment name!")
                print(f"   Response: {response.choices[0].message.content}")
                
            except Exception as e2:
                print(f"❌ Still failed: {e2}")

if __name__ == "__main__":
    test_sync_connection()