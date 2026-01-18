"""
Deploy v2 agents to Azure AI Foundry using the Foundry Agent Service SDK.

This script creates declarative agents (v2) using the AIProjectClient.Administration API.
These agents appear in the new Azure AI Foundry UI with full enterprise features.

Requirements:
    pip install azure-ai-projects azure-identity pyyaml python-dotenv

Environment Variables:
    AZURE_SUBSCRIPTION_ID - Your Azure subscription ID
    AZURE_RESOURCE_GROUP - Resource group containing the AI Foundry project
    AZURE_AI_FOUNDRY_ACCOUNT - AI Foundry account name
    AZURE_AI_PROJECT_NAME - AI Foundry project name
"""

import os
import json
import yaml
from pathlib import Path
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_project_client() -> AIProjectClient:
    """Create AIProjectClient for Foundry Agent Service."""
    
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    resource_group = os.getenv("AZURE_RESOURCE_GROUP")
    account_name = os.getenv("AZURE_AI_FOUNDRY_ACCOUNT")
    project_name = os.getenv("AZURE_AI_PROJECT_NAME")
    
    if not all([subscription_id, resource_group, account_name, project_name]):
        raise ValueError(
            "Missing required environment variables:\n"
            "  AZURE_SUBSCRIPTION_ID\n"
            "  AZURE_RESOURCE_GROUP\n"
            "  AZURE_AI_FOUNDRY_ACCOUNT\n"
            "  AZURE_AI_PROJECT_NAME"
        )
    
    # Construct the project connection string
    project_connection = (
        f"https://mangent_params(agent_def: dict) -> dict:
    """Convert YAML agent definition to Foundry Agent Service parameters."""
    
    # Extract tools - convert to tool definitions
    tools = []
    tool_resources = {}
    
    for tool in agent_def.get('tools', []):
        if tool.get('enabled', True):
            tool_type = tool['type']
            tools.append({"type": tool_type})
            
            # Initialize tool_resources for file_search and code_interpreter
            if tool_type == "file_search" and tool_type not in tool_resources:
                tool_resources["file_search"] = {}
            elif tool_type == "code_interpreter" and tool_type not in tool_resources:
                tool_resources["code_interpreter"] = {}
    
    # Build the parameters for CreateAgent
    params = {
        "model": agent_def['model']['name'],
        "name": agent_def['name'],
        "description": agent_def.get('description', ''),
        "instructions": agent_def.get('instructions', ''),
        "tools": tools,
        "temperature": agent_def['model']['configuration'].get('temperature', 0.7),
        "top_p": agent_def['model']['configuration'].get('top_p', 0.95)
    }
    
    # Add tool_resources if we have any tools
    if tool_resources:
        params["tool_resources"] = tool_resources
    
    # Add metadata
    if 'metadata' in agent_def:
        params["metadata"] = agent_def['metadata']
    
    return paramsNotFoundError(f"Agent definition not found: {yaml_path}")
    
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)


def convert_yaml_to_api_payload(agent_def: dict) -> dict:
    """Convert YAML agent definition to Foundry API payload format."""
    
    # Extract tools
    tools = []
    for tool in agent_def.get('tools', []):
        if tool.get('enabled', True):
            tools.append({
                "type": tool['type']
            })
    
    # Build the API payload
    payload = {
        "name": agent_def['name'],
        "description": agent_def.get('description', ''),
        "instructions": agent_def.get('instructions', ''),
        "model": agent_def['model']['name'],
        "tools": tools,
        "temperature": agent_def['model']['configuration'].get('temperature', 0.7),
        "top_p": agent_def['model']['configuration'].get('top_p', 0.95)
        # "metadata":sdk(client: AIProjectClient, params: dict) -> dict:
    """Create agent using Foundry Agent Service SDK."""
    
    print("="*60)
    print("CREATING V2 FOUNDRY AGENT")
    print("="*60 + "\n")
    
    print(f"Agent Name: {params['name']}")
    print(f"Model: {params['model']}")
    print(f"Temperature: {params['temperature']}")
    print(f"Tools: {[t['type'] for t in params.get('tools', [])]}\n")
    
    print("Agent Parameters:")
    print(json.dumps(params, indent=2))
    print("\n" + "="*60 + "\n")
    
    try:
        # Create agent using Administration API
        agent = client.agents.create_agent(**params)
        
        print("✓ Agent created successfully!\n")
        print("Agent Details:")
        print(f"  ID: {agent.id}")
        print(f"  Name: {agent.name}")
        print(f"  Model: {agent.model}")
        print(f"  Created At: {agent.created_at}")
        
        return agent
        
    except Exception as e:
        print(f"❌ Error creating agent: {str(e)}")
        raise(payload, indent=2))
    print("\n" + "="*60 + "\n")
    
    response = requests.post(api_url, headers=headers, json=payload)
    
    print(f"Response Status: {response.status_code}")
    
    if response.status_code in [200, 201]:
        agent = response.json()
        print("✓ Agent created successfully!\n")
        return agent
    else:
        print(f"❌ Error creating agent:")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        response.raise_for_status()


