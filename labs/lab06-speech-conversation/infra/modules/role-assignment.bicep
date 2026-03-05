// Role Assignment at resource group scope
@description('Principal ID to assign the role to')
param principalId string

@description('Role definition ID')
param roleDefinitionId string

@description('Principal type (User, ServicePrincipal, Group)')
param principalType string = 'User'

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, principalId, roleDefinitionId)
  properties: {
    principalId: principalId
    roleDefinitionId: roleDefinitionId
    principalType: principalType
  }
}
