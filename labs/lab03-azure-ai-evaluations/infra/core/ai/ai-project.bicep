// Standalone Azure AI Foundry Project (no Hub required)

@description('AI Foundry name')
param aiFoundryName string

@description('Name of the AI Project')
param name string

@description('Location for the resource')
param location string = resourceGroup().location

// Optional parameters
@description('OpenAI model deployment name')
param openAiModelDeploymentName string = 'gpt-4o'

@description('OpenAI model name')
param openAiModelName string = 'gpt-4o'

@description('OpenAI model version')
param openAiModelVersion string = '2024-08-06'

@description('OpenAI model capacity (in thousands of tokens per minute)')
param openAiModelCapacity int = 30

/*
  An AI Foundry resources is a variant of a CognitiveServices/account resource type
*/ 
resource aiFoundry 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = {
  name: aiFoundryName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'S0'
  }
  kind: 'AIServices'
  properties: {
    // required to work in AI Foundry
    allowProjectManagement: true 

    // Defines developer API endpoint subdomain
    customSubDomainName: aiFoundryName

    // Enable public network access
    publicNetworkAccess: 'Enabled'

    disableLocalAuth: true
  }
}

/*
  Developer APIs are exposed via a project, which groups in- and outputs that relate to one use case, including files.
  Its advisable to create one project right away, so development teams can directly get started.
  Projects may be granted individual RBAC permissions and identities on top of what account provides.
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
  Optionally deploy a model to use in playground, agents and other tools.
*/
resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01'= {
  parent: aiFoundry
  name: openAiModelDeploymentName
  sku : {
    capacity: openAiModelCapacity
    name: 'GlobalStandard'
  }
  properties: {
    model:{
      name: openAiModelName
      format: 'OpenAI'
      version: openAiModelVersion
    }
  }
}

output id string = aiProject.id
output name string = aiProject.name
output principalId string = aiProject.identity.principalId
