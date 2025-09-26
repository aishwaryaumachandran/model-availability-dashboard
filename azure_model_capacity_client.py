"""
Azure AI Services Model Capacities API Client

This module provides functionality to query the Azure AI Services Model Capacities API
to check available capacity for different AI models (GPT-4o, o3, o4).

Features:
- Secure authentication using Azure DefaultAzureCredential (Managed Identity)
- Configuration-driven approach with JSON config file
- Retry logic with exponential backoff for transient failures
- Comprehensive error handling and logging
- Support for multiple model queries

Author: Generated following Azure best practices
Reference: https://learn.microsoft.com/en-us/rest/api/aiservices/accountmanagement/model-capacities/list
"""

import json
import logging
import time
import sys
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

import requests
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import AzureError


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('azure_model_capacity.log')
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for a specific AI model."""
    model_format: str
    model_name: str
    model_version: str


@dataclass 
class ModelCapacityResult:
    """Result object containing model capacity information."""
    model_name: str
    location: str
    sku_name: str
    available_capacity: int
    available_finetune_capacity: int
    model_format: str
    model_version: str


class ConfigurationError(Exception):
    """Raised when there's an error in configuration."""
    pass


class AzureModelCapacityClient:
    """
    Client for querying Azure AI Services Model Capacities API.
    
    This client follows Azure best practices:
    - Uses DefaultAzureCredential for secure authentication
    - Implements retry logic with exponential backoff
    - Provides comprehensive error handling and logging
    - Supports connection pooling and timeouts
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the client with configuration.
        
        Args:
            config_path: Path to the JSON configuration file
            
        Raises:
            ConfigurationError: If configuration is invalid or missing
            AzureError: If authentication fails
        """
        self.config = self._load_config(config_path)
        self.credential = None
        self.session = requests.Session()
        self._setup_authentication()
        self._setup_session()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load and validate configuration from JSON file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Loaded configuration dictionary
            
        Raises:
            ConfigurationError: If config file is missing or invalid
        """
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                raise ConfigurationError(f"Configuration file not found: {config_path}")
                
            with open(config_file, 'r') as f:
                config = json.load(f)
                
            # Validate required configuration sections
            required_sections = ['azure', 'models', 'request_settings']
            for section in required_sections:
                if section not in config:
                    raise ConfigurationError(f"Missing required configuration section: {section}")
                    
            # Validate Azure configuration
            azure_config = config['azure']
            required_azure_fields = ['subscription_id', 'api_version', 'base_url']
            for field in required_azure_fields:
                if field not in azure_config or not azure_config[field]:
                    raise ConfigurationError(f"Missing or empty Azure configuration field: {field}")
                    
            logger.info(f"Configuration loaded successfully from {config_path}")
            return config
            
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading configuration: {e}")
            
    def _setup_authentication(self):
        """
        Setup Azure authentication using DefaultAzureCredential.
        
        DefaultAzureCredential tries multiple authentication methods:
        1. Environment variables (service principal)
        2. Managed identity (when running in Azure)
        3. Visual Studio Code
        4. Azure CLI
        5. Azure PowerShell
        6. Interactive browser
        
        Raises:
            AzureError: If authentication setup fails
        """
        try:
            # Use DefaultAzureCredential following Azure best practices
            self.credential = DefaultAzureCredential()
            
            # Test credential by getting a token for Azure Resource Manager
            token = self.credential.get_token("https://management.azure.com/.default")
            if not token or not token.token:
                raise AzureError("Failed to obtain access token")
                
            logger.info("Azure authentication configured successfully")
            
        except Exception as e:
            logger.error(f"Authentication setup failed: {e}")
            raise AzureError(f"Authentication failed: {e}")
            
    def _setup_session(self):
        """Configure requests session with connection pooling and timeouts."""
        # Configure session for optimal performance
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=0  # We handle retries manually
        )
        self.session.mount('https://', adapter)
        
        # Set default timeout from configuration
        timeout = self.config['request_settings'].get('timeout', 30)
        self.session.timeout = timeout
        
        logger.info("HTTP session configured with connection pooling")
        
    def _get_access_token(self) -> str:
        """
        Get a fresh access token for Azure Resource Manager API.
        
        Returns:
            Access token string
            
        Raises:
            AzureError: If token acquisition fails
        """
        try:
            token = self.credential.get_token("https://management.azure.com/.default")
            return token.token
        except Exception as e:
            logger.error(f"Failed to get access token: {e}")
            raise AzureError(f"Token acquisition failed: {e}")
            
    def _make_request_with_retry(self, url: str, headers: Dict[str, str], params: Dict[str, str]) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic and exponential backoff.
        
        Args:
            url: Request URL
            headers: Request headers
            params: Query parameters
            
        Returns:
            Response JSON data
            
        Raises:
            requests.RequestException: If all retry attempts fail
        """
        retry_attempts = self.config['request_settings'].get('retry_attempts', 3)
        retry_delay = self.config['request_settings'].get('retry_delay', 1)
        
        for attempt in range(retry_attempts):
            try:
                logger.debug(f"Making request attempt {attempt + 1}/{retry_attempts}")
                
                response = self.session.get(
                    url=url,
                    headers=headers,
                    params=params,
                    timeout=self.config['request_settings'].get('timeout', 30)
                )
                
                # Handle successful responses
                if response.status_code == 200:
                    return response.json()
                    
                # Handle authentication errors (don't retry these)
                elif response.status_code in [401, 403]:
                    logger.error(f"Authentication/Authorization error: {response.status_code}")
                    response.raise_for_status()
                    
                # Handle rate limiting and server errors (retry these)
                elif response.status_code in [429, 500, 502, 503, 504]:
                    if attempt == retry_attempts - 1:
                        logger.error(f"Request failed after {retry_attempts} attempts: {response.status_code}")
                        response.raise_for_status()
                    else:
                        wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Request failed with {response.status_code}, retrying in {wait_time} seconds")
                        time.sleep(wait_time)
                        continue
                else:
                    logger.error(f"Unexpected response status: {response.status_code}")
                    response.raise_for_status()
                    
            except requests.exceptions.Timeout:
                if attempt == retry_attempts - 1:
                    logger.error("Request timed out after all retry attempts")
                    raise
                else:
                    wait_time = retry_delay * (2 ** attempt)
                    logger.warning(f"Request timed out, retrying in {wait_time} seconds")
                    time.sleep(wait_time)
                    continue
                    
            except requests.exceptions.ConnectionError:
                if attempt == retry_attempts - 1:
                    logger.error("Connection error after all retry attempts")
                    raise
                else:
                    wait_time = retry_delay * (2 ** attempt)
                    logger.warning(f"Connection error, retrying in {wait_time} seconds")
                    time.sleep(wait_time)
                    continue
                    
        raise requests.RequestException("Request failed after all retry attempts")
        
    def get_model_capacity(self, model_name: str) -> List[ModelCapacityResult]:
        """
        Query model capacity for a specific model.
        
        Args:
            model_name: Name of the model (e.g., 'gpt-4o', 'o3', 'o4')
            
        Returns:
            List of ModelCapacityResult objects
            
        Raises:
            ConfigurationError: If model is not configured
            AzureError: If API call fails
            requests.RequestException: If HTTP request fails
        """
        # Validate model is configured
        if model_name not in self.config['models']:
            raise ConfigurationError(f"Model '{model_name}' not found in configuration")
            
        model_config = ModelConfig(**self.config['models'][model_name])
        logger.info(f"Querying capacity for model: {model_name}")
        
        try:
            # Get fresh access token
            access_token = self._get_access_token()
            
            # Build request URL and parameters
            base_url = self.config['azure']['base_url']
            subscription_id = self.config['azure']['subscription_id']
            api_version = self.config['azure']['api_version']
            
            url = f"{base_url}/subscriptions/{subscription_id}/providers/Microsoft.CognitiveServices/modelCapacities"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'User-Agent': 'Azure-Model-Capacity-Client/1.0'
            }
            
            params = {
                'api-version': api_version,
                'modelFormat': model_config.model_format,
                'modelName': model_config.model_name,
                'modelVersion': model_config.model_version
            }
            
            # Make API request with retry logic
            response_data = self._make_request_with_retry(url, headers, params)
            
            # Parse response into result objects
            results = []
            for item in response_data.get('value', []):
                properties = item.get('properties', {})
                model_info = properties.get('model', {})
                
                result = ModelCapacityResult(
                    model_name=model_info.get('name', ''),
                    location=item.get('location', ''),
                    sku_name=properties.get('skuName', ''),
                    available_capacity=properties.get('availableCapacity', 0),
                    available_finetune_capacity=properties.get('availableFinetuneCapacity', 0),
                    model_format=model_info.get('format', ''),
                    model_version=model_info.get('version', '')
                )
                results.append(result)
                
            logger.info(f"Retrieved capacity data for {len(results)} locations for model '{model_name}'")
            return results
            
        except Exception as e:
            logger.error(f"Failed to get model capacity for '{model_name}': {e}")
            raise
            
    def get_all_models_capacity(self) -> Dict[str, List[ModelCapacityResult]]:
        """
        Query capacity for all configured models.
        
        Returns:
            Dictionary mapping model names to their capacity results
            
        Raises:
            AzureError: If any API calls fail
        """
        logger.info("Querying capacity for all configured models")
        all_results = {}
        errors = []
        
        for model_name in self.config['models'].keys():
            try:
                results = self.get_model_capacity(model_name)
                all_results[model_name] = results
            except Exception as e:
                error_msg = f"Failed to get capacity for model '{model_name}': {e}"
                logger.error(error_msg)
                errors.append(error_msg)
                all_results[model_name] = []
                
        if errors:
            logger.warning(f"Completed with {len(errors)} errors")
            
        return all_results
        
    def print_capacity_report(self, results: Dict[str, List[ModelCapacityResult]]):
        """
        Print a formatted capacity report.
        
        Args:
            results: Dictionary of model capacity results
        """
        print("\n" + "="*80)
        print("Azure AI Services Model Capacity Report")
        print("="*80)
        
        for model_name, model_results in results.items():
            print(f"\nModel: {model_name.upper()}")
            print("-" * 40)
            
            if not model_results:
                print("  No capacity data available or query failed")
                continue
                
            for result in model_results:
                print(f"  Location: {result.location}")
                print(f"  SKU: {result.sku_name}")
                print(f"  Available Capacity: {result.available_capacity}")
                print(f"  Available Finetune Capacity: {result.available_finetune_capacity}")
                print(f"  Model Format: {result.model_format}")
                print(f"  Model Version: {result.model_version}")
                print()
                
        print("="*80)
        
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        if self.session:
            self.session.close()
            

