#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from openai import AzureOpenAI
import asyncio

load_dotenv()

def create_azure_openai_client():
    """Create a working Azure OpenAI client (bypasses Foundry)"""
    
    # Create credential
    try:
        credential = ClientSecretCredential(
            tenant_id=os.environ.get("AZURE_TENANT_ID"),
            client_id=os.environ.get("AZURE_CLIENT_ID"),
            client_secret=os.environ.get("AZURE_CLIENT_SECRET")
        )
    except:
        credential = DefaultAzureCredential()
    
    # Get token for Azure OpenAI
    token = credential.get_token("https://cognitiveservices.azure.com/.default")
    
    # Create direct Azure OpenAI client
    client = AzureOpenAI(
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
        azure_ad_token=token.token
    )
    
    return client

def test_chat_completion():
    """Test chat completion with working Azure OpenAI client"""
    
    print("🤖 Azure OpenAI Direct Connection Demo")
    print("=" * 50)
    
    client = create_azure_openai_client()
    
    # Test conversation
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": "What are the benefits of using Azure AI services?"}
    ]
    
    try:
        response = client.chat.completions.create(
            model=os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
            messages=messages,
            max_tokens=200,
            temperature=0.7
        )
        
        print(f"✅ Model: {response.model}")
        print(f"📝 Response:")
        print(f"{response.choices[0].message.content}")
        
        return client
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_streaming_response():
    """Demonstrate streaming responses"""
    
    print(f"\n🔄 Streaming Response Demo")
    print("-" * 30)
    
    client = create_azure_openai_client()
    
    try:
        stream = client.chat.completions.create(
            model=os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
            messages=[
                {"role": "user", "content": "Tell me a short story about AI and creativity."}
            ],
            max_tokens=150,
            stream=True
        )
        
        print("📖 Story:")
        for chunk in stream:
            # Safely handle streaming chunks - some might be empty or have different structure
            if hasattr(chunk, 'choices') and chunk.choices:
                choice = chunk.choices[0]
                if hasattr(choice, 'delta') and hasattr(choice.delta, 'content'):
                    if choice.delta.content is not None:
                        print(choice.delta.content, end="")
        print("\n")
        
    except Exception as e:
        print(f"❌ Streaming error: {e}")

def test_multiple_requests():
    """Test multiple concurrent requests"""
    
    print(f"\n⚡ Multiple Requests Demo")
    print("-" * 30)
    
    client = create_azure_openai_client()
    
    prompts = [
        "Explain Python in one sentence.",
        "What is machine learning?", 
        "Benefits of cloud computing?"
    ]
    
    for i, prompt in enumerate(prompts, 1):
        try:
            response = client.chat.completions.create(
                model=os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50
            )
            
            print(f"{i}. {prompt}")
            print(f"   → {response.choices[0].message.content}")
            
        except Exception as e:
            print(f"{i}. ❌ Error: {e}")

if __name__ == "__main__":
    # Run all demos
    client = test_chat_completion()
    
    if client:  # Only continue if the first test worked
        test_streaming_response()
        
        print(f"\n✨ All demos completed successfully!")

    else:
        print(f"\n❌ Connection failed. Check your environment variables.")