# Azure Foundry SDK Lab

This lab demonstrates how to connect to an Azure OpenAI model deployed in Microsoft Foundry using the Microsoft Agent Framework.

## Prerequisites

- Azure subscription with access to Microsoft Foundry
- Azure CLI installed and authenticated (`az login`)
- Python 3.8 or higher
- A Microsoft Foundry project with deployed OpenAI models

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Up Environment Variables**
   ```bash
   # Copy the example environment file
   cp env.example .env
   
   # Edit .env with your actual values
   # At minimum, set AZURE_AI_PROJECT_ENDPOINT
   ```

3. **Find Your Foundry Project Endpoint**
   - Go to your Microsoft Foundry project in the Azure portal
   - Copy the endpoint from the overview page
   - It should look like: `https://<account>.services.ai.azure.com/api/projects/<project>`

4. **Run the Connection Test**
   ```bash
   python azure_foundry_openai_connection.py
   ```

## What This Script Does

The script will:

1. ✅ Test connection to your Foundry project
2. ✅ Test OpenAI model access with a simple chat completion
3. ✅ List any existing agents in your project
4. 🏗️ Create a simple test agent
5. 💬 Test a conversation with the created agent

## Environment Variables Reference

### Required
- `AZURE_AI_PROJECT_ENDPOINT`: Your Foundry project endpoint

### Optional
- `AZURE_AI_MODEL_DEPLOYMENT_NAME`: Specific model deployment (defaults to gpt-4o-mini)
- `AZURE_OPENAI_ENDPOINT`: Direct Azure OpenAI endpoint (alternative to Foundry)
- `AZURE_OPENAI_DEPLOYMENT_NAME`: Model deployment name for direct OpenAI
- `AZURE_SUBSCRIPTION_ID`: Azure subscription ID for resource management

## Troubleshooting

### Authentication Issues
- Make sure you're logged in: `az login`
- Check if you have access to the Foundry project
- Verify your Azure subscription and tenant

### Model Deployment Issues
- Check if your model is deployed in the Foundry project
- Verify the deployment name matches your environment variable
- Try using "gpt-4o-mini" as a fallback

### Connection Issues
- Verify your project endpoint is correct
- Check if your Foundry project is in the right region
- Ensure network connectivity to Azure services

## Examples

### Simple Chat Completion
```python
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

credential = DefaultAzureCredential()
endpoint = "your-foundry-endpoint"

with AIProjectClient(endpoint=endpoint, credential=credential) as client:
    with client.get_openai_client() as openai_client:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello!"}],
            max_tokens=100
        )
        print(response.choices[0].message.content)
```

### Creating an Agent
```python
from azure.ai.agents import AgentsClient

with AgentsClient(endpoint=endpoint, credential=credential) as agents_client:
    agent = agents_client.agents.create(
        name="my-assistant",
        description="A helpful assistant",
        instructions="You are a helpful AI assistant.",
        model="gpt-4o-mini"
    )
    print(f"Created agent: {agent.id}")
```

## Next Steps

- Explore the [Azure AI Projects SDK documentation](https://docs.microsoft.com/azure/ai-services/foundry/)
- Check out agent conversation patterns
- Integrate with your applications
- Explore function calling and tool use
- Set up evaluation pipelines

## Related Files

- `requirements.txt`: Python dependencies
- `env.example`: Environment variable template
- `.env`: Your actual environment configuration (don't commit this!)
- `azure_foundry_openai_connection.py`: Main connection test script