def list_agents_via_sdk(client: AIProjectClient) -> list:
    """List all agents using Foundry Agent Service SDK."""
    
    try:
        agents = client.agents.list_agents()
        return list(agents)
    except Exception as e:
        print(f"❌ Error listing agents: {str(e)}")
        return []


def deploy_agent_v2(yaml_file: str):
    """Deploy a v2 agent from YAML definition using Foundry Agent Service SDK."""
    
    print(f"Loading agent definition from: {yaml_file}\n")
    agent_def = load_agent_definition(yaml_file)
    
    # Create project client
    client = get_project_client()
    
    # Convert YAML to agent parameters
    params = convert_yaml_to_agent_params(agent_def)
    
    # Create agent via SDK
    agent = create_agent_via_sdk(client, params)
    
    return agent


def list_all_agents():
    """List all agents in the project."""
    
    print("Connecting to Foundry project...\n")
    client = get_project_client()
    
    print("Fetching agents from Foundry...\n")
    agents = list_agents_via_sdk(client)
    
    if agents:
        print(f"Found {len(agents)} agent(s):\n")
        for agent in agents:
            print(f"  • {agent.name} (ID: {agent.id})")
            print(f"    Model: {agent.model}")
            print(f"    Description: {agent.description or 'N/A'}")
            print(f"    Created: {agent.created_at}")
            print()
    else:
        print("No agents found in project.")


def list_available_definitions():
    """List all available agent definitions in the agents directory."""
    agents_dir = Path(__file__).parent.parent / "agents"
    
    if not agents_dir.exists():
        print("No agents directory found.")
        return []
    
    yaml_files = list(agents_dir.glob("*.yaml")) + list(agents_dir.glob("*.yml"))
    
    print("\n" + "="*60)
    print("AVAILABLE AGENT DEFINITIONS")
    print("="*60 + "\n")
    
    for yaml_file in yaml_files:
        try:
            with open(yaml_file, 'r') as f:
                agent_def = yaml.safe_load(f)
                print(f"📄 {yaml_file.name}")
                print(f"   Name: {agent_def.get('name', 'N/A')}")
                print(f"   Description: {agent_def.get('description', 'N/A')}")
                print(f"   Model: {agent_def.get('model', {}).get('name', 'N/A')}")
                
                tools = [t['type'] for t in agent_def.get('tools', []) if t.get('enabled', True)]
                if tools:
                    print(f"   Tools: {', '.join(tools)}")
                print()
        except Exception as e:
            print(f"❌ Error reading {yaml_file.name}: {e}\n")
    
    return yaml_files


def main():
    """Main execution function."""
    import sys
    
    try:
        # Check command
        if len(sys.argv) > 1 and sys.argv[1] == "--list":
            list_all_agents()
            return 0
        
        # List available definitions
        available_agents = list_available_definitions()
        
        if not available_agents:
            print("❌ No agent definitions found in the agents/ directory")
            return 1
        
        # Deploy agent
        if len(sys.argv) > 1:
            yaml_file = sys.argv[1]
        else:
            print("\n" + "="*60)
            print("No agent specified. Deploying 'evaluation-assistant.yaml'")
            print("Usage: python deploy_agent_v2.py <agent-file.yaml>")
            print("       python deploy_agent_v2.py --list")
            print("="*60 + "\n")
            yaml_file = "evaluation-assistant.yaml"
        
        agent = deploy_agent_v2(yaml_file)
        
        print("\n" + "="*60)
        print("✓ DEPLOYMENT COMPLETE")
        print("="*60)
        print(f"\nAgent ID: {agent.id}")
        print(f"Agent Name: {agent.name}")
        print(f"View at: https://ai.azure.com\n")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\nAvailable agents:")
        for agent_file in list_available_definitions():
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
