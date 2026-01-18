"""
Deploy YAML-based agents to Azure AI Foundry Project.

This script deploys declarative agents (v2) defined in YAML format to Azure AI Foundry.
These agents appear in the new Foundry UI and support advanced features like grounding.

Requirements:
    pip install azure-ai-projects azure-identity pyyaml python-dotenv

Environment Variables:
    AZURE_AI_PROJECT_NAME - Name of the AI Foundry project
    AZURE_RESOURCE_GROUP - Resource group name
    AZURE_SUBSCRIPTION_ID - Azure subscription ID
"""

import os
import yaml
from pathlib import Path
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def load_agent_definition(yaml_file: str) -> dict:
    """Load and parse agent definition from YAML file."""
    yaml_path = Path(__file__).parent.parent / "agents" / yaml_file
    
    if not yaml_path.exists():
        raise FileNotFoundError(f"Agent definition not found: {yaml_path}")
    
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)


def create_v2_agent(client: AIProjectClient, agent_def: dict):
    """Create a v2 declarative agent from YAML definition."""
    
    print(f"Creating agent: {agent_def['name']}")
    print(f"Description: {agent_def['description']}")
    print(f"Model: {agent_def['model']['name']}\n")
    
    # Extract configuration
    model_config = agent_def['model']['configuration']
    tools = []
    
    # Configure tools based on YAML definition
    for tool in agent_def.get('tools', []):
        if tool.get('enabled', True):
            tools.append({"type": tool['type']})
    
    # Create the agent
    agent = client.agents.create_agent(
        name=agent_def['name'],
        description=agent_def['description'],
        model=agent_def['model']['name'],
        instructions=agent_def['instructions'],
        tools=tools,
        temperature=model_config.get('temperature', 0.7),
        top_p=model_config.get('top_p', 0.95)
    )
    
    print("✓ Agent created successfully!\n")
    print("Agent Details:")
    print(f"  ID: {agent.id}")
    print(f"  Name: {agent.name}")
    print(f"  Model: {agent.model}")
    print(f"  Tools: {[t['type'] for t in tools]}")
    
    if 'metadata' in agent_def:
        print(f"  Category: {agent_def['metadata'].get('category', 'N/A')}")
        print(f"  Tags: {', '.join(agent_def['metadata'].get('tags', []))}")
    
    print(f"\n✓ Agent is now available in Azure AI Foundry portal")
    
    return agent


def deploy_agent(yaml_file: str):
    """Deploy an agent from YAML definition to Azure AI Foundry."""
    
    # Get configuration from environment
    project_name = os.getenv("AZURE_AI_PROJECT_NAME")
    resource_group = os.getenv("AZURE_RESOURCE_GROUP")
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    project_endpoint = os.getenv("AZURE_FOUNDRY_PROJECT_ENDPOINT")
    
    if not all([project_name, resource_group, subscription_id, project_endpoint]):
        raise ValueError(
            "Missing required environment variables. Please set:\n"
            "  - AZURE_AI_PROJECT_NAME\n"
            "  - AZURE_RESOURCE_GROUP\n"
            "  - AZURE_SUBSCRIPTION_ID\n"
            "  - AZURE_FOUNDRY_PROJECT_ENDPOINT"
        )
    
    # Load agent definition
    print(f"Loading agent definition from: {yaml_file}\n")
    agent_def = load_agent_definition(yaml_file)
    
    # Construct project connection
    project_connection = (
        f"/subscriptions/{subscription_id}"
        f"/resourceGroups/{resource_group}"
        f"/providers/Microsoft.CognitiveServices/accounts/{project_name.replace('-project', '')}"
        f"/projects/{project_name}"
    )
    
    print(f"Connecting to AI Foundry Project: {project_name}\n")
    
    # Initialize client
    credential = DefaultAzureCredential()
    client = AIProjectClient(
        endpoint=project_endpoint,
        credential=credential,
        project_connection_string=project_connection
    )
    
    print("✓ Connected to AI Foundry Project\n")
    
    # Create the agent
    agent = create_v2_agent(client, agent_def)
    
    return agent


def list_available_agents():
    """List all available agent definitions in the agents directory."""
    agents_dir = Path(__file__).parent.parent / "agents"
    
    if not agents_dir.exists():
        print("No agents directory found.")
        return []
    
    yaml_files = list(agents_dir.glob("*.yaml")) + list(agents_dir.glob("*.yml"))
    
    print("\nAvailable agent definitions:")
    print("-" * 60)
    
    for yaml_file in yaml_files:
        try:
            with open(yaml_file, 'r') as f:
                agent_def = yaml.safe_load(f)
                print(f"\n📄 {yaml_file.name}")
                print(f"   Name: {agent_def.get('name', 'N/A')}")
                print(f"   Description: {agent_def.get('description', 'N/A')}")
                print(f"   Model: {agent_def.get('model', {}).get('name', 'N/A')}")
                
                tools = [t['type'] for t in agent_def.get('tools', []) if t.get('enabled', True)]
                if tools:
                    print(f"   Tools: {', '.join(tools)}")
        except Exception as e:
            print(f"\n❌ Error reading {yaml_file.name}: {e}")
    
    print("\n" + "-" * 60)
    return yaml_files


def main():
    """Main execution function."""
    import sys
    
    try:
        # List available agents
        available_agents = list_available_agents()
        
        if not available_agents:
            print("\n❌ No agent definitions found in the agents/ directory")
            return 1
        
        # Deploy agent based on command line argument or default
        if len(sys.argv) > 1:
            yaml_file = sys.argv[1]
        else:
            print("\nNo agent specified. Deploying 'evaluation-assistant.yaml'")
            print("Usage: python deploy_agent.py <agent-file.yaml>")
            yaml_file = "evaluation-assistant.yaml"
        
        print(f"\n{'=' * 60}")
        print("DEPLOYING AGENT")
        print(f"{'=' * 60}\n")
        
        agent = deploy_agent(yaml_file)
        
        print(f"\n{'=' * 60}")
        print("✓ DEPLOYMENT COMPLETE")
        print(f"{'=' * 60}")
        print(f"\nView your agent at: https://ai.azure.com")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\nAvailable agents:")
        for agent_file in available_agents:
            print(f"  - {agent_file.name}")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
