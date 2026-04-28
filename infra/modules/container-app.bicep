@description('Name of the Container App')
param name string

@description('Location for the Container App')
param location string

@description('Tags for the resource')
param tags object = {}

@description('Container Apps Environment ID')
param containerAppsEnvironmentId string

@description('ACR name for credentials')
param acrName string

@description('ACR login server')
param acrLoginServer string

@description('Target port for the container')
param targetPort int = 8501

@description('Subscription ID to query model capacities')
param modelCapacitySubscriptionId string

@description('Container image to deploy')
param imageName string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: acrName
}

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  tags: union(tags, { 'azd-service-name': 'dashboard' })
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironmentId
    workloadProfileName: 'Consumption'
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: targetPort
        transport: 'auto'
        allowInsecure: false
      }
      registries: [
        {
          server: acrLoginServer
          username: acr.listCredentials().username
          passwordSecretRef: 'acr-password'
        }
      ]
      secrets: [
        {
          name: 'acr-password'
          value: acr.listCredentials().passwords[0].value
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'dashboard'
          image: imageName
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 1
      }
    }
  }
}

// Assign "Cognitive Services User" role to the managed identity on the subscription
// This allows the dashboard to query model capacity data
var cognitiveServicesUserRoleId = 'a97b65f3-24c7-4388-baec-2e87135dc908'

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(app.id, cognitiveServicesUserRoleId, modelCapacitySubscriptionId)
  properties: {
    principalId: app.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesUserRoleId)
  }
}

output name string = app.name
output fqdn string = app.properties.configuration.ingress.fqdn
output id string = app.id
output principalId string = app.identity.principalId
