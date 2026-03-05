// Azure Speech Service for STT/TTS capabilities

@description('Name of the Speech service')
param name string

@description('Location for the resource')
param location string = resourceGroup().location

@description('Tags for the resource')
param tags object = {}

@description('Log Analytics workspace resource ID for diagnostics (empty = no diagnostics)')
param logAnalyticsWorkspaceId string = ''

resource speechService 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: name
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'S0'
  }
  kind: 'SpeechServices'
  properties: {
    customSubDomainName: name
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: false // Allow key auth for local development
  }
}

// Diagnostic settings – send all logs & metrics to Log Analytics
resource diagnosticSettings 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (!empty(logAnalyticsWorkspaceId)) {
  name: '${speechService.name}-diag'
  scope: speechService
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

output id string = speechService.id
output name string = speechService.name
output endpoint string = speechService.properties.endpoint
output principalId string = speechService.identity.principalId
output location string = speechService.location

#disable-next-line outputs-should-not-contain-secrets
output key1 string = speechService.listKeys().key1
