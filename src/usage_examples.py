"""
Example script demonstrating different usage patterns for the Azure Model Capacity Client.
"""

from azure_model_capacity_client import AzureModelCapacityClient, ConfigurationError, AzureError
import json


def example_single_model_query():
    """Example: Query capacity for a single model."""
    print("Example 1: Single Model Query")
    print("-" * 30)
    
    try:
        with AzureModelCapacityClient("config.json") as client:
            # Query GPT-4o capacity
            results = client.get_model_capacity("gpt-4o")
            
            if results:
                print(f"Found capacity data for GPT-4o in {len(results)} regions:")
                for result in results:
                    print(f"  📍 {result.location}: {result.available_capacity} units available")
            else:
                print("No capacity data found for GPT-4o")
                
    except ConfigurationError as e:
        print(f"Configuration error: {e}")
    except AzureError as e:
        print(f"Azure error: {e}")
    except Exception as e:
        print(f"Error: {e}")


def example_all_models_query():
    """Example: Query capacity for all configured models."""
    print("\nExample 2: All Models Query")
    print("-" * 30)
    
    try:
        with AzureModelCapacityClient("config.json") as client:
            all_results = client.get_all_models_capacity()
            
            for model_name, results in all_results.items():
                print(f"\n🤖 Model: {model_name}")
                if results:
                    total_capacity = sum(r.available_capacity for r in results)
                    print(f"   Total available capacity: {total_capacity} units")
                    print(f"   Available in {len(results)} regions")
                else:
                    print("   No capacity data available")
                    
    except Exception as e:
        print(f"Error: {e}")


def example_capacity_summary():
    """Example: Generate a capacity summary report."""
    print("\nExample 3: Capacity Summary")
    print("-" * 30)
    
    try:
        with AzureModelCapacityClient("config.json") as client:
            all_results = client.get_all_models_capacity()
            
            summary = {}
            for model_name, results in all_results.items():
                if results:
                    summary[model_name] = {
                        "total_capacity": sum(r.available_capacity for r in results),
                        "total_finetune_capacity": sum(r.available_finetune_capacity for r in results),
                        "regions": len(results),
                        "top_region": max(results, key=lambda x: x.available_capacity) if results else None
                    }
                else:
                    summary[model_name] = {
                        "total_capacity": 0,
                        "total_finetune_capacity": 0,
                        "regions": 0,
                        "top_region": None
                    }
            
            print("\n📊 Capacity Summary:")
            for model, data in summary.items():
                print(f"\n{model.upper()}:")
                print(f"  • Total Capacity: {data['total_capacity']} units")
                print(f"  • Total Finetune Capacity: {data['total_finetune_capacity']} units")
                print(f"  • Available Regions: {data['regions']}")
                if data['top_region']:
                    top = data['top_region']
                    print(f"  • Highest Capacity Region: {top.location} ({top.available_capacity} units)")
                    
    except Exception as e:
        print(f"Error: {e}")


def example_find_best_regions():
    """Example: Find regions with highest capacity for each model."""
    print("\nExample 4: Best Regions Analysis")
    print("-" * 30)
    
    try:
        with AzureModelCapacityClient("config.json") as client:
            all_results = client.get_all_models_capacity()
            
            print("\n🏆 Best Regions by Model:")
            for model_name, results in all_results.items():
                if results:
                    # Sort by available capacity (descending)
                    sorted_results = sorted(results, key=lambda x: x.available_capacity, reverse=True)
                    top_3 = sorted_results[:3]
                    
                    print(f"\n{model_name.upper()}:")
                    for i, result in enumerate(top_3, 1):
                        print(f"  {i}. {result.location}: {result.available_capacity} units")
                else:
                    print(f"\n{model_name.upper()}: No data available")
                    
    except Exception as e:
        print(f"Error: {e}")


def example_export_custom_format():
    """Example: Export results in custom format."""
    print("\nExample 5: Custom Export")
    print("-" * 30)
    
    try:
        with AzureModelCapacityClient("config.json") as client:
            all_results = client.get_all_models_capacity()
            
            # Create custom export format
            export_data = {
                "timestamp": "2025-01-17T12:00:00Z",  # You'd use actual timestamp
                "subscription": client.config['azure'].get('subscription_name', 'N/A'),
                "models": {}
            }
            
            for model_name, results in all_results.items():
                model_data = {
                    "total_regions": len(results),
                    "total_capacity": sum(r.available_capacity for r in results),
                    "regions": []
                }
                
                for result in results:
                    region_data = {
                        "name": result.location,
                        "capacity": result.available_capacity,
                        "finetune_capacity": result.available_finetune_capacity,
                        "sku": result.sku_name
                    }
                    model_data["regions"].append(region_data)
                
                export_data["models"][model_name] = model_data
            
            # Save to file
            with open("custom_capacity_report.json", "w") as f:
                json.dump(export_data, f, indent=2)
            
            print("✅ Custom report exported to 'custom_capacity_report.json'")
            print(f"📊 Summary: {len(export_data['models'])} models analyzed")
            
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Run all examples."""
    print("🚀 Azure Model Capacity Client - Usage Examples")
    print("=" * 50)
    
    # Run examples
    example_single_model_query()
    example_all_models_query()  
    example_capacity_summary()
    example_find_best_regions()
    example_export_custom_format()
    
    print("\n" + "=" * 50)
    print("✨ All examples completed!")
    print("\nNote: Update config.json with your Azure details before running.")


if __name__ == "__main__":
    main()