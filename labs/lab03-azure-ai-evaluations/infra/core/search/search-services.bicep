// Azure AI Search Service
param name string
param location string = resourceGroup().location
param tags object = {}

param sku object = {
  name: 'basic'
}

param authOptions object = {}
param semanticSearch string = 'free'

resource search 'Microsoft.Search/searchServices@2023-11-01' = {
  name: name
  location: location
  tags: tags
  sku: sku
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    authOptions: authOptions
    disableLocalAuth: false
    encryptionWithCmk: {
      enforcement: 'Unspecified'
    }
    hostingMode: 'default'
    partitionCount: 1
    publicNetworkAccess: 'enabled'
    replicaCount: 1
    semanticSearch: semanticSearch
  }
}

output endpoint string = 'https://${name}.search.windows.net'
output id string = search.id
output name string = search.name
output principalId string = search.identity.principalId
