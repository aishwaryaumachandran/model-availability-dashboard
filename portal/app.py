"""
Azure AI Services Model Capacity Dashboard

A streamlined Streamlit web application for visualizing Azure OpenAI model capacity across regions.
Features:
- Interactive filters for models and regions at the top
- Clean table showing capacity by model and region
- Real-time data refresh
- Export capabilities
- Responsive design with modern UI

Author: Generated following Azure best practices
"""

import streamlit as st
import pandas as pd
import json
import asyncio
from datetime import datetime
import numpy as np
from io import BytesIO
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from azure_model_capacity_client import AzureModelCapacityClient, ConfigurationError, AzureError
from azure_email_service import AzureEmailService, load_email_config_from_file, EmailConfig


# Page configuration
st.set_page_config(
    page_title="Azure AI Model Capacity Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #0066cc;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(90deg, #f0f8ff 0%, #e6f3ff 100%);
        border-radius: 10px;
        border-left: 5px solid #0066cc;
    }
    
    .filter-container {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        margin-bottom: 1.5rem;
    }
    
    .stMultiSelect {
        margin-bottom: 0.5rem;
    }
    
    .stSelectbox {
        margin-bottom: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f8f9fa;
        border-radius: 4px 4px 0px 0px;
        color: #495057;
        font-weight: 500;
        margin: 0 5px;
        padding: 8px 16px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #0066cc;
        color: white;
    }
    
    .email-button {
        background: linear-gradient(45deg, #0066cc, #0052a3);
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        cursor: pointer;
        font-weight: bold;
        text-align: center;
        margin: 10px 0;
    }
    
    .email-button:hover {
        background: linear-gradient(45deg, #0052a3, #003d82);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,102,204,0.3);
    }
    
    .email-section {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #0066cc;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_capacity_data():
    """Load capacity data from Azure API with caching."""
    try:
        # Look for config.json in the parent directory
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        with AzureModelCapacityClient(config_path) as client:
            return client.get_all_models_capacity()
    except Exception as e:
        st.error(f"Error loading capacity data: {str(e)}")
        return {}


def process_capacity_data(raw_data, selected_sku=None):
    """Process raw capacity data into a structured format for display with regions as rows, filtered by SKU."""
    # First, collect all regions and model+version combinations for the selected SKU
    all_regions = set()
    model_versions = set()
    region_model_capacity = {}  # {region: {model_version: capacity}}
    all_skus = set()  # Track all available SKUs
    
    for model_name, results in raw_data.items():
        if not results:
            # Create model+version key for empty models
            model_version_key = f"{model_name} (N/A)"
            model_versions.add(model_version_key)
            continue
        
        # Collect all SKUs for reference
        for result in results:
            all_skus.add(result.sku_name)
        
        # Filter by selected SKU if specified
        if selected_sku:
            results = [r for r in results if r.sku_name == selected_sku]
        
        if not results:  # No results for this SKU
            continue
            
        # Group by model version
        version_groups = {}
        for result in results:
            version = result.model_version
            if version not in version_groups:
                version_groups[version] = []
            version_groups[version].append(result)
        
        for version, version_results in version_groups.items():
            model_version_key = f"{model_name} ({version})"
            model_versions.add(model_version_key)
            
            # Process each result
            for result in version_results:
                region = result.location
                all_regions.add(region)
                
                if region not in region_model_capacity:
                    region_model_capacity[region] = {}
                
                if model_version_key not in region_model_capacity[region]:
                    region_model_capacity[region][model_version_key] = 0
                
                region_model_capacity[region][model_version_key] += result.available_capacity
    
    # Create processed data with regions as rows
    processed_data = []
    for region in sorted(all_regions):
        row_data = {'Region': region}
        
        for model_version in sorted(model_versions):
            capacity = region_model_capacity.get(region, {}).get(model_version, 0)
            row_data[model_version] = capacity
        
        processed_data.append(row_data)
    
    return processed_data, sorted(model_versions), sorted(all_skus)


def create_capacity_table(processed_data, selected_model_versions):
    """Create a pandas DataFrame for the capacity table with regions as rows."""
    if not processed_data:
        return pd.DataFrame()
    
    # Create DataFrame
    df = pd.DataFrame(processed_data)
    
    # Define the column order: Region, selected model versions
    base_columns = ['Region']
    model_columns = [col for col in df.columns if col in selected_model_versions]
    
    column_order = base_columns + sorted(model_columns)
    
    # Reorder columns and fill missing values
    df = df.reindex(columns=column_order, fill_value=0)
    
    return df


def create_comprehensive_excel(raw_data, all_skus):
    """Create a comprehensive Excel file with separate sheets for each SKU."""
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Create a summary sheet
        summary_data = []
        for sku in sorted(all_skus):
            processed_data, model_versions, _ = process_capacity_data(raw_data, selected_sku=sku)
            total_regions = len(processed_data)
            total_models = len(model_versions)
            
            # Calculate total capacity for this SKU
            total_capacity = 0
            for row in processed_data:
                for model_version in model_versions:
                    total_capacity += row.get(model_version, 0)
            
            summary_data.append({
                'SKU_Type': sku,
                'Total_Regions': total_regions,
                'Total_Models': total_models,
                'Total_Capacity': total_capacity
            })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Create a sheet for each SKU
        for sku in sorted(all_skus):
            processed_data, model_versions, _ = process_capacity_data(raw_data, selected_sku=sku)
            
            if processed_data:
                df = create_capacity_table(processed_data, model_versions)
                if not df.empty:
                    # Clean sheet name (Excel has limitations on sheet names)
                    sheet_name = sku.replace('/', '_').replace('\\', '_')[:31]  # Max 31 chars for Excel
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    output.seek(0)
    return output.getvalue()


def apply_table_styling(df):
    """Apply color coding to the capacity table."""
    def color_capacity(val):
        """Color cells based on capacity value."""
        try:
            if pd.isna(val) or val == 'N/A':
                return 'background-color: #e2e3e5; color: #383d41'  # Gray for N/A
            
            val = float(val)
            if val >= 1000:
                return 'background-color: #d4edda; color: #155724'  # Green for high capacity
            elif val >= 100:
                return 'background-color: #fff3cd; color: #856404'  # Yellow for medium capacity
            elif val > 0:
                return 'background-color: #f8d7da; color: #721c24'  # Red for low capacity
            else:
                return 'background-color: #e2e3e5; color: #383d41'  # No capacity - gray
        except (ValueError, TypeError):
            return 'background-color: #e2e3e5; color: #383d41'
    
    # Apply styling to model version columns only
    model_columns = [col for col in df.columns if col not in ['Region']]
    
    # Use map instead of applymap (newer API)
    styled_df = df.style.map(color_capacity, subset=model_columns)
    
    # Format the table - no Total_Capacity to format
    return styled_df


def send_email_report(raw_data, all_skus, recipients=None):
    """
    Send email report with capacity data for all SKUs.
    
    Args:
        raw_data: Raw capacity data
        all_skus: List of all available SKU types
        recipients: Optional list of recipient emails
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Look for config.json in the parent directory
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        
        # Load email configuration with validation
        try:
            email_config = load_email_config_from_file(config_path)
        except Exception as config_error:
            return False, f"Email configuration error: {str(config_error)}"
        
        # Prepare capacity data for each SKU
        capacity_data = {}
        summary_stats = {
            'total_sku_types': len(all_skus),
            'total_regions': set(),
            'total_models': set()
        }
        
        for sku in all_skus:
            processed_data, model_versions, _ = process_capacity_data(raw_data, selected_sku=sku)
            
            if processed_data:
                df = create_capacity_table(processed_data, model_versions)
                if not df.empty:
                    capacity_data[sku] = df
                    
                    # Update summary stats
                    summary_stats['total_regions'].update(df['Region'].tolist())
                    model_cols = [col for col in df.columns if col != 'Region']
                    summary_stats['total_models'].update(model_cols)
        
        # Convert sets to counts
        summary_stats['total_regions'] = len(summary_stats['total_regions'])
        summary_stats['total_models'] = len(summary_stats['total_models'])
        
        # Send email
        try:
            with AzureEmailService(email_config) as email_service:
                success = email_service.send_capacity_report(
                    capacity_data=capacity_data,
                    recipients=recipients
                )
                
                if success:
                    return True, "Email report sent successfully!"
                else:
                    return False, "Failed to send email report. Check logs for details."
        except Exception as send_error:
            return False, f"Error during email sending: {str(send_error)}"
                
    except FileNotFoundError:
        return False, "Configuration file not found. Please ensure config.json exists."
    except KeyError as e:
        return False, f"Email configuration missing: {str(e)}"
    except Exception as e:
        return False, f"Error sending email: {str(e)}"


def main():
    """Main Streamlit application."""
    # Header
    st.markdown('<div class="main-header">Azure AI Model Capacity Dashboard</div>', unsafe_allow_html=True)
    
    # Load data first
    with st.spinner("Loading capacity data..."):
        raw_data = load_capacity_data()
    
    if not raw_data:
        st.error("No capacity data available. Please check your configuration.")
        return
    
    # Process data to get available SKUs
    temp_processed_data, temp_model_versions, all_skus = process_capacity_data(raw_data)
    
    # Create tabs for different SKU types
    if all_skus:
        # Sort SKUs with commonly used ones first
        sku_priority = ['GlobalStandard', 'GlobalProvisionedManaged', 'Standard', 'ProvisionedManaged', 'GlobalBatch']
        sorted_skus = []
        
        # Add priority SKUs if they exist
        for priority_sku in sku_priority:
            if priority_sku in all_skus:
                sorted_skus.append(priority_sku)
        
        # Add remaining SKUs
        for sku in sorted(all_skus):
            if sku not in sorted_skus:
                sorted_skus.append(sku)
        
        # Create tabs
        tab_names = [f"  {sku}  " for sku in sorted_skus]
        tabs = st.tabs(tab_names)
        
        # Process each tab
        for i, (sku, tab) in enumerate(zip(sorted_skus, tabs)):
            with tab:
                # Process data for the selected SKU
                processed_data, all_model_versions, _ = process_capacity_data(raw_data, selected_sku=sku)
    
                # Get all unique regions for this SKU
                all_regions = sorted(list(set(row['Region'] for row in processed_data)))
                
                # Filters for this tab
                st.markdown('<div class="filter-container">', unsafe_allow_html=True)
                st.subheader(f"Filters for {sku}")
                
                filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([3, 3, 2, 1])
                
                with filter_col1:
                    region_filter_options = ["All Regions"] + ["US Regions", "Europe Regions", "Asia Regions"] + all_regions
                    selected_region_filter = st.selectbox(
                        "Filter Regions:",
                        options=region_filter_options,
                        index=0,
                        key=f"region_filter_{sku}",
                        help="Choose which regions to display as rows"
                    )
                
                with filter_col2:
                    model_filter_options = ["All Models"] + all_model_versions
                    selected_model_filter = st.selectbox(
                        "Filter Models:",
                        options=model_filter_options,
                        index=0,
                        key=f"model_filter_{sku}",
                        help="Choose which model versions to display as columns"
                    )
                
                with filter_col3:
                    show_empty_regions = st.selectbox(
                        "Include Empty Regions:",
                        options=["Yes", "No"],
                        index=0,
                        key=f"empty_regions_{sku}",
                        help="Show regions with zero capacity"
                    )
                
                with filter_col4:
                    st.write("")  # Spacing
                    if st.button("Refresh", key=f"refresh_{sku}", type="primary"):
                        st.cache_data.clear()
                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
    
                # Apply region filtering
                filtered_data = []
                selected_regions = []
                
                if selected_region_filter == "All Regions":
                    selected_regions = all_regions
                elif selected_region_filter in ["US Regions", "Europe Regions", "Asia Regions"]:
                    region_prefixes = {
                        "US Regions": ["east", "west", "central", "south", "north"],
                        "Europe Regions": ["europe", "uk", "france", "germany", "norway", "sweden", "switzerland"],
                        "Asia Regions": ["asia", "japan", "korea", "india", "australia"]
                    }
                    prefixes = region_prefixes[selected_region_filter]
                    selected_regions = [region for region in all_regions if any(prefix in region.lower() for prefix in prefixes)]
                else:
                    selected_regions = [selected_region_filter] if selected_region_filter in all_regions else []
                
                # Apply model filtering
                selected_model_versions = []
                if selected_model_filter == "All Models":
                    selected_model_versions = all_model_versions
                else:
                    selected_model_versions = [selected_model_filter] if selected_model_filter in all_model_versions else []
                
                # Filter data by regions and capacity
                for row in processed_data:
                    if row['Region'] not in selected_regions:
                        continue
                    
                    # Check if region has any capacity for selected models if empty regions are excluded
                    if show_empty_regions == "No":
                        has_capacity = False
                        for model_version in selected_model_versions:
                            if row.get(model_version, 0) > 0:
                                has_capacity = True
                                break
                        if not has_capacity:
                            continue
                        
                    filtered_data.append(row)
                
                # Show filter summary
                if selected_regions and selected_model_versions:
                    st.info(f"**{sku}**: Showing {len(selected_regions)} regions across {len(selected_model_versions)} model versions")
                
                # Create and display table
                st.subheader(f"{sku} - Regional Capacity by Model Version")
                
                if filtered_data and selected_model_versions:
                    df = create_capacity_table(filtered_data, selected_model_versions)
                    
                    if not df.empty:
                        # Display the styled table
                        styled_df = apply_table_styling(df)
                        st.dataframe(
                            styled_df,
                            width='stretch',
                            height=min(600, len(filtered_data) * 35 + 100)  # Dynamic height
                        )
            
                        # Legend
                        st.markdown("""
                        **Legend:**
                        - **Green**: High capacity (≥1,000 units)
                        - **Yellow**: Medium capacity (100-999 units) 
                        - **Red**: Low capacity (1-99 units)
                        - **Gray**: No capacity available (0 or N/A)
                        """)
                        
                        # Export functionality
                        st.markdown("---")
                        col1, col2, col3 = st.columns([2, 2, 2])
                        
                        with col1:
                            # Comprehensive Excel download (only show on first tab to avoid duplicates)
                            if i == 0:  # Only show on the first tab
                                try:
                                    excel_data = create_comprehensive_excel(raw_data, all_skus)
                                    st.download_button(
                                        label="Download All SKUs Excel",
                                        data=excel_data,
                                        file_name=f"azure_capacity_all_skus_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        key="excel_download_all"
                                    )
                                except Exception as e:
                                    st.error(f"Excel generation failed: {str(e)}")
                            else:
                                st.write("")  # Empty space for alignment
                        
                        with col2:
                            # Email button (only show on first tab to avoid duplicates)
                            if i == 0:  # Only show on the first tab
                                if st.button("Email report to the default recipients", type="secondary", help="Send capacity report to default recipients", key="email_button_main"):
                                    with st.spinner("Sending email report..."):
                                        success, message = send_email_report(raw_data, all_skus, recipients=None)
                                    
                                    if success:
                                        st.success(message)
                                    else:
                                        st.error(message)
                            else:
                                st.write("")  # Empty space for alignment
                        
                        with col3:
                            st.caption(f"**{sku}**: {len(filtered_data)} regions • Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                            
                    else:
                        st.warning(f"No data to display for {sku} with current filters.")
                else:
                    if not selected_model_versions:
                        st.warning("Please select at least one model version to display.")
                    elif not selected_regions:
                        st.warning("Please select at least one region to display.")
                    else:
                        st.warning(f"No capacity data available for {sku} with the selected filters.")
    
    else:
        st.warning("No capacity data available. Please check your configuration.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.error("Please check your configuration and try again.")