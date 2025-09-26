# Azure AI Services Model Capacity Client

A comprehensive solution for monitoring Azure AI Services Model Capacities, featuring both a Python client library and an interactive web dashboard.

## 🌟 Features

### Python Client Library
- **Secure Authentication**: Uses Azure DefaultAzureCredential (Managed Identity) following Azure best practices
- **Configuration-Driven**: JSON configuration file for easy management of models and settings
- **Retry Logic**: Exponential backoff for transient failures
- **Comprehensive Error Handling**: Detailed logging and error reporting
- **Connection Pooling**: Optimized HTTP requests with connection reuse
- **Multiple Model Support**: Query capacity for multiple models simultaneously

### Web Dashboard (NEW!)
- **Interactive Table View**: Models as rows, regions as columns with capacity numbers
- **Real-time Data**: Live capacity monitoring with auto-refresh
- **Color-coded Visualization**: Green (high), Yellow (medium), Red (low), Gray (N/A)
- **Filtering & Search**: Filter by model type, region, and capacity level
- **Export Capabilities**: Download data as CSV or JSON
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Summary Metrics**: Overview cards showing total models, regions, and capacity

## 📊 Dashboard Preview

The Streamlit dashboard provides an intuitive interface showing:
- **Model Table**: Each row is a model (e.g., GPT-4o, O3-mini), columns are regions
- **Capacity Values**: Actual numbers where available, "NA" where not supported
- **Color Coding**: Instant visual feedback on capacity levels
- **Interactive Charts**: Capacity overview and regional distribution
- **Export Options**: Download filtered data for analysis

## Prerequisites

1. **Azure Subscription**: Valid Azure subscription with AI Services access
2. **Authentication**: One of the following:
   - Azure CLI authentication (`az login`)
   - Managed Identity (when running in Azure)
   - Service Principal with environment variables
   - Visual Studio Code authentication

## Installation

1. **Clone or download** the project files
2. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

## Configuration

Update `config.json` with your Azure details:

```json
{
  "azure": {
    "subscription_name": "Your-Subscription-Name",
    "subscription_id": "your-subscription-id-guid",
    "api_version": "2024-04-01-preview",
    "base_url": "https://management.azure.com"
  },
  "models": {
    "gpt-4o": {
      "model_format": "OpenAI",
      "model_name": "gpt-4o",
      "model_version": "2024-05-13"
    },
    "o3": {
      "model_format": "OpenAI", 
      "model_name": "o3",
      "model_version": "2025-01-31"
    },
    "o4": {
      "model_format": "OpenAI",
      "model_name": "o4",
      "model_version": "2025-01-31"
    }
  }
}
```

- **Model versions**: Update model versions as needed based on available versions

## Usage

### 🖥️ Web Dashboard (Recommended)

Launch the interactive web dashboard:

```powershell
# Method 1: Using the runner script (recommended)
python run_dashboard.py

# Method 2: Direct Streamlit command
streamlit run streamlit_app.py
```

The dashboard will automatically:
- Open in your default web browser at `http://localhost:8501`
- Load capacity data from your Azure subscription
- Display an interactive table with models and regions
- Provide filtering, sorting, and export capabilities

### 🔧 Command Line Interface

For programmatic access or automation:

```powershell
# Run the basic client
python azure_model_capacity_client.py

# Or run examples
python usage_examples.py
```

### 📊 Dashboard Features

#### Main Table View
- **Rows**: Each model (GPT-4o, O3-mini, O4-mini, etc.)
- **Columns**: Azure regions (East US, West Europe, etc.)
- **Values**: Available capacity numbers or "NA" if not supported

#### Color Coding
- 🟢 **Green (≥1,000)**: High capacity available
- 🟡 **Yellow (100-999)**: Medium capacity available
- 🔴 **Red (1-99)**: Low capacity available
- ⚪ **Gray (NA)**: Not available in this region

#### Interactive Features
- **Auto-refresh**: Optional 5-minute automatic data updates
- **Filtering**: Show/hide models without capacity
- **Region Focus**: Filter by US, Europe, or Asia regions
- **Export**: Download as CSV or JSON
- **Metrics**: Summary cards showing totals and status

### 🐍 Programmatic Usage

```python
from azure_model_capacity_client import AzureModelCapacityClient

# Initialize client
with AzureModelCapacityClient("config.json") as client:
    # Query specific model
    gpt4o_results = client.get_model_capacity("gpt-4o")
    
    # Query all models
    all_results = client.get_all_models_capacity()
    
    # Print formatted report
    client.print_capacity_report(all_results)
```

## 🚀 Quick Start

### Option 1: Web Dashboard (Recommended)
```powershell
# Double-click to run
start_dashboard.bat

# Or run via Python
python run_dashboard.py
```

### Option 2: Command Line
```powershell
python azure_model_capacity_client.py
```

## 📊 Dashboard Interface

The web dashboard provides a comprehensive view of your Azure AI model capacity:

