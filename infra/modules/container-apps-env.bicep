@description('Name of the Container Apps environment')
param name string

@description('Location for the environment')
param location string

@description('Tags for the resource')
param tags object = {}

resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
  }
}

output id string = env.id
output name string = env.name
