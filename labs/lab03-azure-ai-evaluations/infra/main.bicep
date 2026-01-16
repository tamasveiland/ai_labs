// Main Bicep template for Azure AI Evaluations Lab
targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the environment for resource naming')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Id of the principal to assign roles')
param principalId string = ''

// Optional parameters
@description('OpenAI model deployment name')
param openAiModelDeploymentName string = 'gpt-4o'

@description('OpenAI model name')
param openAiModelName string = 'gpt-4o'

@description('OpenAI model version')
param openAiModelVersion string = '2024-08-06'

@description('OpenAI model capacity (in thousands of tokens per minute)')
param openAiModelCapacity int = 30

// Generate unique suffix for resource names
var abbrs = loadJsonContent('./abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var aiFoundryName = 'aif${resourceToken}'
var aiProjectName = '${aiFoundryName}-project'
var tags = {
  'azd-env-name': environmentName
  'lab': 'lab03-azure-ai-evaluations'
}

// Organize resources in a resource group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}



// Log Analytics Workspace
module logAnalytics './core/monitor/loganalytics.bicep' = {
  name: 'loganalytics'
  scope: rg
  params: {
    name: '${abbrs.operationalInsightsWorkspaces}${resourceToken}'
    location: location
    tags: tags
  }
}

// Application Insights
module appInsights './core/monitor/applicationinsights.bicep' = {
  name: 'appinsights'
  scope: rg
  params: {
    name: '${abbrs.insightsComponents}${resourceToken}'
    location: location
    tags: tags
    workspaceId: logAnalytics.outputs.id
  }
}

// Key Vault for AI Project
module keyVault './core/keyvault/keyvault.bicep' = {
  name: 'keyvault'
  scope: rg
  params: {
    name: '${abbrs.keyVaultVaults}${resourceToken}'
    location: location
    tags: tags
  }
}

// AI Foundry and Project
module aiProject './core/ai/ai-project.bicep' = {
  name: 'aiproject'
  scope: rg
  params: {
    aiFoundryName: aiFoundryName
    name: aiProjectName
    location: location
    openAiModelDeploymentName: openAiModelDeploymentName
    openAiModelName: openAiModelName
    openAiModelVersion: openAiModelVersion
    openAiModelCapacity: openAiModelCapacity
  }
}

// AI Search Service
module search './core/search/search-services.bicep' = {
  name: 'search'
  scope: rg
  params: {
    name: '${abbrs.searchSearchServices}${resourceToken}'
    location: location
    tags: tags
    sku: {
      name: 'basic'
    }
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
    semanticSearch: 'free'
  }
}

// Storage Account for documents
module storage './core/storage/storage-account.bicep' = {
  name: 'storage'
  scope: rg
  params: {
    name: '${abbrs.storageStorageAccounts}${resourceToken}'
    location: location
    tags: tags
    sku: {
      name: 'Standard_LRS'
    }
    containers: [
      {
        name: 'documents'
        publicAccess: 'None'
      }
    ]
  }
}

// Role assignments for the user
module userRoleAssignments './core/security/role-assignments.bicep' = if (!empty(principalId)) {
  name: 'user-role-assignments'
  scope: rg
  params: {
    principalId: principalId
    roles: [
      'Search Index Data Contributor'
      'Storage Blob Data Contributor'
    ]
    resourceIds: [
      search.outputs.id
      storage.outputs.id
    ]
  }
}

// Role assignment for AI Project to access Storage
module projectStorageRole './core/security/role-assignment.bicep' = {
  name: 'project-storage-role'
  scope: rg
  params: {
    principalId: aiProject.outputs.principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe') // Storage Blob Data Contributor
    principalType: 'ServicePrincipal'
    resourceId: storage.outputs.id
  }
}

// Role assignment for AI Project to access Key Vault
module projectKeyVaultRole './core/security/role-assignment.bicep' = {
  name: 'project-keyvault-role'
  scope: rg
  params: {
    principalId: aiProject.outputs.principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '00482a5a-887f-4fb3-b363-3b7fe8e74483') // Key Vault Administrator
    principalType: 'ServicePrincipal'
    resourceId: keyVault.outputs.id
  }
}

// Role assignment for Search Service to access Storage
module searchStorageRole './core/security/role-assignment.bicep' = {
  name: 'search-storage-role'
  scope: rg
  params: {
    principalId: search.outputs.principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1') // Storage Blob Data Reader
    principalType: 'ServicePrincipal'
    resourceId: storage.outputs.id
  }
}


// Outputs
output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_SUBSCRIPTION_ID string = subscription().subscriptionId
output AZURE_RESOURCE_GROUP string = rg.name

// AI Foundry outputs
output AZURE_AI_PROJECT_NAME string = aiProject.outputs.name

// Search outputs
output AZURE_SEARCH_ENDPOINT string = search.outputs.endpoint
output AZURE_SEARCH_NAME string = search.outputs.name

// Storage outputs
output AZURE_STORAGE_ACCOUNT_NAME string = storage.outputs.name
output AZURE_STORAGE_ENDPOINT string = storage.outputs.primaryEndpoints.blob

// Key Vault outputs
output AZURE_KEY_VAULT_NAME string = keyVault.outputs.name
output AZURE_KEY_VAULT_URI string = keyVault.outputs.vaultUri
