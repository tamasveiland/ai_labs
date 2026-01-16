// Role Assignment for a single resource
param principalId string
param roleDefinitionId string
param principalType string = 'User'
param resourceId string

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceId, principalId, roleDefinitionId)
  scope: resourceGroup()
  properties: {
    principalId: principalId
    roleDefinitionId: roleDefinitionId
    principalType: principalType
  }
}
