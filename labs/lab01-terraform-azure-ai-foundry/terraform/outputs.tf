output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "storage_account_name" {
  description = "Name of the storage account"
  value       = azurerm_storage_account.main.name
}

output "search_service_name" {
  description = "Name of the Azure AI Search service"
  value       = azurerm_search_service.main.name
}

output "search_service_endpoint" {
  description = "Endpoint of the Azure AI Search service"
  value       = "https://${azurerm_search_service.main.name}.search.windows.net"
}

output "cognitive_account_name" {
  description = "Name of the Azure Cognitive Services account"
  value       = azapi_resource.ai_foundry.name
}

# output "cognitive_account_endpoint" {
#   description = "Endpoint of the Azure Cognitive Services account"
#   value       = azapi_resource.ai_foundry_project.properties.endpoint
# }

output "gpt_deployment_name" {
  description = "Name of the GPT-4o deployment"
  value       = azurerm_cognitive_deployment.gpt4o.name
}

# Managed Identity Outputs
output "search_service_identity_principal_id" {
  description = "Principal ID of the Azure AI Search service system-assigned managed identity"
  value       = azurerm_search_service.main.identity[0].principal_id
}

output "search_service_identity_tenant_id" {
  description = "Tenant ID of the Azure AI Search service system-assigned managed identity"
  value       = azurerm_search_service.main.identity[0].tenant_id
}

output "ai_foundry_identity_principal_id" {
  description = "Principal ID of the Azure AI Foundry system-assigned managed identity"
  value       = azapi_resource.ai_foundry.output.identity.principalId
}

output "ai_foundry_project_identity_principal_id" {
  description = "Principal ID of the Azure AI Foundry Project system-assigned managed identity"
  value       = azapi_resource.ai_foundry_project.output.identity.principalId
}

