# pylint: disable=line-too-long,useless-suppression
# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

"""
DESCRIPTION:
    This script demonstrates how to connect to an Azure OpenAI model deployed in 
    Microsoft Foundry using the Microsoft Agent Framework.

USAGE:
    python azure_foundry_openai_connection.py

    Before running the script:

    pip install -r requirements.txt

    Set your environment variables by copying .env.example to .env and updating the values:
    1) AZURE_AI_PROJECT_ENDPOINT - Required. The Azure AI Project endpoint, as found in the overview page of your
       Microsoft Foundry project. It has the form: https://<account_name>.services.ai.azure.com/api/projects/<project_name>.
    2) AZURE_AI_MODEL_DEPLOYMENT_NAME - Optional. The name of the model deployment to use (e.g., gpt-4o-mini).
"""

import os
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.aio import AIProjectClient

from azure.ai.agents import AgentsClient

import asyncio

import traceback
from azure.core.exceptions import AzureError, HttpResponseError

# Load environment variables
load_dotenv()


async def test_openai_connection(endpoint: str, credential, model_deployment: str = None):
    """
    Test connection to Azure OpenAI through Foundry project.
    
    Args:
        endpoint (str): The Azure AI Project endpoint
        credential: Azure credential object
        model_deployment (str, optional): Name of the model deployment
    """
    
    try:
        # Create AI Project client
        async with AIProjectClient(
            endpoint=endpoint, 
            credential=credential, 
            api_version="2025-11-15-preview"
        ) as project_client:
            
            print("✅ Successfully created AI Project client")

            # List available deployments to debug the 404 issue
            try:
                print("📋 Checking available deployments...")
                deployments = project_client.deployments.list()
                deployment_list = []
                async for deployment in deployments:
                    deployment_list.append(deployment)
                
                print(f"✅ Found {len(deployment_list)} deployment(s):")
                for deployment in deployment_list:
                    # Debug: print all attributes to see what's available
                    print(f"   - Name: {deployment.name}")
                    print(f"     Attributes: {[attr for attr in dir(deployment) if not attr.startswith('_')]}")
                    
                    # Try different ways to get model info
                    if hasattr(deployment, 'model_name'):
                        print(f"     Model: {deployment.model_name}")
                    elif hasattr(deployment, 'sku'):
                        print(f"     SKU: {deployment.sku}")
                    elif hasattr(deployment, 'properties'):
                        print(f"     Properties: {deployment.properties}")
                    else:
                        print(f"     Type: {type(deployment)}")
                
                # Use the first deployment name as the model to test
                if deployment_list:
                    actual_model_name = deployment_list[0].name
                    print(f"\n💡 Trying with actual deployment name: {actual_model_name}")
                    model_deployment = actual_model_name
                
                if len(deployment_list) == 0:
                    print("❌ No deployments found in this project!")
                    print("   Please deploy a model in the Foundry portal first.")
                    return
                    
            except Exception as e:
                print(f"⚠️  Could not list deployments: {str(e)}")
                import traceback
                traceback.print_exc()
            
            # Get OpenAI client from the project
            async with project_client.get_openai_client() as openai_client:
                print("✅ Successfully obtained OpenAI client")
                
                # Test a simple completion
                test_prompt = "Hello! Please respond with a brief greeting."
                
                try:
                    if model_deployment:
                        response = await openai_client.chat.completions.create(
                            model=model_deployment,
                            messages=[
                                {"role": "system", "content": "You are a helpful assistant."},
                                {"role": "user", "content": test_prompt}
                            ],
                            max_tokens=100
                        )
                    else:
                        # If no specific deployment, try with default
                        response = await openai_client.chat.completions.create(
                            model="gpt-4o-mini",  # Default fallback
                            messages=[
                                {"role": "system", "content": "You are a helpful assistant."},
                                {"role": "user", "content": test_prompt}
                            ],
                            max_tokens=100
                        )
                    
                    print("✅ Successfully received response from OpenAI:")
                    print(f"   Model: {response.model}")
                    print(f"   Response: {response.choices[0].message.content}")
                
                except HttpResponseError as e:
                    print(f"HTTP Error: {e.status_code}")
                    print(f"Error Code: {e.error.code if e.error else 'N/A'}")
                    print(f"Error Message: {e.error.message if e.error else str(e)}")
                    print(f"Response: {e.response.text() if hasattr(e, 'response') else 'N/A'}")
                    traceback.print_exc()
                    
                except AzureError as e:
                    print(f"Azure Error: {type(e).__name__}")
                    print(f"Message: {str(e)}")
                    if hasattr(e, 'inner_exception') and e.inner_exception:
                        print(f"Inner Exception: {e.inner_exception}")
                    traceback.print_exc()
                    
                except Exception as e:
                    print(f"Unexpected Error: {type(e).__name__}")
                    print(f"Message: {str(e)}")
                    traceback.print_exc()

                # except Exception as e:
                #     print(f"❌ Failed to get response from OpenAI: {str(e)}")
                #     print(f"{e.with_traceback}");

                    
    except Exception as e:
        print(f"❌ Failed to create AI Project client: {str(e)}")
        print("   Please check:")
        print("   - AZURE_AI_PROJECT_ENDPOINT is correct")
        print("   - You have proper authentication set up")
        print("   - Your Azure credentials have access to the project")


