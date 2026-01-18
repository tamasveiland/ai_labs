"""
Create an AI Agent in Azure AI Foundry Project using the latest SDK.

This script demonstrates how to create an agent that appears in the new Azure AI Foundry UI.
It uses the azure-ai-projects SDK with the latest API versions.

Requirements:
    pip install azure-ai-projects azure-identity python-dotenv

Environment Variables:
    AZURE_AI_PROJECT_NAME - Name of the AI Foundry project
    AZURE_RESOURCE_GROUP - Resource group name
    AZURE_SUBSCRIPTION_ID - Azure subscription ID
"""

import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_agent():
    """Create an AI agent in Azure AI Foundry Project."""
    
    # Get configuration from environment
    project_name = os.getenv("AZURE_AI_PROJECT_NAME")
    resource_group = os.getenv("AZURE_RESOURCE_GROUP")
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    project_endpoint = os.getenv("AZURE_FOUNDRY_PROJECT_ENDPOINT")
    
    if not all([project_name, resource_group, subscription_id]):
        raise ValueError(
            "Missing required environment variables. Please set:\n"
            "  - AZURE_AI_PROJECT_NAME\n"
            "  - AZURE_RESOURCE_GROUP\n"
            "  - AZURE_SUBSCRIPTION_ID"
        )
    
    # Construct the project connection string
    # Format: /subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.CognitiveServices/accounts/{account}/projects/{project}
    project_connection = (
        f"/subscriptions/{subscription_id}"
        f"/resourceGroups/{resource_group}"
        f"/providers/Microsoft.CognitiveServices/accounts/{project_name.replace('-project', '')}"
        f"/projects/{project_name}"
    )
    
    print(f"Connecting to AI Foundry Project: {project_name}")
    print(f"Project connection: {project_connection}\n")
    print(f"Using endpoint: {project_endpoint}\n")
    
    # Initialize the AI Project client with DefaultAzureCredential
    credential = DefaultAzureCredential()
    client = AIProjectClient(
        endpoint=project_endpoint,
        credential=credential,
        project_connection_string=project_connection
    )
    
    print("✓ Successfully connected to AI Foundry Project\n")
    
    # Agent configuration
    agent_name = "evaluation-assistant"
    agent_description = "AI agent for helping with evaluation tasks and analysis"
    model_deployment = "gpt-4o"  # Must match the deployment name in your project
    
    print(f"Creating agent: {agent_name}")
    print(f"Model deployment: {model_deployment}")
    print(f"Description: {agent_description}\n")
    
    # Create the agent using the latest API
    agent = client.agents.create_agent(
        name=agent_name,
        description=agent_description,
        model=model_deployment,
        instructions="""You are an AI evaluation assistant. Your role is to:
        
1. Help users understand and interpret evaluation metrics
2. Analyze evaluation results and provide insights
3. Suggest improvements based on evaluation outcomes
4. Explain best practices for AI model evaluation
5. Answer questions about groundedness, relevance, coherence, and other quality metrics

Be clear, concise, and provide actionable recommendations.""",
        tools=[
            {"type": "code_interpreter"},  # Enable code interpreter for data analysis
            {"type": "file_search"}        # Enable file search for RAG scenarios
        ],
        temperature=0.7,
        top_p=0.95
    )
    
    print("✓ Agent created successfully!\n")
    print("Agent Details:")
    print(f"  ID: {agent.id}")
    print(f"  Name: {agent.name}")
    print(f"  Model: {agent.model}")
    print(f"  Created at: {agent.created_at}")
    print(f"\n✓ Agent should now be visible in Azure AI Foundry portal at:")
    print(f"  https://ai.azure.com")
    
    return agent

def list_agents():
    """List all agents in the AI Foundry Project."""
    
    # Get configuration from environment
    project_name = os.getenv("AZURE_AI_PROJECT_NAME")
    resource_group = os.getenv("AZURE_RESOURCE_GROUP")
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    project_endpoint = os.getenv("AZURE_FOUNDRY_PROJECT_ENDPOINT")   
    
    project_connection = (
        f"/subscriptions/{subscription_id}"
        f"/resourceGroups/{resource_group}"
        f"/providers/Microsoft.CognitiveServices/accounts/{project_name.replace('-project', '')}"
        f"/projects/{project_name}"
    )
    
    credential = DefaultAzureCredential()
    client = AIProjectClient(
        endpoint=project_endpoint,
        credential=credential,
        project_connection_string=project_connection
    )
    
    print("\nListing all agents in the project:\n")
    agents = client.agents.list_agents()
    
    for agent in agents:
        print(f"  • {agent.name} (ID: {agent.id})")
        print(f"    Model: {agent.model}")
        print(f"    Created: {agent.created_at}\n")

def main():
    """Main execution function."""
    try:
        # Create the agent
        agent = create_agent()
        
        # List all agents to verify
        list_agents()
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
