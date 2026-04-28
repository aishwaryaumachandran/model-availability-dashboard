targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the environment (e.g., dev, prod)')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Azure subscription ID to query model capacities for')
param modelCapacitySubscriptionId string = ''

var abbrs = loadJsonContent('./abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = { 'azd-env-name': environmentName }

resource rg 'Microsoft.Resources/resourceGroups@2022-09-01' = {
  name: '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}

module acr './modules/acr.bicep' = {
  name: 'acr'
  scope: rg
  params: {
    name: '${abbrs.containerRegistryRegistries}${resourceToken}'
    location: location
    tags: tags
  }
}

module containerAppsEnv './modules/container-apps-env.bicep' = {
  name: 'container-apps-env'
  scope: rg
  params: {
    name: '${abbrs.appManagedEnvironments}${resourceToken}'
    location: location
    tags: tags
  }
}

module dashboard './modules/container-app.bicep' = {
  name: 'dashboard'
  scope: rg
  params: {
    name: '${abbrs.appContainerApps}dashboard-${resourceToken}'
    location: location
    tags: tags
    containerAppsEnvironmentId: containerAppsEnv.outputs.id
    acrName: acr.outputs.name
    acrLoginServer: acr.outputs.loginServer
    targetPort: 8501
    modelCapacitySubscriptionId: modelCapacitySubscriptionId != '' ? modelCapacitySubscriptionId : subscription().subscriptionId
  }
}

output AZURE_CONTAINER_REGISTRY_ENDPOINT string = acr.outputs.loginServer
output AZURE_CONTAINER_REGISTRY_NAME string = acr.outputs.name
output AZURE_CONTAINER_APP_FQDN string = dashboard.outputs.fqdn
output AZURE_CONTAINER_APP_URL string = 'https://${dashboard.outputs.fqdn}'
output SERVICE_DASHBOARD_NAME string = dashboard.outputs.name
