// Main Bicep template for Lab06: Speech Conversation with Azure AI Foundry
targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the environment for resource naming')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string = 'swedencentral'

@description('Id of the principal to assign roles')
param principalId string = ''

// Optional parameters
@description('OpenAI model deployment name')
param openAiModelDeploymentName string = 'gpt-4o'

@description('OpenAI model name')
param openAiModelName string = 'gpt-4o'

@description('OpenAI model version')
param openAiModelVersion string = '2024-08-06'

@description('OpenAI model capacity (thousands of tokens per minute)')
param openAiModelCapacity int = 30

// Generate unique suffix for resource names
var abbrs = loadJsonContent('./abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var aiFoundryName = '${abbrs.cognitiveServicesAccounts}${resourceToken}'
var aiProjectName = '${aiFoundryName}-project'
var speechServiceName = '${abbrs.speechServicesAccounts}${resourceToken}'
var tags = {
  'azd-env-name': environmentName
  lab: 'lab06-speech-conversation'
  SecurityControl: 'Ignore'
}

// ============================================================================
// Resource Group
// ============================================================================

resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}

// ============================================================================
// AI Foundry + Project + GPT-4o Model
// ============================================================================

module aiProject './modules/ai-project.bicep' = {
  name: 'ai-project'
  scope: rg
  params: {
    aiFoundryName: aiFoundryName
    name: aiProjectName
    location: location
    tags: tags
    openAiModelDeploymentName: openAiModelDeploymentName
    openAiModelName: openAiModelName
    openAiModelVersion: openAiModelVersion
    openAiModelCapacity: openAiModelCapacity
    logAnalyticsWorkspaceId: logAnalytics.outputs.id
  }
}

// ============================================================================
// Azure Speech Service (STT/TTS)
// ============================================================================

module speech './modules/speech.bicep' = {
  name: 'speech-service'
  scope: rg
  params: {
    name: speechServiceName
    location: location
    tags: tags
    logAnalyticsWorkspaceId: logAnalytics.outputs.id
  }
}

// ============================================================================
// Log Analytics Workspace (monitoring)
// ============================================================================

module logAnalytics './modules/log-analytics.bicep' = {
  name: 'log-analytics'
  scope: rg
  params: {
    name: '${abbrs.operationalInsightsWorkspaces}${resourceToken}'
    location: location
    tags: tags
  }
}

// ============================================================================
// RBAC Role Assignments
// ============================================================================

// Cognitive Services OpenAI User - allows the developer to use OpenAI APIs
module openAiRoleAssignment './modules/role-assignment.bicep' = if (!empty(principalId)) {
  name: 'openai-role-assignment'
  scope: rg
  params: {
    principalId: principalId
    // Cognitive Services OpenAI User
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
    principalType: 'User'
  }
}

// Cognitive Services User - allows the developer to use Speech APIs
module speechRoleAssignment './modules/role-assignment.bicep' = if (!empty(principalId)) {
  name: 'speech-role-assignment'
  scope: rg
  params: {
    principalId: principalId
    // Cognitive Services User
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'a97b65f3-24c7-4388-baec-2e87135dc908')
    principalType: 'User'
  }
}

// ============================================================================
// Outputs (captured by azd as environment variables)
// ============================================================================

output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_SUBSCRIPTION_ID string = subscription().subscriptionId
output AZURE_RESOURCE_GROUP string = rg.name

// AI Foundry / OpenAI outputs
output AZURE_AI_PROJECT_NAME string = aiProject.outputs.name
output AZURE_OPENAI_ENDPOINT string = aiProject.outputs.openAiEndpoint
output AZURE_OPENAI_DEPLOYMENT_NAME string = openAiModelDeploymentName

// Speech Service outputs
output AZURE_SPEECH_ENDPOINT string = speech.outputs.endpoint
output AZURE_SPEECH_REGION string = speech.outputs.location
output AZURE_SPEECH_RESOURCE_NAME string = speech.outputs.name

#disable-next-line outputs-should-not-contain-secrets
output AZURE_SPEECH_KEY string = speech.outputs.key1

// Monitoring
output AZURE_LOG_ANALYTICS_NAME string = logAnalytics.outputs.name
