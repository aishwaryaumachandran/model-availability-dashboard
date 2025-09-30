# Azure Communication Service Email Setup Guide

## Overview
This guide explains how to set up Azure Communication Service for email functionality in the Model Capacity Dashboard.

## Prerequisites
1. Azure subscription with active Azure Communication Service resource
2. Email domain configured and verified in Azure Communication Service
3. Sender email address configured

## Setup Steps

### 1. Create Azure Communication Service Resource
```bash
# Using Azure CLI
az communication create \
  --name "your-communication-service" \
  --resource-group "your-resource-group" \
  --location "global"
```

### 2. Configure Email Domain
1. Go to Azure Portal → Communication Services → Your service
2. Navigate to "Email" → "Provision domains"
3. Either:
   - Use Azure managed domain (free tier): `your-subdomain.azurecomm.net`
   - Connect your custom domain (requires DNS verification)

### 3. Get Connection String
1. In Azure Portal → Communication Services → Your service
2. Go to "Keys" in the left menu
3. Copy the "Primary connection string"

### 4. Update Configuration
Update your `config.json` file with email settings:

```json
{
  "email": {
    "connection_string": "endpoint=https://your-service.communication.azure.com/;accesskey=your-access-key",
    "sender_email": "donotreply@your-subdomain.azurecomm.net",
    "default_recipients": [
      "admin@yourcompany.com",
      "team@yourcompany.com"
    ],
    "subject_prefix": "[Azure Model Capacity]"
  }
}
```

### 5. Test Email Functionality
1. Run the dashboard: `streamlit run portal/app.py`
2. Navigate to the "Email Report" section at the bottom
3. Add test recipient emails or use defaults
4. Click "Send Email Report"

## Email Features

### What's Included in the Email
- **Summary Statistics**: Total SKUs, regions, and models
- **Color-coded Tables**: Capacity data for each SKU type
  - Green: High capacity (≥1,000 units)
  - Yellow: Medium capacity (100-999 units)
  - Red: Low capacity (1-99 units)
  - Gray: No capacity (0 units)
- **Professional HTML Formatting**: Clean, readable layout
- **Timestamp**: When the report was generated

### Email Configuration Options
- `connection_string`: Azure Communication Service connection string
- `sender_email`: Must be from verified domain
- `default_recipients`: List of default email addresses
- `subject_prefix`: Prefix for email subject line

### Usage in Dashboard
1. **Default Recipients**: Leave email field empty to use configured defaults
2. **Custom Recipients**: Enter email addresses (one per line) in the text area
3. **Preview**: Use the "Preview Email Content" section to see what will be sent
4. **Send**: Click the "Send Email Report" button

## Troubleshooting

### Common Issues
1. **"Email configuration missing"**
   - Ensure `config.json` has proper email section
   - Check all required fields are present

2. **"Failed to send email"**
   - Verify connection string is correct
   - Ensure sender email is from verified domain
   - Check recipient email addresses are valid

3. **"Sender email not verified"**
   - Verify the domain in Azure Communication Service
   - Use email address from verified domain only

### Authentication Requirements
- Uses Azure Communication Service connection string
- No additional Azure AD authentication required for email service
- Sender domain must be verified in Azure Communication Service

### Pricing
- Azure Communication Service Email pricing:
  - First 250 emails/month: Free
  - Additional emails: $0.0025 per email
- Custom domain: Additional DNS verification required
- Azure managed domain: Free with service

## Security Best Practices
1. Store connection string securely (consider Azure Key Vault for production)
2. Use least privilege access for Communication Service
3. Validate recipient email addresses
4. Monitor email usage and costs
5. Implement proper error handling and logging

## Example Usage
```python
# In your application
from azure_email_service import AzureEmailService, load_email_config_from_file

# Load configuration
config = load_email_config_from_file('config.json')

# Send report
with AzureEmailService(config) as email_service:
    success = email_service.send_capacity_report(
        capacity_data={'Standard': dataframe},
        recipients=['user@company.com']
    )
```