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

  # Disable shared key access for better security (required by organization policy)
  shared_access_key_enabled = false

  tags                     = var.tags
}

# Create a Blob container in the storage account
resource "azurerm_storage_container" "main" {
  name                  = "mylogs"
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = "private"
}

# Azure AI Search, enabled with system-assigned identity
# Enabling RBAC access control for the Search service
resource "azurerm_search_service" "main" {
  name                = "search-${var.project_name}-${var.environment}-${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.search_sku
  tags                = var.tags

  identity {
    type = "SystemAssigned"
  }

  # Enable RBAC for data plane operations
  local_authentication_enabled = true
  authentication_failure_mode  = "http401WithBearerChallenge"
}

# # AI Services Account (for Azure OpenAI)
# resource "azurerm_cognitive_account" "main" {
#   name                = "cog-${var.project_name}-${var.environment}-${random_string.suffix.result}"
#   resource_group_name = azurerm_resource_group.main.name
#   location            = azurerm_resource_group.main.location
#   kind                = "AIServices"
#   sku_name            = "S0"
#   tags                = var.tags
# }

## Create the AI Foundry resource
##
resource "azapi_resource" "ai_foundry" {
  type                      = "Microsoft.CognitiveServices/accounts@2025-06-01"
  name                      = "aif-${var.project_name}-${var.environment}-${random_string.suffix.result}"
  parent_id                 = azurerm_resource_group.main.id
  location                  = azurerm_resource_group.main.location
  schema_validation_enabled = false

  body = {
    kind = "AIServices"
    sku = {
      name = "S0"
    }
    identity = {
      type = "SystemAssigned"
    }

    properties = {
      # Support both Entra ID and API Key authentication for Cognitive Services account
      disableLocalAuth = false

      # Specifies that this is an AI Foundry resourceyes
      allowProjectManagement = true

      # Set custom subdomain name for DNS names created for this Foundry resource
      customSubDomainName = "aifoundry${random_string.suffix.result}"
    }
    tags = var.tags
  }
}

## Create AI Foundry project
##
resource "azapi_resource" "ai_foundry_project" {
  type                      = "Microsoft.CognitiveServices/accounts/projects@2025-06-01"
  name                      = "pr-${var.project_name}-${var.environment}-${random_string.suffix.result}"
  parent_id                 = azapi_resource.ai_foundry.id
  location                  = var.location
  schema_validation_enabled = false

  body = {
    sku = {
      name = "S0"
    }
    identity = {
      type = "SystemAssigned"
    }

    properties = {
      displayName = "byod-demo"
      description = "Project for BYOD demo"
    }
  }
}

# Azure OpenAI GPT-4o Deployment
resource "azurerm_cognitive_deployment" "gpt4o" {
  name                 = "gpt-4o-deployment"
  cognitive_account_id = azapi_resource.ai_foundry.id

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

# Azure text-embedding-3-small Deployment
resource "azurerm_cognitive_deployment" "text_embedding" {
  name                 = "text-embedding-3-small-deployment"
  cognitive_account_id = azapi_resource.ai_foundry.id

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

# Azure OpenAI instance
resource "azurerm_cognitive_account" "openai" {
  name                = "oai-${var.project_name}-${var.environment}-${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.main.name 
  location            = azurerm_resource_group.main.location
  kind                = "OpenAI"
  sku_name            = "S0"
  custom_subdomain_name = "oai-${var.project_name}-${var.environment}-${random_string.suffix.result}"
  tags                = var.tags
}

# Azure OpenAI text-embedding-3-small Deployment
resource "azurerm_cognitive_deployment" "openai_text_embedding_small" {
  name                 = "text-embedding-3-small-deployment"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "text-embedding-3-small"
    version = "1"
  }

  sku {
    name     = "GlobalStandard"
    capacity = var.embedding_deployment_capacity
  }
}

# # Create connection from AI Foundry Project to Azure OpenAI
# resource "azapi_resource" "openai_connection" {
#   type      = "Microsoft.MachineLearningServices/workspaces/connections@2024-04-01"
#   name      = "openai-connection"
#   parent_id = azapi_resource.ai_foundry_project.id

#   body = jsonencode({
#     properties = {
#       category = "AzureOpenAI"
#       target = azurerm_cognitive_account.openai.id
#       authType = "AAD"
#       isSharedToAll = true
#       metadata = {
#         ApiVersion = "2024-05-01-preview"
#         ResourceId = azurerm_cognitive_account.openai.id
#       }
#     }
#   })
# }


  
  
# # Connection to Azure AI Search in AI Project
# resource "azapi_resource" "search_connection" {
#   type      = "Microsoft.MachineLearningServices/workspaces/connections@2024-04-01"
#   name      = "search-connection"
#   parent_id = azapi_resource.ai_project.id

#   body = jsonencode({
#     properties = {
#       category = "CognitiveSearch"
#       target = "https://${azurerm_search_service.main.name}.search.windows.net"
#       authType = "AAD"
#       isSharedToAll = true
#       metadata = {
#         ApiVersion = "2024-05-01-preview"
#         ResourceId = azurerm_search_service.main.id
#       }
#     }
#   })
# }

# Data source for current client config
data "azurerm_client_config" "current" {}
