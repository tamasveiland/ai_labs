# AI Agent Creation Script

This script creates an AI agent in your Azure AI Foundry project using the latest Azure AI Projects SDK. The agent will appear in the new Azure AI Foundry UI at https://ai.azure.com.

## Prerequisites

- Azure AI Foundry project deployed (via `azd up`)
- Python 3.9 or higher
- Azure CLI authenticated (`az login`)

## Setup

1. **Create a Python virtual environment:**
   
   Navigate to the lab03 directory:
   ```bash
   cd labs/lab03-azure-ai-evaluations
   ```
   
   Create and activate the virtual environment:
   ```powershell
   # Create virtual environment
   python -m venv .venv
   
   # Activate (PowerShell)
   .\.venv\Scripts\Activate.ps1
   
   # Or activate (Command Prompt)
   .venv\Scripts\activate.bat
   
   # Or activate (Bash/Linux/macOS)
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r scripts/requirements-agent.txt
   ```

3. **Configure environment variables:**
   
   Copy `.env.example` to `.env` and update with your values:
   ```bash
   cp .env.example .env
   ```
   
   Or get values from azd:
   ```bash
   azd env get-values > .env
   ```

## Usage

### Create an Agent

```bash
python create_agent.py
```

This will:
1. Connect to your AI Foundry project
2. Create an agent named "evaluation-assistant"
3. Configure it with GPT-4o model
4. Enable code interpreter and file search tools
5. Display agent details and confirmation

### Expected Output

```
Connecting to AI Foundry Project: aif12345-project
Project connection: /subscriptions/.../projects/aif12345-project

✓ Successfully connected to AI Foundry Project

Creating agent: evaluation-assistant
Model deployment: gpt-4o
Description: AI agent for helping with evaluation tasks and analysis

✓ Agent created successfully!

Agent Details:
  ID: asst_abc123xyz
  Name: evaluation-assistant
  Model: gpt-4o
  Created at: 2026-01-16T...

✓ Agent should now be visible in Azure AI Foundry portal at:
  https://ai.azure.com
```

## Agent Configuration

The created agent includes:

- **Name:** evaluation-assistant
- **Model:** gpt-4o (must match your deployment)
- **Tools:**
  - Code Interpreter - for data analysis
  - File Search - for RAG scenarios
- **Instructions:** Specialized for evaluation tasks

## Customization

Edit the script to customize:

```python
agent = client.agents.create_agent(
    name="your-agent-name",
    model="your-model-deployment",
    instructions="Your custom instructions...",
    temperature=0.7,  # Adjust creativity
    top_p=0.95        # Adjust diversity
)
```

## Viewing in Azure Portal

After creation, view your agent at:
1. Navigate to https://ai.azure.com
2. Select your project
3. Go to "Agents" section
4. Your agent will appear in the list

## Troubleshooting

### Authentication Error
```bash
az login
az account set --subscription "your-subscription-id"
```

### Project Not Found
Verify your environment variables match the deployed resources:
```bash
azd env get-values
```

### Model Not Found
Ensure the model deployment name matches what's deployed in your project:
- Default: `gpt-4o`
- Check in portal: AI Foundry > Deployments

## Next Steps

- Use the agent in the Foundry playground
- Create threads and run conversations
- Add files for file search capability
- Integrate with your evaluation workflows
