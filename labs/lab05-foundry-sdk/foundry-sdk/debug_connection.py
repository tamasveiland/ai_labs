#!/usr/bin/env python3
import os
import asyncio
from dotenv import load_dotenv
from azure.identity.aio import ClientSecretCredential, DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
import traceback

load_dotenv()

async def debug_openai_connection():
    """Debug version to figure out the 404 issue."""
    
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
    
    print("🔍 Azure Foundry OpenAI Debug Session")
    print("=" * 50)
    
    async with AIProjectClient(
        endpoint=endpoint,
        credential=credential,
        api_version="2025-11-15-preview"
    ) as project_client:
        
        print("✅ Project client created")
        
        # Get deployments with full details
        deployments = project_client.deployments.list()
        async for deployment in deployments:
            print(f"\n📋 Deployment Details:")
            print(f"   Name: {deployment.name}")
            print(f"   Model Name: {deployment.model_name}")
            print(f"   Model Version: {deployment.model_version}") 
            print(f"   Model Publisher: {deployment.model_publisher}")
            print(f"   SKU: {deployment.sku}")
            print(f"   Type: {deployment.type}")
            print(f"   Connection: {deployment.connection_name}")
            print(f"   Capabilities: {deployment.capabilities}")
        
        # Try getting OpenAI connection info
        try:
            openai_client = project_client.get_openai_client()
            print(f"\n✅ OpenAI client type: {type(openai_client)}")
            
            # Check if this is an async vs sync issue
            async with openai_client as client:
                print(f"✅ Async OpenAI client ready")
                
                # Try a very basic call with detailed error handling
                try:
                    print(f"\n🧪 Testing with deployment name: 'gpt-4o'")
                    
                    response = await client.chat.completions.create(
                        model="gpt-4o",  # Exact deployment name
                        messages=[{"role": "user", "content": "Hi"}],
                        max_tokens=10
                    )
                    print(f"✅ SUCCESS! Response: {response.choices[0].message.content}")
                    
                except Exception as e:
                    print(f"❌ Detailed Error Info:")
                    print(f"   Type: {type(e).__name__}")
                    print(f"   Message: {str(e)}")
                    
                    # Check for specific Azure/OpenAI error types
                    if hasattr(e, 'status_code'):
                        print(f"   Status Code: {e.status_code}")
                    if hasattr(e, 'response'):
                        print(f"   Response: {e.response}")
                    if hasattr(e, 'request'):
                        print(f"   Request URL: {getattr(e.request, 'url', 'N/A')}")
                        
                    print(f"\nFull traceback:")
                    traceback.print_exc()
                
        except Exception as e:
            print(f"❌ Failed to get OpenAI client: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_openai_connection())