// Role Assignments for multiple resources
param principalId string
param roles array
param resourceIds array

var roleDefinitions = {
  'Cognitive Services OpenAI User': '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
  'Search Index Data Contributor': '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
  'Storage Blob Data Contributor': 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
  'Storage Blob Data Reader': '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'
}

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for (role, i) in roles: {
  name: guid(principalId, role, resourceIds[i])
  properties: {
    principalId: principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleDefinitions[role])
    principalType: 'User'
  }
}]
