@description('The name of the App Service')
param name string

@description('The location for the App Service')
param location string = resourceGroup().location

@description('The ID of the App Service Plan')
param appServicePlanId string

@description('Tags to apply to the resource')
param tags object = {}

@description('Application Insights connection string')
param applicationInsightsConnectionString string = ''

@description('Enable managed identity')
param enableManagedIdentity bool = true

resource appService 'Microsoft.Web/sites@2023-01-01' = {
  name: name
  location: location
  tags: union(tags, { 'azd-service-name': 'agent-tools-api' })
  kind: 'app,linux'
  identity: enableManagedIdentity ? {
    type: 'SystemAssigned'
  } : null
  properties: {
    serverFarmId: appServicePlanId
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'DOTNETCORE|8.0'
      alwaysOn: true
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      http20Enabled: true
      appSettings: !empty(applicationInsightsConnectionString) ? [
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: applicationInsightsConnectionString
        }
        {
          name: 'ApplicationInsightsAgent_EXTENSION_VERSION'
          value: '~3'
        }
      ] : []
      cors: {
        allowedOrigins: [
          '*'
        ]
      }
    }
  }
}

output id string = appService.id
output name string = appService.name
output uri string = 'https://${appService.properties.defaultHostName}'
output principalId string = enableManagedIdentity ? appService.identity.principalId : ''
