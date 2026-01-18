# YAML-Based Agent Deployment

This directory contains YAML-based agent definitions for Azure AI Foundry v2 agents. These agents use a declarative format and appear in the new Foundry UI.

## Agent Definitions

### Available Agents

1. **evaluation-assistant.yaml** - Agent specialized in evaluation tasks
   - Tools: Code Interpreter, File Search
   - Temperature: 0.7 (balanced creativity)
   - Best for: Analyzing evaluation results and metrics

2. **code-reviewer.yaml** - Agent for code review and analysis
   - Tools: Code Interpreter
   - Temperature: 0.3 (focused and deterministic)
   - Best for: Security audits, quality checks, refactoring suggestions

3. **research-assistant.yaml** - Agent for research and document analysis
   - Tools: File Search, Code Interpreter
   - Temperature: 0.8 (creative synthesis)
   - Best for: Document analysis, information synthesis, research tasks

## YAML Agent Schema

```yaml
name: agent-name                    # Unique identifier
version: 1.0.0                      # Semantic version
description: Agent description      # What the agent does

model:
  name: gpt-4o                     # Model deployment name
  type: chat
  configuration:
    temperature: 0.7               # 0.0-1.0 (higher = more creative)
    top_p: 0.95                    # Nucleus sampling
    max_tokens: 4000               # Maximum response length

instructions: |                    # System prompt (multi-line)
  Your agent instructions here...

tools:                             # Available tools
  - type: code_interpreter
    enabled: true
    description: Execute Python code
    
  - type: file_search
    enabled: true
    description: Search uploaded files

conversation:
  max_turns: 50                    # Conversation limit
  context_window: 128000           # Token window

grounding:                         # Optional grounding config
  enabled: true
  sources:
    - type: ai_search
      enabled: false

metadata:                          # Optional metadata
  category: evaluation
  tags:
    - tag1
    - tag2
  created_by: your-name
  purpose: description
```

## Deployment

### Prerequisites

```bash
# Install dependencies
pip install -r requirements-agent.txt

# Ensure environment is configured
azd env get-values > ../.env
```

### Deploy an Agent

```bash
# Deploy specific agent
python deploy_agent.py evaluation-assistant.yaml

# Deploy code reviewer
python deploy_agent.py code-reviewer.yaml

# Deploy research assistant
python deploy_agent.py research-assistant.yaml

# List available agents
python deploy_agent.py
```

### Expected Output

```
Available agent definitions:
------------------------------------------------------------

📄 evaluation-assistant.yaml
   Name: evaluation-assistant
   Description: AI agent for evaluation tasks and analysis
   Model: gpt-4o
   Tools: code_interpreter, file_search

============================================================
DEPLOYING AGENT
============================================================

Loading agent definition from: evaluation-assistant.yaml

Connecting to AI Foundry Project: aifxxxxx-project

✓ Connected to AI Foundry Project

Creating agent: evaluation-assistant
Description: AI agent for evaluation tasks and analysis
Model: gpt-4o

✓ Agent created successfully!

Agent Details:
  ID: asst_xxxxx
  Name: evaluation-assistant
  Model: gpt-4o
  Tools: ['code_interpreter', 'file_search']
  Category: evaluation
  Tags: evaluation, analysis, ai-quality

✓ Agent is now available in Azure AI Foundry portal

============================================================
✓ DEPLOYMENT COMPLETE
============================================================

View your agent at: https://ai.azure.com
```

## Creating Custom Agents

### 1. Create a new YAML file

```bash
# Copy an existing template
cp evaluation-assistant.yaml my-custom-agent.yaml
```

### 2. Edit the YAML definition

Customize:
- `name` - Unique agent identifier
- `description` - What your agent does
- `instructions` - Detailed system prompt
- `model.configuration.temperature` - Creativity level (0.0-1.0)
- `tools` - Enable/disable code_interpreter and file_search
- `metadata.tags` - Categorization tags

### 3. Deploy your custom agent

```bash
python deploy_agent.py my-custom-agent.yaml
```

## Tool Capabilities

### Code Interpreter
- Execute Python code
- Analyze data with pandas, numpy, scipy
- Create visualizations with matplotlib
- Process files and generate outputs

### File Search
- Search through uploaded documents
- RAG-based question answering
- Document summarization
- Citation extraction

## Best Practices

1. **Temperature Settings**
   - 0.0-0.3: Factual, deterministic (code review, analysis)
   - 0.4-0.7: Balanced (general assistance)
   - 0.8-1.0: Creative (brainstorming, research)

2. **Instructions**
   - Be specific about agent capabilities
   - Include examples of expected behavior
   - Define response format preferences
   - Set boundaries and limitations

3. **Tools**
   - Only enable tools the agent needs
   - Document tool usage in instructions
   - Consider token costs for file_search

4. **Metadata**
   - Use consistent tagging
   - Document versioning
   - Track agent purpose and owner

## Troubleshooting

### Agent not visible in portal
- Check that deployment completed successfully
- Verify you're viewing the correct project
- Refresh the browser

### Model not found
- Ensure `gpt-4o` is deployed in your project
- Check model deployment name matches
- Verify model has sufficient capacity

### Tool errors
- Confirm tools are enabled in your project
- Check RBAC permissions
- Verify resource quotas

## Next Steps

- Test agents in Foundry playground
- Create agent threads for conversations
- Upload files for file_search capability
- Configure grounding with AI Search
- Monitor agent usage and costs
