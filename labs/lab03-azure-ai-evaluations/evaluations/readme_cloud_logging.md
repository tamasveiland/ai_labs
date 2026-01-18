# Running Local Evaluations with Azure AI Foundry Logging

## Overview

You can run evaluations locally on your machine while having the results automatically appear in Azure AI Foundry. This combines the convenience of local development with cloud-based result tracking and visualization.

## How It Works

The `evaluate_local.py` script now supports the `azure_ai_project` parameter in the `evaluate()` function. When configured, evaluation results are automatically logged to your Azure AI Foundry project where you can:

- View evaluation runs in the Foundry portal
- Compare multiple evaluation runs
- Track metrics over time
- Share results with your team

## Setup

### 1. Set Environment Variables

Add these variables to your `.env` file or environment:

```bash
# Required for evaluation
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o

# Optional: For cloud logging to Azure AI Foundry
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_RESOURCE_GROUP=your-resource-group-name
AZURE_AI_PROJECT_NAME=your-ai-project-name
```

### 2. Get Your Azure AI Project Information

You can find these values in the Azure AI Foundry portal:

1. Navigate to your AI Foundry project
2. Go to **Settings** → **Project properties**
3. Copy the subscription ID, resource group, and project name

Or use Azure CLI:

```bash
# Get subscription ID
az account show --query id -o tsv

# List AI Foundry projects in resource group
az ml workspace list --resource-group <rg-name> --query "[].name" -o tsv
```

### 3. Ensure Dependencies

The required package should already be in your requirements.txt:

```bash
azure-ai-ml>=1.13.0
```

## Usage

### Local Only (Default)

Run without cloud logging (results only saved locally):

```bash
python evaluate_local.py
```

Output:
```
ℹ️  Running local-only evaluation (results won't appear in Foundry)
```

### With Cloud Logging

Set the environment variables and run:

```bash
python evaluate_local.py
```

Output:
```
✅ Azure AI Foundry project configured - results will be logged to cloud
☁️  Logging results to Azure AI Foundry project: your-project-name
```

## Viewing Results in Azure AI Foundry

1. Navigate to [Azure AI Foundry](https://ai.azure.com)
2. Select your project
3. Go to **Evaluation** section
4. View your evaluation runs with:
   - Aggregate metrics
   - Individual row scores
   - Comparison charts
   - Run metadata

## Benefits

✅ **Local Development** - Run evaluations on your machine with fast iteration  
✅ **Cloud Tracking** - Automatic logging to Azure AI Foundry  
✅ **Team Collaboration** - Share results with stakeholders  
✅ **Version Control** - Track evaluation metrics over time  
✅ **Flexibility** - Works with or without cloud logging

## Troubleshooting

### Authentication Issues

If you see authentication errors:

```bash
# Login to Azure
az login

# Set default subscription
az account set --subscription <subscription-id>
```

### Missing Project

If the project isn't found:

```bash
# Verify project exists
az ml workspace show --name <project-name> --resource-group <rg-name>
```

### Results Not Appearing

- Wait 1-2 minutes for results to propagate
- Refresh the Azure AI Foundry portal
- Check that you're looking at the correct project
- Verify environment variables are set correctly

## Example .env File

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://my-openai.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-08-01-preview

# Optional: API Key (if not using managed identity)
# AZURE_OPENAI_API_KEY=your-api-key

# Azure AI Foundry Project (for cloud logging)
AZURE_SUBSCRIPTION_ID=12345678-1234-1234-1234-123456789abc
AZURE_RESOURCE_GROUP=rg-ai-labs-dev
AZURE_AI_PROJECT_NAME=ai-project-dev
```

## Next Steps

- Run multiple evaluations and compare results in Foundry
- Set up automated evaluation pipelines
- Integrate with CI/CD for continuous quality monitoring
- Export results for further analysis
