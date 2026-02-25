#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from openai import AzureOpenAI

load_dotenv()

def test_direct_azure_openai():
    """Test direct connection to Azure OpenAI (bypass Foundry)"""
    
    # Create credential
    try:
        credential = ClientSecretCredential(
            tenant_id=os.environ.get("AZURE_TENANT_ID"),
            client_id=os.environ.get("AZURE_CLIENT_ID"),
            client_secret=os.environ.get("AZURE_CLIENT_SECRET")
        )
    except:
        credential = DefaultAzureCredential()
    
    print("🔍 Testing Direct Azure OpenAI Connection")
    print("=" * 50)
    
    # Get token for Azure OpenAI
    token = credential.get_token("https://cognitiveservices.azure.com/.default")
    
    # Create direct Azure OpenAI client
    client = AzureOpenAI(
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
        azure_ad_token=token.token
    )
    
    print(f"✅ Direct Azure OpenAI client created")
    print(f"   Endpoint: {os.environ.get('AZURE_OPENAI_ENDPOINT')}")
    print(f"   API Version: {os.environ.get('AZURE_OPENAI_API_VERSION', '2024-08-01-preview')}")
    
    # Test the connection
    try:
        print(f"\n🧪 Testing with deployment: {os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o')}")
        
        response = client.chat.completions.create(
            model=os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
            messages=[
                {"role": "user", "content": "Hello! Please say hi back."}
            ],
            max_tokens=50
        )
        
        print(f"✅ SUCCESS with direct Azure OpenAI!")
        print(f"   Model: {response.model}")
        print(f"   Response: {response.choices[0].message.content}")
        print(f"\n💡 This confirms Azure OpenAI is working - the issue is with Foundry integration!")
        
    except Exception as e:
        print(f"❌ Direct Azure OpenAI Error: {e}")
        print(f"   Type: {type(e).__name__}")
        
        # Try different deployment names
        alt_deployments = ["gpt-4o-mini", "gpt-35-turbo", "gpt-4", "gpt-4-turbo"]
        print(f"\n🔄 Trying alternative deployment names...")
        
        for deployment in alt_deployments:
            try:
                print(f"   Testing: {deployment}")
                response = client.chat.completions.create(
                    model=deployment,
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=10
                )
                print(f"   ✅ SUCCESS with {deployment}!")
                break
            except Exception as alt_e:
                print(f"   ❌ {deployment}: {alt_e}")

def test_foundry_connection_status():
    """Check if there's a connection issue in Foundry"""
    from azure.ai.projects import AIProjectClient
    
    try:
        credential = ClientSecretCredential(
            tenant_id=os.environ.get("AZURE_TENANT_ID"),
            client_id=os.environ.get("AZURE_CLIENT_ID"),
            client_secret=os.environ.get("AZURE_CLIENT_SECRET")
        )
    except:
        credential = DefaultAzureCredential()
    
    print(f"\n🔍 Checking Foundry Project Configuration")
    print("=" * 50)
    
    with AIProjectClient(
        endpoint=os.environ.get("AZURE_AI_PROJECT_ENDPOINT"),
        credential=credential,
        api_version="2025-11-15-preview"
    ) as project_client:
        
        # Check connections
        try:
            connections = list(project_client.connections.list())
            print(f"📋 Found {len(connections)} connection(s) in Foundry project:")
            for conn in connections:
                print(f"   - {conn.name} ({conn.authentication})")
            
            if len(connections) == 0:
                print("❌ No connections found! This might be the issue.")
                print("   You may need to connect your Foundry project to Azure OpenAI.")
                
        except Exception as e:
            print(f"⚠️  Could not list connections: {e}")

if __name__ == "__main__":
    test_direct_azure_openai()
    test_foundry_connection_status()