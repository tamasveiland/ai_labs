# Random string for unique resource names
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

# Storage Account
resource "azurerm_storage_account" "main" {
  name                     = "st${var.project_name}${var.environment}${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = var.storage_account_tier
  account_replication_type = var.storage_account_replication_type
  tags                     = var.tags
}

# Azure AI Search
resource "azurerm_search_service" "main" {
  name                = "search-${var.project_name}-${var.environment}-${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.search_sku
  tags                = var.tags
}

# Application Insights for AI Foundry
resource "azurerm_application_insights" "main" {
  name                = "appi-${var.project_name}-${var.environment}-${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  application_type    = "web"
  tags                = var.tags
}

# Key Vault for secrets
resource "azurerm_key_vault" "main" {
  name                       = "kv-${var.project_name}-${var.environment}-${random_string.suffix.result}"
  resource_group_name        = azurerm_resource_group.main.name
  location                   = azurerm_resource_group.main.location
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 7
  purge_protection_enabled   = false
  tags                       = var.tags
}

# Container Registry for AI Foundry
resource "azurerm_container_registry" "main" {
  name                = "cr${var.project_name}${var.environment}${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = true
  tags                = var.tags
}

# AI Hub (AI Foundry Hub)
resource "azapi_resource" "ai_hub" {
  type      = "Microsoft.MachineLearningServices/workspaces@2024-04-01"
  name      = "aih-${var.project_name}-${var.environment}-${random_string.suffix.result}"
  parent_id = azurerm_resource_group.main.id
  location  = azurerm_resource_group.main.location
  tags      = var.tags

  identity {
    type = "SystemAssigned"
  }

  body = jsonencode({
    properties = {
      description = "AI Foundry Hub for ${var.project_name}"
      friendlyName = "AI Hub ${var.project_name} ${var.environment}"
      kind = "Hub"
      storageAccount = azurerm_storage_account.main.id
      keyVault = azurerm_key_vault.main.id
      applicationInsights = azurerm_application_insights.main.id
      containerRegistry = azurerm_container_registry.main.id
      publicNetworkAccess = "Enabled"
    }
    kind = "Hub"
  })
}

# AI Services Account (for Azure OpenAI)
resource "azurerm_cognitive_account" "main" {
  name                = "cog-${var.project_name}-${var.environment}-${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  kind                = "AIServices"
  sku_name            = "S0"
  tags                = var.tags
}

# Azure OpenAI GPT-4o Deployment
resource "azurerm_cognitive_deployment" "gpt4o" {
  name                 = "gpt-4o-deployment"
  cognitive_account_id = azurerm_cognitive_account.main.id

  model {
    format  = "OpenAI"
    name    = var.gpt_model_name
    version = var.gpt_model_version
  }

  sku {
    name     = "Standard"
    capacity = var.gpt_deployment_capacity
  }
}

# AI Project
resource "azapi_resource" "ai_project" {
  type      = "Microsoft.MachineLearningServices/workspaces@2024-04-01"
  name      = "aip-${var.project_name}-${var.environment}-${random_string.suffix.result}"
  parent_id = azurerm_resource_group.main.id
  location  = azurerm_resource_group.main.location
  tags      = var.tags

  identity {
    type = "SystemAssigned"
  }

  body = jsonencode({
    properties = {
      description = "AI Foundry Project for ${var.project_name}"
      friendlyName = "AI Project ${var.project_name} ${var.environment}"
      kind = "Project"
      hubResourceId = azapi_resource.ai_hub.id
      publicNetworkAccess = "Enabled"
    }
    kind = "Project"
  })
}

# Connection to Azure OpenAI in AI Project
resource "azapi_resource" "openai_connection" {
  type      = "Microsoft.MachineLearningServices/workspaces/connections@2024-04-01"
  name      = "aoai-connection"
  parent_id = azapi_resource.ai_project.id

  body = jsonencode({
    properties = {
      category = "AzureOpenAI"
      target = azurerm_cognitive_account.main.endpoint
      authType = "AAD"
      isSharedToAll = true
      metadata = {
        ApiVersion = "2024-06-01"
        ResourceId = azurerm_cognitive_account.main.id
      }
    }
  })
}

# Connection to Azure AI Search in AI Project
resource "azapi_resource" "search_connection" {
  type      = "Microsoft.MachineLearningServices/workspaces/connections@2024-04-01"
  name      = "search-connection"
  parent_id = azapi_resource.ai_project.id

  body = jsonencode({
    properties = {
      category = "CognitiveSearch"
      target = "https://${azurerm_search_service.main.name}.search.windows.net"
      authType = "AAD"
      isSharedToAll = true
      metadata = {
        ApiVersion = "2024-05-01-preview"
        ResourceId = azurerm_search_service.main.id
      }
    }
  })
}

# Data source for current client config
data "azurerm_client_config" "current" {}
