// Standalone Azure AI Foundry Project with OpenAI model deployment

@description('AI Foundry resource name')
param aiFoundryName string

@description('Name of the AI Project')
param name string

@description('Location for the resource')
param location string = resourceGroup().location

@description('Tags for the resource')
param tags object = {}

@description('OpenAI model deployment name')
param openAiModelDeploymentName string = 'gpt-4o'

@description('OpenAI model name')
param openAiModelName string = 'gpt-4o'

@description('OpenAI model version')
param openAiModelVersion string = '2024-08-06'

@description('OpenAI model capacity (thousands of tokens per minute)')
param openAiModelCapacity int = 30

@description('Log Analytics workspace resource ID for diagnostics (empty = no diagnostics)')
param logAnalyticsWorkspaceId string = ''

/*
  AI Foundry resource - a CognitiveServices/account with kind=AIServices.
  This provides access to OpenAI models and other AI capabilities.
*/
resource aiFoundry 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = {
  name: aiFoundryName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'S0'
  }
  kind: 'AIServices'
  properties: {
    allowProjectManagement: true
    customSubDomainName: aiFoundryName
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: false
  }
}

/*
  AI Foundry Project - groups resources for a specific use case.
  Child resource of the AI Foundry account.
*/
resource aiProject 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = {
  name: name
  parent: aiFoundry
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {}
}

/*
  GPT-4o model deployment for the conversational agent.
*/
resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: aiFoundry
  name: openAiModelDeploymentName
  sku: {
    capacity: openAiModelCapacity
    name: 'GlobalStandard'
  }
  properties: {
    model: {
      name: openAiModelName
      format: 'OpenAI'
      version: openAiModelVersion
    }
  }
}

// Diagnostic settings – send all logs & metrics to Log Analytics
resource diagnosticSettings 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (!empty(logAnalyticsWorkspaceId)) {
  name: '${aiFoundry.name}-diag'
  scope: aiFoundry
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

output id string = aiProject.id
output name string = aiProject.name
output principalId string = aiProject.identity.principalId
output aiFoundryId string = aiFoundry.id
output aiFoundryName string = aiFoundry.name
output aiFoundryEndpoint string = aiFoundry.properties.endpoint
output openAiEndpoint string = 'https://${aiFoundryName}.openai.azure.com/'
