# Lab 01: Terraform Azure AI Foundry Environment

This lab demonstrates how to provision a complete Azure AI Foundry environment using Terraform, including Azure OpenAI with GPT-4o, Azure AI Search, and Azure Storage.

## Architecture

This Terraform configuration deploys the following resources:

- **Azure AI Foundry Hub**: Central hub for AI project management
- **Azure AI Foundry Project**: Project workspace for AI development
- **Azure AI Services**: Cognitive Services account for Azure OpenAI
- **GPT-4o Deployment**: Azure OpenAI GPT-4o model deployment
- **Azure AI Search**: Search service for RAG scenarios
- **Azure Storage Account**: Storage for data and artifacts
- **Azure Key Vault**: Secure storage for secrets and keys
- **Azure Container Registry**: Container image storage
- **Application Insights**: Monitoring and telemetry

## Prerequisites

- [Terraform](https://www.terraform.io/downloads.html) >= 1.5.0
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
- An active Azure subscription
- Appropriate permissions to create resources in the subscription

## Setup Instructions

### 1. Authenticate with Azure

```bash
az login
az account set --subscription "<your-subscription-id>"
```

### 2. Configure Variables

Copy the example variables file and update with your values:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and set your Azure subscription ID:

```hcl
subscription_id = "your-subscription-id-here"
```

### 3. Initialize Terraform

```bash
terraform init
```

### 4. Review the Plan

```bash
terraform plan
```

### 5. Apply the Configuration

```bash
terraform apply
```

Type `yes` when prompted to confirm the deployment.

## Configuration Options

### Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `subscription_id` | Azure subscription ID | Required |
| `location` | Azure region | `eastus` |
| `resource_group_name` | Resource group name | `rg-ai-labs` |
| `project_name` | Project name prefix | `ailabs` |
| `environment` | Environment name | `dev` |
| `gpt_model_name` | GPT model name | `gpt-4o` |
| `gpt_model_version` | GPT model version | `2024-08-06` |
| `gpt_deployment_capacity` | Model deployment capacity | `10` |
| `search_sku` | Azure AI Search SKU | `basic` |

### Outputs

After deployment, the following outputs will be available:

- Resource group name
- Storage account name
- AI Search service name and endpoint
- Azure OpenAI endpoint and deployment name
- AI Hub and Project names
- Key Vault, Application Insights, and Container Registry names

View outputs:

```bash
terraform output
```

## Usage

### Access Azure AI Foundry Portal

After deployment, you can access your AI Foundry resources:

1. Navigate to [Azure AI Foundry](https://ai.azure.com/)
2. Sign in with your Azure credentials
3. Select your AI Hub and Project

### Use Azure OpenAI

The GPT-4o model is deployed and ready to use. You can access it via:

- Azure AI Foundry Studio
- Azure OpenAI API
- SDK (Python, .NET, JavaScript)

Example using Azure CLI to test the deployment:

```bash
# Get the endpoint and key
ENDPOINT=$(terraform output -raw cognitive_account_endpoint)
DEPLOYMENT=$(terraform output -raw gpt_deployment_name)

# Get the API key from Azure
KEY=$(az cognitiveservices account keys list \
  --name $(terraform output -raw cognitive_account_name) \
  --resource-group $(terraform output -raw resource_group_name) \
  --query key1 -o tsv)

# Test the deployment
curl -X POST "$ENDPOINT/openai/deployments/$DEPLOYMENT/chat/completions?api-version=2024-06-01" \
  -H "Content-Type: application/json" \
  -H "api-key: $KEY" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello, Azure AI!"}
    ]
  }'
```

## Cleanup

To destroy all resources created by this lab:

```bash
terraform destroy
```

Type `yes` when prompted to confirm the destruction.

## Cost Considerations

This deployment creates several Azure resources that may incur costs:

- **Azure AI Services (OpenAI)**: Pay-per-use based on tokens processed
- **Azure AI Search**: Basic tier has a monthly cost
- **Storage Account**: Pay-per-use for storage and transactions
- **Other resources**: Key Vault, Application Insights, and Container Registry have minimal costs

It's recommended to destroy resources when not in use to avoid unnecessary charges.

## Troubleshooting

### Common Issues

1. **Quota Limitations**: Azure OpenAI requires quota approval. If deployment fails, check your quota in the Azure portal.

2. **Region Availability**: Not all regions support all Azure AI services. The default region (`eastus`) is recommended for availability.

3. **Naming Conflicts**: Resource names must be globally unique. The configuration uses a random suffix to avoid conflicts.

4. **Permissions**: Ensure you have the required permissions to create resources in the subscription.

## Next Steps

- Explore Azure AI Foundry Studio
- Create a prompt flow
- Implement RAG with Azure AI Search
- Build a chatbot using the GPT-4o deployment
- Integrate with your applications using the Azure OpenAI SDK

## Resources

- [Azure AI Foundry Documentation](https://learn.microsoft.com/en-us/azure/ai-studio/)
- [Azure OpenAI Service Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Azure AI Search Documentation](https://learn.microsoft.com/en-us/azure/search/)
- [Terraform Azure Provider Documentation](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
