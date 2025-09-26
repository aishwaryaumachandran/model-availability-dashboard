"""
Azure AI Services Model Capacity Client Package

This package provides tools for querying and monitoring Azure AI Services
model capacity across different regions and SKU types.

Components:
- azure_model_capacity_client: Main client library for Azure API interactions
- usage_examples: Example scripts demonstrating client usage
"""

__version__ = "1.0.0"
__author__ = "Aishwarya Umachandran"
__description__ = "Azure AI Services Model Capacity Monitoring Tools"

from .azure_model_capacity_client import AzureModelCapacityClient, ModelCapacityResult, ConfigurationError, AzureError

__all__ = [
    'AzureModelCapacityClient',
    'ModelCapacityResult', 
    'ConfigurationError',
    'AzureError'
]