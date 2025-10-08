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
  value       = azurerm_cognitive_account.main.name
}

output "cognitive_account_endpoint" {
  description = "Endpoint of the Azure Cognitive Services account"
  value       = azurerm_cognitive_account.main.endpoint
}

output "gpt_deployment_name" {
  description = "Name of the GPT-4o deployment"
  value       = azurerm_cognitive_deployment.gpt4o.name
}

output "ai_hub_name" {
  description = "Name of the AI Hub"
  value       = azapi_resource.ai_hub.name
}

output "ai_project_name" {
  description = "Name of the AI Project"
  value       = azapi_resource.ai_project.name
}

output "key_vault_name" {
  description = "Name of the Key Vault"
  value       = azurerm_key_vault.main.name
}

output "application_insights_name" {
  description = "Name of Application Insights"
  value       = azurerm_application_insights.main.name
}

output "container_registry_name" {
  description = "Name of the Container Registry"
  value       = azurerm_container_registry.main.name
}

output "container_registry_login_server" {
  description = "Login server of the Container Registry"
  value       = azurerm_container_registry.main.login_server
}
