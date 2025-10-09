# Role assignments for RBAC access to Azure AI Search

# Assign Search Service Contributor role to AI Foundry service for managing search service resources
resource "azurerm_role_assignment" "ai_foundry_search_service_contributor" {
  scope                = azurerm_search_service.main.id
  role_definition_name = "Search Service Contributor"
  principal_id         = azapi_resource.ai_foundry.output.identity.principalId
}

# Assign Search Index Data Reader role to AI Foundry service for search/query operations
resource "azurerm_role_assignment" "ai_foundry_search_index_data_reader" {
  scope                = azurerm_search_service.main.id
  role_definition_name = "Search Index Data Reader"
  principal_id         = azapi_resource.ai_foundry.output.identity.principalId
}

# # Assign Search Service Contributor role to AI Foundry Project for managing search service resources
# resource "azurerm_role_assignment" "ai_foundry_project_search_service_contributor" {
#   scope                = azurerm_search_service.main.id
#   role_definition_name = "Search Service Contributor"
#   principal_id         = jsondecode(azapi_resource.ai_foundry_project.output).identity.principalId
# }

# # Assign Search Index Data Contributor role to AI Foundry Project for indexing operations
# resource "azurerm_role_assignment" "ai_foundry_project_search_index_data_contributor" {
#   scope                = azurerm_search_service.main.id
#   role_definition_name = "Search Index Data Contributor"
#   principal_id         = jsondecode(azapi_resource.ai_foundry_project.output).identity.principalId
# }

# # Assign Search Index Data Reader role to AI Foundry Project for search/query operations
# resource "azurerm_role_assignment" "ai_foundry_project_search_index_data_reader" {
#   scope                = azurerm_search_service.main.id
#   role_definition_name = "Search Index Data Reader"
#   principal_id         = jsondecode(azapi_resource.ai_foundry_project.output).identity.principalId
# }

# Add role assignments for storage account
# Assign Storage Blob Data Reader for Search service to read from storage account
resource "azurerm_role_assignment" "search_service_storage_blob_data_reader" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = azurerm_search_service.main.identity[0].principal_id
}

# Add role assignments for Azure AI Foundry
# Assign Cognitive Services OpenAI User for AI Search service to access OpenAI models
resource "azurerm_role_assignment" "ai_foundry_cognitive_services_openai_user" {
  scope                = azurerm_cognitive_account.openai.id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = azurerm_search_service.main.identity[0].principal_id
}

# Add role assignments for Azure OpenAI
# Assign Cognitive Services OpenAI User for Search service to access OpenAI models
resource "azurerm_role_assignment" "search_service_cognitive_services_openai_user" {
  scope                = azapi_resource.ai_foundry.id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = azurerm_search_service.main.identity[0].principal_id
}

### Current user ###
# Assign current user as Search Service Contributor for full administrative access
resource "azurerm_role_assignment" "current_user_search_service_contributor" {
  scope                = azurerm_search_service.main.id
  role_definition_name = "Search Service Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Assign current user as Search Index Data Reader for search/query operations
resource "azurerm_role_assignment" "current_user_search_index_data_reader" {
  scope                = azurerm_search_service.main.id
  role_definition_name = "Search Index Data Reader"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Assign current user as Storage Blob Data Contributor for read/write access to storage account
resource "azurerm_role_assignment" "current_user_storage_blob_data_contributor" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Additional role assignments for indexing and AI enrichment

# Allow Search service to write to Storage for Knowledge Store
resource "azurerm_role_assignment" "search_service_storage_blob_data_contributor" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_search_service.main.identity[0].principal_id
}

# Allow Search service to read from Storage Tables for Knowledge Store
resource "azurerm_role_assignment" "search_service_storage_table_data_contributor" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Table Data Contributor"
  principal_id         = azurerm_search_service.main.identity[0].principal_id
}

# Allow current user Search Index Data Contributor role for managing index content
resource "azurerm_role_assignment" "current_user_search_index_data_contributor" {
  scope                = azurerm_search_service.main.id
  role_definition_name = "Search Index Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}