def test_agents_connection(endpoint: str, credential):
    """
    Test connection to Azure AI Agents service.
    
    Args:
        endpoint (str): The Azure AI Project endpoint
        credential: Azure credential object
    """
    
    try:
        # Create Agents client
        with AgentsClient(
            endpoint=endpoint, 
            credential=credential, 
            api_version="2025-11-15-preview"
        ) as agents_client:
            
            print("✅ Successfully created Agents client")
            
            # List available agents
            try:
                agents = list(agents_client.agents.list())
                print(f"✅ Found {len(agents)} agent(s) in the project:")
                
                for agent in agents[:3]:  # Show first 3 agents
                    print(f"   - {agent.name} (ID: {agent.id})")
                
                if len(agents) == 0:
                    print("   No agents found in this project.")
                    print("   You can create agents through the Foundry portal or programmatically.")
                    
            except Exception as e:
                print(f"❌ Failed to list agents: {str(e)}")
                
    except Exception as e:
        print(f"❌ Failed to create Agents client: {str(e)}")


def main():
    """
    Main function to demonstrate Azure Foundry OpenAI connection.
    """
    
    print("🔗 Azure Foundry OpenAI Connection Test")
    print("=" * 50)
    
    # Get configuration from environment variables
    endpoint = os.environ.get("AZURE_AI_PROJECT_ENDPOINT")
    model_deployment = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME")
    
    if not endpoint:
        print("❌ AZURE_AI_PROJECT_ENDPOINT environment variable is required")
        print("   Copy .env.example to .env and set your project endpoint:")
        print("   https://<account_name>.services.ai.azure.com/api/projects/<project_name>")
        return
    
    print(f"📍 Project Endpoint: {endpoint}")
    if model_deployment:
        print(f"🤖 Model Deployment: {model_deployment}")
    else:
        print("🤖 Model Deployment: Will use default (gpt-4o-mini)")
        model_deployment = "gpt-4o-mini"
    
    print("\n" + "=" * 50)
    
    # Create Azure credential
    try:
        # credential = DefaultAzureCredential()
        credential = ClientSecretCredential(
            tenant_id=os.environ.get("AZURE_TENANT_ID"),
            client_id=os.environ.get("AZURE_CLIENT_ID"),
            client_secret=os.environ.get("AZURE_CLIENT_SECRET")
        )
        print("✅ Successfully created Azure credentials")
    except Exception as e:
        print(f"❌ Failed to create Azure credentials: {str(e)}")
        return
    
    print("\n🧪 Testing Azure OpenAI Connection...")
    print("-" * 30)
    asyncio.run(test_openai_connection(endpoint, credential, model_deployment))
    
    print("\n" + "=" * 50)
    print("✨ Connection test completed!")
    print("\nNext steps:")
    print("- Use the Azure OpenAI client for chat completions, embeddings, etc.")


if __name__ == "__main__":
    main()