def main():
    """
    Main function demonstrating usage of the Azure Model Capacity Client.
    """
    try:
        # Initialize client with configuration
        with AzureModelCapacityClient("config.json") as client:
            print("Azure AI Services Model Capacity Client")
            print("======================================")
            
            # Option 1: Query specific model
            print("\n1. Query specific model (example: gpt-4o)")
            try:
                gpt4o_results = client.get_model_capacity("gpt-4o")
                print(f"Found capacity data for {len(gpt4o_results)} regions")
                for result in gpt4o_results[:2]:  # Show first 2 results
                    print(f"  - {result.location}: {result.available_capacity} capacity available")
            except Exception as e:
                print(f"  Error querying gpt-4o: {e}")
            
            # Option 2: Query all configured models
            print("\n2. Query all configured models")
            all_results = client.get_all_models_capacity()
            
            # Print formatted report
            client.print_capacity_report(all_results)
            
            # Option 3: Export to JSON (optional)
            print("\n3. Export results to JSON")
            export_data = {}
            for model_name, results in all_results.items():
                export_data[model_name] = [
                    {
                        'location': r.location,
                        'sku_name': r.sku_name,
                        'available_capacity': r.available_capacity,
                        'available_finetune_capacity': r.available_finetune_capacity,
                        'model_format': r.model_format,
                        'model_version': r.model_version
                    } for r in results
                ]
                
            with open('model_capacity_results.json', 'w') as f:
                json.dump(export_data, f, indent=2)
            print("Results exported to 'model_capacity_results.json'")
            
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        print(f"Error: {e}")
        print("\nPlease check your config.json file and ensure all required fields are filled.")
        sys.exit(1)
        
    except AzureError as e:
        logger.error(f"Azure authentication error: {e}")
        print(f"Azure Error: {e}")
        print("\nPlease ensure you are authenticated with Azure (az login) or have proper managed identity configured.")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()