"""
Azure Communication Service Email Client

A client for sending emails using Azure Communication Service with model capacity data.
Follows Azure best practices for secure authentication and error handling.

Author: Generated following Azure best practices
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from azure.identity import DefaultAzureCredential
from azure.communication.email import EmailClient
from azure.core.exceptions import AzureError
import pandas as pd


@dataclass
class EmailConfig:
    """Configuration for Azure Communication Service Email."""
    connection_string: str
    sender_email: str
    default_recipients: List[str]
    subject_prefix: str = "[Azure Model Capacity]"


class AzureEmailService:
    """Azure Communication Service Email client for sending capacity reports."""
    
    def __init__(self, config: EmailConfig):
        """
        Initialize the Azure Email Service client.
        
        Args:
            config: Email configuration object
        """
        self.config = config
        self.client = None
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging for the email service."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def __enter__(self):
        """Context manager entry."""
        try:
            self.client = EmailClient.from_connection_string(self.config.connection_string)
            self.logger.info("Azure Email Service client initialized successfully")
            return self
        except Exception as e:
            self.logger.error(f"Failed to initialize Azure Email Service: {str(e)}")
            raise
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type:
            self.logger.error(f"Error in Azure Email Service: {exc_val}")
        self.client = None
    
    def format_capacity_table_html(self, df: pd.DataFrame, sku_type: str) -> str:
        """
        Format capacity data as an HTML table for email.
        
        Args:
            df: DataFrame containing capacity data
            sku_type: Type of SKU being reported
            
        Returns:
            HTML formatted table string
        """
        if df.empty:
            return f"<p>No capacity data available for {sku_type}.</p>"
        
        # Create a styled HTML table
        html = f"""
        <div style="margin: 20px 0;">
            <h3 style="color: #0066cc; margin-bottom: 15px;">{sku_type} - Model Capacity by Region</h3>
            <table style="border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; font-size: 12px;">
                <thead>
                    <tr style="background-color: #0066cc; color: white;">
        """
        
        # Add headers
        for col in df.columns:
            html += f'<th style="border: 1px solid #ddd; padding: 8px; text-align: left;">{col}</th>'
        
        html += "</tr></thead><tbody>"
        
        # Add data rows
        for _, row in df.iterrows():
            html += "<tr>"
            for i, (col, value) in enumerate(row.items()):
                if i == 0:  # Region column
                    style = "border: 1px solid #ddd; padding: 8px; background-color: #f8f9fa;"
                else:  # Capacity columns
                    # Color coding based on capacity
                    if pd.isna(value) or value == 0:
                        bg_color = "#e2e3e5"  # Gray for no capacity
                    elif value >= 1000:
                        bg_color = "#d4edda"  # Green for high capacity
                    elif value >= 100:
                        bg_color = "#fff3cd"  # Yellow for medium capacity
                    else:
                        bg_color = "#f8d7da"  # Red for low capacity
                    
                    style = f"border: 1px solid #ddd; padding: 8px; background-color: {bg_color}; text-align: center;"
                
                html += f'<td style="{style}">{value}</td>'
            html += "</tr>"
        
        html += """
                </tbody>
            </table>
            <div style="margin-top: 10px; font-size: 11px; color: #666;">
                <strong>Legend:</strong>
                <span style="background-color: #d4edda; padding: 2px 6px; margin: 0 3px;">High (≥1,000)</span>
                <span style="background-color: #fff3cd; padding: 2px 6px; margin: 0 3px;">Medium (100-999)</span>
                <span style="background-color: #f8d7da; padding: 2px 6px; margin: 0 3px;">Low (1-99)</span>
                <span style="background-color: #e2e3e5; padding: 2px 6px; margin: 0 3px;">None (0)</span>
            </div>
        </div>
        """
        
        return html
    
    def create_email_content(self, capacity_data: Dict[str, pd.DataFrame], 
                           summary_stats: Dict[str, Any]) -> str:
        """
        Create HTML email content with capacity data.
        
        Args:
            capacity_data: Dictionary mapping SKU types to their capacity DataFrames
            summary_stats: Summary statistics about the data
            
        Returns:
            HTML formatted email content
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #0066cc; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .summary {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Azure AI Model Capacity Report</h1>
                <p>Generated on {timestamp}</p>
            </div>
            
            <div class="content">
                <div class="summary">
                    <h2>Summary</h2>
                    <ul>
                        <li><strong>Total SKU Types:</strong> {summary_stats.get('total_sku_types', 0)}</li>
                        <li><strong>Total Regions:</strong> {summary_stats.get('total_regions', 0)}</li>
                        <li><strong>Total Models:</strong> {summary_stats.get('total_models', 0)}</li>
                        <li><strong>Report Generated:</strong> {timestamp}</li>
                    </ul>
                </div>
        """
        
        # Add capacity tables for each SKU type
        for sku_type, df in capacity_data.items():
            html_content += self.format_capacity_table_html(df, sku_type)
        
        html_content += """
            </div>
            
            <div class="footer">
                <p>This report was automatically generated by the Azure AI Model Capacity Dashboard.</p>
                <p>For questions or support, please contact your Azure administrator.</p>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def send_capacity_report(self, capacity_data: Dict[str, pd.DataFrame], 
                           recipients: Optional[List[str]] = None,
                           subject_suffix: str = "") -> bool:
        """
        Send capacity report via email.
        
        Args:
            capacity_data: Dictionary mapping SKU types to their capacity DataFrames
            recipients: List of recipient email addresses (uses default if None)
            subject_suffix: Additional text to append to email subject
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.client:
            self.logger.error("Email client not initialized")
            return False
        
        try:
            # Use default recipients if none provided
            if not recipients:
                recipients = self.config.default_recipients
            
            if not recipients:
                self.logger.error("No recipients specified")
                return False
            
            # Calculate summary statistics
            total_regions = set()
            total_models = set()
            for df in capacity_data.values():
                if not df.empty:
                    total_regions.update(df['Region'].tolist())
                    model_cols = [col for col in df.columns if col != 'Region']
                    total_models.update(model_cols)
            
            summary_stats = {
                'total_sku_types': len(capacity_data),
                'total_regions': len(total_regions),
                'total_models': len(total_models)
            }
            
            # Create email content
            html_content = self.create_email_content(capacity_data, summary_stats)
            
            # Prepare email subject
            subject = f"{self.config.subject_prefix} Report"
            if subject_suffix:
                subject += f" - {subject_suffix}"
            subject += f" ({datetime.now().strftime('%Y-%m-%d')})"
            
            # Send email
            message = {
                "senderAddress": self.config.sender_email,
                "recipients": {
                    "to": [{"address": email} for email in recipients]
                },
                "content": {
                    "subject": subject,
                    "html": html_content
                }
            }
            
            poller = self.client.begin_send(message)
            result = poller.result()
            
            self.logger.info(f"Email sent successfully to {len(recipients)} recipients")
            
            # Try to log message ID if available, but don't fail if not present
            try:
                if hasattr(result, 'id'):
                    self.logger.info(f"Message ID: {result.id}")
                elif hasattr(result, 'message_id'):
                    self.logger.info(f"Message ID: {result.message_id}")
                elif isinstance(result, dict):
                    message_id = result.get('id') or result.get('message_id') or result.get('messageId')
                    if message_id:
                        self.logger.info(f"Message ID: {message_id}")
                    else:
                        self.logger.info(f"Email sent, result: {str(result)}")
                else:
                    self.logger.info(f"Email sent, result type: {type(result)}")
            except Exception as log_error:
                self.logger.warning(f"Could not log message ID: {str(log_error)}")
                
            return True
            
        except AzureError as e:
            self.logger.error(f"Azure error sending email: {str(e)}")
            self.logger.error(f"Error details: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending email: {str(e)}")
            self.logger.error(f"Error type: {type(e).__name__}")
            # Log more details for debugging
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return False


def load_email_config_from_file(config_path: str) -> EmailConfig:
    """
    Load email configuration from JSON file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        EmailConfig object
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        KeyError: If required configuration keys are missing
        json.JSONDecodeError: If config file is invalid JSON
    """
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        email_config = config_data.get('email', {})
        
        return EmailConfig(
            connection_string=email_config['connection_string'],
            sender_email=email_config['sender_email'],
            default_recipients=email_config.get('default_recipients', []),
            subject_prefix=email_config.get('subject_prefix', '[Azure Model Capacity]')
        )
    
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    except KeyError as e:
        raise KeyError(f"Missing required email configuration key: {e}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in configuration file: {e}")