# Deployment Guide - Agent Tools API

This guide explains how to deploy the Agent Tools API to Azure App Service.

## Prerequisites

- Azure CLI installed and logged in (`az login`)
- Azure Developer CLI (azd) installed
- .NET 8.0 SDK installed
- Appropriate permissions in your Azure subscription

## Option 1: Deploy with Azure Developer CLI (Recommended)

The easiest way to deploy is using `azd`, which will provision all infrastructure and deploy the application:

```bash
# Navigate to the lab directory
cd labs/lab03-azure-ai-evaluations

# Initialize azd (if not already done)
azd init

# Set environment variables
azd env set AZURE_ENV_NAME <your-env-name>
azd env set AZURE_LOCATION <azure-region>  # e.g., eastus2

# Deploy infrastructure and application
azd up
```

After deployment completes, the API URL will be shown in the outputs as `AGENT_TOOLS_API_URI`.

## Option 2: Deploy Infrastructure Only

If you only want to provision the infrastructure:

```bash
cd labs/lab03-azure-ai-evaluations

# Deploy Bicep templates
azd provision
```

## Option 3: Manual Deployment

### Step 1: Deploy Infrastructure

```bash
cd labs/lab03-azure-ai-evaluations/infra

# Create resource group
az group create --name rg-ai-eval-dev --location eastus2

# Deploy Bicep template
az deployment group create \
  --resource-group rg-ai-eval-dev \
  --template-file main.bicep \
  --parameters environmentName=dev location=eastus2
```

### Step 2: Build and Publish the API

```bash
cd ../api/AgentToolsApi

# Restore dependencies
dotnet restore

# Build the project
dotnet build -c Release

# Publish the project
dotnet publish -c Release -o ./publish
```

### Step 3: Deploy to App Service

```bash
# Zip the publish folder
cd publish
zip -r ../publish.zip .
cd ..

# Get the App Service name from infrastructure outputs
APP_SERVICE_NAME=$(az deployment group show \
  --resource-group rg-ai-eval-dev \
  --name main \
  --query properties.outputs.AGENT_TOOLS_API_NAME.value \
  -o tsv)

# Deploy the zip file
az webapp deployment source config-zip \
  --resource-group rg-ai-eval-dev \
  --name $APP_SERVICE_NAME \
  --src publish.zip
```

## Verify Deployment

After deployment, verify the API is running:

```bash
# Get the API URL
API_URL=$(az deployment group show \
  --resource-group rg-ai-eval-dev \
  --name main \
  --query properties.outputs.AGENT_TOOLS_API_URI.value \
  -o tsv)

# Test the API
curl $API_URL/api/order/123
curl $API_URL/api/tracking/123
curl "$API_URL/api/eiffeltower?infoType=hours"

# Access Swagger UI
echo "Swagger UI: $API_URL/swagger"
```

## Monitoring

The API is configured with Application Insights for monitoring and diagnostics.

### View Logs

```bash
# Stream logs from App Service
az webapp log tail \
  --resource-group rg-ai-eval-dev \
  --name $APP_SERVICE_NAME
```

### Access Application Insights

1. Go to Azure Portal
2. Navigate to your resource group
3. Open the Application Insights resource
4. View metrics, logs, and performance data

## Configuration

### Environment Variables

Add application settings to App Service:

```bash
az webapp config appsettings set \
  --resource-group rg-ai-eval-dev \
  --name $APP_SERVICE_NAME \
  --settings KEY1=VALUE1 KEY2=VALUE2
```

### Scale the App Service

To change the App Service Plan tier:

```bash
az appservice plan update \
  --resource-group rg-ai-eval-dev \
  --name <plan-name> \
  --sku B2  # or S1, P1V2, etc.
```

## Troubleshooting

### Check App Service Status

```bash
az webapp show \
  --resource-group rg-ai-eval-dev \
  --name $APP_SERVICE_NAME \
  --query state
```

### View Deployment Logs

```bash
az webapp log deployment show \
  --resource-group rg-ai-eval-dev \
  --name $APP_SERVICE_NAME
```

### Restart App Service

```bash
az webapp restart \
  --resource-group rg-ai-eval-dev \
  --name $APP_SERVICE_NAME
```

## Clean Up

To delete all resources:

```bash
# Using azd
azd down --purge

# Or manually
az group delete --name rg-ai-eval-dev --yes
```

## Next Steps

- Configure custom domain and SSL certificate
- Set up CI/CD pipeline with GitHub Actions or Azure DevOps
- Enable authentication/authorization
- Configure CORS for specific origins
- Add rate limiting and API management