### Main Features:
1. **📈 Summary Metrics**: Total models, working models, restricted models, available regions
2. **📊 Visual Charts**: Capacity overview and regional distribution graphs  
3. **📋 Interactive Table**: 
   - **Rows**: Model names and versions (GPT-4o, O3-mini, O4-mini, etc.)
   - **Columns**: Azure regions (eastus, westeurope, australiaeast, etc.)
   - **Values**: Available capacity numbers or "NA" for unsupported regions
4. **🎨 Color Coding**:
   - 🟢 Green: High capacity (≥1,000 units)
   - 🟡 Yellow: Medium capacity (100-999 units)
   - 🔴 Red: Low capacity (1-99 units)
   - ⚪ Gray: Not available (NA)
5. **🔍 Filtering Options**:
   - Show/hide models without capacity
   - Filter by geographic regions (US, Europe, Asia)
   - Auto-refresh every 5 minutes
6. **📥 Export Features**:
   - Download as CSV for spreadsheet analysis
   - Download as JSON for programmatic use

### Example Dashboard View:
```
Model      Version     Total_Regions  eastus  westus  eastus2  westeurope  japaneast
GPT-4o     2024-05-13  132           450     150     150      450         450
O4-mini    2025-04-16  93            1000    1000    NA       NA          1000  
O3-mini    2025-01-31  112           500     500     300      500         500
O3         2025-04-16  0             NA      NA      NA       NA          NA
```

### 🌟 Key Benefits:
- **At-a-glance Overview**: See all model capacity across regions instantly
- **Real-time Data**: Always current capacity information
- **Decision Support**: Choose optimal regions for deployments
- **Export Ready**: Download data for reports or analysis
- **Professional UI**: Clean, modern interface suitable for stakeholders

## 🔐 Authentication Setup

### Option 1: Azure CLI (Recommended for Development)
```powershell
az login
az account set --subscription "your-subscription-id"
```

### Option 2: Service Principal (CI/CD)
Set environment variables:
```powershell
$env:AZURE_CLIENT_ID="your-client-id"
$env:AZURE_CLIENT_SECRET="your-client-secret" 
$env:AZURE_TENANT_ID="your-tenant-id"
```

### Option 3: Managed Identity (Azure-hosted)
No additional setup required when running in Azure with Managed Identity enabled.

## 🎯 API Endpoint Reference

This application queries the Azure AI Services Model Capacities API:
- **Endpoint**: `https://management.azure.com/subscriptions/{subscriptionId}/providers/Microsoft.CognitiveServices/modelCapacities`
- **Documentation**: [Model Capacities - List API](https://learn.microsoft.com/en-us/rest/api/aiservices/accountmanagement/model-capacities/list?view=rest-aiservices-accountmanagement-2024-04-01-preview)

## Output

The client provides:
1. **Console Output**: Formatted capacity report showing available capacity by region
2. **Log File**: Detailed logging in `azure_model_capacity.log`
3. **JSON Export**: Results saved to `model_capacity_results.json`

### Sample Output
```
Azure AI Services Model Capacity Report
=====================================

Model: GPT-4O
--------------
  Location: East US
  SKU: Standard
  Available Capacity: 300
  Available Finetune Capacity: 20
  Model Format: OpenAI
  Model Version: 2024-05-13
```

## Error Handling

The client handles various error scenarios:
- **Authentication failures**: Clear error messages with resolution steps
- **Network issues**: Retry logic with exponential backoff
- **API rate limiting**: Automatic retry with appropriate delays
- **Configuration errors**: Validation and helpful error messages

## Security Best Practices

This implementation follows Azure security best practices:
- ✅ Uses DefaultAzureCredential (no hardcoded secrets)
- ✅ Supports Managed Identity for Azure-hosted applications
- ✅ Implements proper token refresh
- ✅ Uses HTTPS for all communications
- ✅ Includes comprehensive logging for audit trails

## Troubleshooting

### Authentication Issues
```
Error: Authentication failed
```
**Solution**: Ensure you're authenticated with Azure:
- Run `az login`
- Verify subscription access with `az account show`

### Configuration Issues
```
Error: Missing or empty Azure configuration field: subscription_id
```
**Solution**: Update `config.json` with your Azure subscription details

### API Permission Issues
```
Error: 403 Forbidden
```
**Solution**: Ensure your account has proper permissions:
- Reader access on the subscription
- Cognitive Services permissions

### Network Issues
```
Error: Connection error after all retry attempts
```
**Solution**: Check network connectivity and firewall settings

## Model Versions

Update model versions in `config.json` based on available versions:
- Check Azure OpenAI Studio for latest GPT-4o versions
- Verify o3 and o4 model availability in your region
- Update version strings as new models are released

## Dependencies

- **azure-identity**: Azure authentication library
- **requests**: HTTP client library
- **azure-core**: Azure SDK core functionality

## License

This code is provided as-is for educational and development purposes.