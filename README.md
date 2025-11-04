# Azure AI Model Capacity Dashboard

A professional web application for monitoring Azure AI Services model capacity across regions and SKU types. Built with Streamlit and following Azure best practices for enterprise deployments.

## Project Structure

```
model-availability-dashboard/
├── portal/                 # Frontend Streamlit Application
│   └── app.py             # Main dashboard application
├── src/                   # Backend Components
│   ├── __init__.py        # Package initialization
│   ├── azure_model_capacity_client.py  # Azure API client
│   └── usage_examples.py  # Example usage scripts
├── config.template.json   # Configuration template (secure)
├── requirements.txt       # Python dependencies
├── run_dashboard.py      # Dashboard launcher
├── start_dashboard.bat   # Windows launcher
├── .gitignore           # Security-focused ignore rules
└── README.md           # This file
```

## Features

### Professional Dashboard Interface
- **Tabbed SKU Interface**: Separate tabs for each capacity type (GlobalStandard, ProvisionedManaged, etc.)
- **Region-Centric View**: Rows for regions, columns for model versions
- **Professional Styling**: Clean blue/green color scheme without emojis
- **Dynamic Filtering**: Dropdown filters for regions and models per SKU type

### Capacity Visualization
- **Color-Coded Cells**: Green (high), yellow (medium), red (low), gray (none)
- **Real-Time Data**: 5-minute caching with manual refresh capability
- **Comprehensive Coverage**: All Azure regions and model versions

### Export Capabilities
- **Individual SKU CSV**: Download specific capacity type data
- **Individual SKU JSON**: Raw API data per capacity type
- **Comprehensive Excel**: All SKUs in separate sheets with summary

### Email Reporting
- **Professional Email Reports**: Send capacity reports via Azure Communication Service
- **HTML Formatted Tables**: Color-coded capacity data with professional styling
- **Flexible Recipients**: Configure default recipients or specify custom ones
- **Summary Statistics**: Include overview of total SKUs, regions, and models
- **Automated Scheduling**: Ready for integration with task schedulers

### Security & Best Practices
- **Secure Configuration**: Template-based config with gitignore protection
- **Azure Authentication**: DefaultAzureCredential with Azure CLI integration
- **Enterprise-Ready**: Professional styling suitable for business presentations

## Quick Start

### Prerequisites
- Python 3.8+ with pip
- Azure CLI installed and authenticated (`az login`)
- Access to Azure AI Services capacity API

### Installation

1. **Clone Repository**:
   ```bash
   git clone https://github.com/aishwaryaumachandran/model-availability-dashboard.git
   cd model-availability-dashboard
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Azure Settings**:
   ```bash
   cp config.template.json config.json
   # Edit config.json with your Azure subscription details
   ```

4. **Launch Dashboard**:
   ```bash
   python run_dashboard.py
   ```

5. **Access Dashboard**: Open http://localhost:8501 in your browser

### Windows Users
Double-click `start_dashboard.bat` for one-click launch.

## Configuration

Edit `config.json` with your Azure details:

```json
{
  "subscription_id": "YOUR_SUBSCRIPTION_ID",
  "subscription_name": "YOUR_SUBSCRIPTION_NAME",
  "models": {
    "gpt-4o": {"version": "2024-05-13"},
    "o4-mini": {"version": "2025-04-16"},
    "o3-mini": {"version": "2025-01-31"}
  }
}
```

### Email Configuration (Optional)
For email reporting functionality, add email settings to `config.json`:

```json
{
  "email": {
    "connection_string": "endpoint=https://your-service.communication.azure.com/;accesskey=your-key",
    "sender_email": "donotreply@your-domain.azurecomm.net",
    "default_recipients": [
      "admin@company.com",
      "team@company.com"
    ],
    "subject_prefix": "[Azure Model Capacity]"
  }
}
```

**Email Setup Steps:**
1. Create Azure Communication Service resource
2. Configure and verify email domain
3. Get connection string from Azure portal
4. Update config.json with email settings
5. See `EMAIL_SETUP.md` for detailed instructions

## Usage

### Dashboard Navigation
1. **Select SKU Tab**: Choose capacity type (GlobalStandard, ProvisionedManaged, etc.)
2. **Apply Filters**: Use dropdowns to filter regions and models
3. **Analyze Capacity**: View color-coded capacity matrix
4. **Export Data**: Download CSV, JSON, or comprehensive Excel file
5. **Send Email Report**: Use the email section to send formatted reports

### Email Reporting
1. **Navigate to Email Section**: Scroll to bottom of dashboard
2. **Add Recipients**: Enter email addresses (one per line) or use defaults
3. **Preview Content**: Expand "Preview Email Content" to see what will be sent
4. **Send Report**: Click "Send Email Report" button
5. **Professional Format**: Recipients receive HTML-formatted tables with color coding

### Capacity Types (SKUs)
- **GlobalStandard**: Pay-per-token global capacity
- **GlobalProvisionedManaged**: Reserved global capacity
- **ProvisionedManaged**: Reserved regional capacity  
- **GlobalBatch**: Batch processing capacity
- **Standard**: Regional pay-per-token capacity
- **DataZone**: Data residency compliant capacity

### Color Coding
- **Green**: High capacity (≥1,000 units)
- **Yellow**: Medium capacity (100-999 units)
- **Red**: Low capacity (1-99 units)
- **Gray**: No capacity available

## Development

### Project Architecture
- **Portal Layer** (`portal/`): Streamlit web interface
- **Service Layer** (`src/`): Azure API client and business logic
- **Configuration**: Template-based secure configuration
- **Launchers**: Cross-platform startup scripts

### Adding New Features
1. Backend logic goes in `src/`
2. UI components go in `portal/app.py`
3. Update requirements.txt for new dependencies
4. Follow the existing code style and security practices

### Security Considerations
- Never commit `config.json` or `*.log` files
- Use the configuration template for sharing
- All sensitive data is automatically gitignored
- Follow principle of least privilege for Azure permissions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following the project structure
4. Test thoroughly with real Azure data
5. Submit a pull request

## 🆘 Support

For issues and questions:
1. Check existing GitHub Issues
2. Create a new issue with detailed description
3. Include relevant log excerpts (remove sensitive data)

## 🏢 Enterprise Usage

This dashboard is designed for enterprise environments:
- Professional styling suitable for executive presentations
- Secure configuration management
- Comprehensive export capabilities for reporting
- Real-time capacity monitoring for planning and deployment decisions

---
