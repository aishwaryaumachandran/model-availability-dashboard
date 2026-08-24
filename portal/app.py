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
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    #"""Load capacity data from Azure API with caching"""
    """Load capacity data from Azure API with caching (background load without progress display)."""
    try:
        # Look for config.json in the parent directory
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        with AzureModelCapacityClient(config_path) as client:
            return client.get_all_models_capacity()
    except Exception as e:
        st.error(f"Error loading capacity data: {str(e)}")
        return {}


def load_capacity_data_with_progress(model_names_filter=None):
    """Load capacity data with progress display, optionally restricted to a subset of models."""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        
        # Initialize session state for persistent display
        if 'capacity_data_loaded' not in st.session_state:
            st.session_state.capacity_data_loaded = False
            st.session_state.loading_results = []
            st.session_state.all_results_cache = {}
        
        # If data is already loaded, show completed status with expanded=True
        if st.session_state.capacity_data_loaded:
            # Data already loaded in this session; don't render loading UI again.
            return st.session_state.all_results_cache
        
        # Load config to get model list
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        models = config.get('models', {})
        model_names = [m for m in models.keys() if not m.startswith('_')]
        if model_names_filter is not None:
            allowed = set(model_names_filter)
            model_names = [m for m in model_names if m in allowed]
        
        all_results = {}
        errors = []
        load_results = []  # Track results in order (newest at top)
        
        def fetch_model_capacity(model_name):
            """Fetch capacity for a single model (runs in thread pool)."""
            try:
                with AzureModelCapacityClient(config_path) as client:
                    results = client.get_model_capacity(model_name)
                    return model_name, results, None
            except Exception as e:
                return model_name, [], str(e)
        
        status_container = st.empty()
        with status_container.container():
            with st.status("Loading model capacity data...", expanded=True) as status:
                results_placeholder = st.empty()
                completed = 0
                
                # Use ThreadPoolExecutor for parallel loading
                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = {executor.submit(fetch_model_capacity, name): name for name in model_names}
                    
                    for future in as_completed(futures):
                        model_name, results, error = future.result()
                        completed += 1
                        
                        status.update(
                            label=f"Loading model capacity data ({completed}/{len(model_names)})",
                            state="running",
                            expanded=True
                        )
                        
                        if error:
                            all_results[model_name] = []
                            errors.append(f"Failed to load {model_name}: {error}")
                            load_results.insert(0, f"✗ {model_name}: Error")
                        else:
                            all_results[model_name] = results
                            load_results.insert(0, f"✓ {model_name}: {len(results)} regions")
                        
                        with results_placeholder.container():
                            for result in load_results:
                                st.write(result)
            
                # Cache results in session state for subsequent reruns
                st.session_state.loading_results = load_results
                st.session_state.all_results_cache = all_results
                st.session_state.capacity_data_loaded = True
            
                # Final status: keep visible only when there are errors.
                if errors:
                    status.update(label=f"Loaded with {len(errors)} errors", state="error", expanded=True)

        # Hide loading component after successful completion.
        if not errors:
            status_container.empty()
        
        return all_results
        
    except Exception as e:
        st.error(f"Error loading capacity data: {str(e)}")
        return {}


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_region_filter_metadata():
    """Load region filter metadata directly from configuration file."""
    try:
        # Look for config.json in the parent directory
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check for region settings in dashboard_settings or top-level regions
        region_setting = config.get('dashboard_settings', {}).get('regions')
        
        # Backward-compatible fallback
        if region_setting is None:
            region_setting = config.get('regions', 0)
        
        # Determine if filtering is active
        if region_setting == 0:
            is_filtered = False
            filtered_regions = None
            filtered_regions_list = []
        elif isinstance(region_setting, list):
            is_filtered = True
            filtered_regions = {str(r).strip().lower() for r in region_setting if str(r).strip()}
            # Keep original casing for display
            filtered_regions_list = [str(r).strip() for r in region_setting if str(r).strip()]
        else:
            # Invalid config, default to full
            is_filtered = False
            filtered_regions = None
            filtered_regions_list = []
        
        return {
            'is_filtered': is_filtered,
            'mode': 'subset' if is_filtered else 'full',
            'filtered_regions': filtered_regions,
            'filtered_regions_list': filtered_regions_list  # Original casing for display
        }
        
    except Exception:
        # Return default (full mode) if error
        return {
            'is_filtered': False,
            'mode': 'full',
            'filtered_regions': None,
            'filtered_regions_list': []
        }


def _model_version_sort_key(model_version_key):
    """Extract version date from 'model (version)' and return a sort key for newest-first ordering."""
    import re
    match = re.search(r'\(([^)]+)\)$', model_version_key)
    if match and match.group(1) != 'N/A':
        version = match.group(1)
        # Date-based versions like 2026-04-24 sort lexicographically
        return (0, version)  # group 0 = has version, sorted by date desc via reverse=True
    return (-1, model_version_key)  # group -1 = N/A versions; with reverse=True, -1 < 0 so these go last


def process_capacity_data(raw_data, selected_sku=None, region_filter_metadata=None):
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
        # Use region name directly (mode is already shown in the banner at the top)
        row_data = {'Region': region}
        
        for model_version in sorted(model_versions):
            capacity = region_model_capacity.get(region, {}).get(model_version, 0)
            row_data[model_version] = capacity
        
        processed_data.append(row_data)
    
    return processed_data, sorted(model_versions, key=_model_version_sort_key, reverse=True), sorted(all_skus)


def create_capacity_table(processed_data, selected_model_versions):
    """Create a pandas DataFrame for the capacity table with regions as rows."""
    if not processed_data:
        return pd.DataFrame()
    
    # Create DataFrame
    df = pd.DataFrame(processed_data)
    
    # Define the column order: Region, selected model versions
    base_columns = ['Region']
    model_columns = [col for col in df.columns if col in selected_model_versions]
    
    column_order = base_columns + sorted(model_columns, key=_model_version_sort_key, reverse=True)
    
    # Reorder columns and fill missing values
    df = df.reindex(columns=column_order, fill_value=0)
    
    return df


def create_comprehensive_excel(raw_data, all_skus, region_filter_metadata=None):
    """Create a comprehensive Excel file with separate sheets for each SKU."""
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Create a summary sheet
        summary_data = []
        for sku in sorted(all_skus):
            processed_data, model_versions, _ = process_capacity_data(raw_data, selected_sku=sku, region_filter_metadata=region_filter_metadata)
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
            processed_data, model_versions, _ = process_capacity_data(raw_data, selected_sku=sku, region_filter_metadata=region_filter_metadata)
            
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


def send_email_report(raw_data, all_skus, recipients=None, region_filter_metadata=None):
    """
    Send email report with capacity data for all SKUs.
    
    Args:
        raw_data: Raw capacity data
        all_skus: List of all available SKU types
        recipients: Optional list of recipient emails
        region_filter_metadata: Region filter configuration metadata
    
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
            processed_data, model_versions, _ = process_capacity_data(raw_data, selected_sku=sku, region_filter_metadata=region_filter_metadata)
            
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


def get_model_registry():
    """Return {provider: [model_name, ...]} from config.json, sorted for stable UI."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
    registry = {}
    for name, meta in config.get('models', {}).items():
        if name.startswith('_') or not isinstance(meta, dict):
            continue
        provider = meta.get('model_format', 'Unknown')
        registry.setdefault(provider, []).append(name)
    for provider in registry:
        registry[provider].sort()
    return dict(sorted(registry.items()))


def render_model_selector():
    """Parent filter: pick providers and models before loading capacity data.

    Returns the list of selected model names, or None if the user hasn't submitted yet.
    """
    registry = get_model_registry()
    all_providers = list(registry.keys())
    total_models = sum(len(v) for v in registry.values())

    if 'selected_models' not in st.session_state:
        st.session_state.selected_models = None
        st.session_state.selected_providers = ['OpenAI'] if 'OpenAI' in registry else all_providers[:1]

    # Once user has loaded data, show a compact summary + "Change selection" control.
    if st.session_state.selected_models is not None:
        selected = st.session_state.selected_models
        with st.container():
            cols = st.columns([6, 1])
            with cols[0]:
                st.caption(
                    f"**Loaded**: {len(selected)} of {total_models} models across "
                    f"{len(st.session_state.selected_providers)} provider(s): "
                    f"{', '.join(st.session_state.selected_providers)}"
                )
            with cols[1]:
                if st.button("Change selection", key="change_model_selection"):
                    st.session_state.selected_models = None
                    st.session_state.capacity_data_loaded = False
                    st.session_state.all_results_cache = {}
                    st.session_state.loading_results = []
                    st.cache_data.clear()
                    st.rerun()
        return selected

    # First-time / re-selection UI.
    st.markdown('<div class="filter-container">', unsafe_allow_html=True)
    st.subheader("Model Filter")
    st.caption(
        f"Select which providers and models to query. "
        f"({total_models} models available across {len(all_providers)} providers.)"
    )

    with st.form("model_selector_form", clear_on_submit=False):
        provider_labels = [f"{p} ({len(registry[p])})" for p in all_providers]
        label_to_provider = dict(zip(provider_labels, all_providers))
        default_provider_labels = [
            f"{p} ({len(registry[p])})" for p in st.session_state.selected_providers if p in registry
        ]
        picked_labels = st.multiselect(
            "Providers:",
            options=provider_labels,
            default=default_provider_labels,
            help="Providers correspond to Azure `modelFormat` values."
        )
        picked_providers = [label_to_provider[l] for l in picked_labels]

        candidate_models = [m for p in picked_providers for m in registry[p]]

        select_all = st.checkbox(
            "Load all models from the selected providers",
            value=True,
            help="Uncheck to narrow the selection to specific models."
        )

        if select_all:
            picked_models = candidate_models
            st.caption(f"{len(picked_models)} model(s) will be loaded.")
        else:
            picked_models = st.multiselect(
                "Models:",
                options=candidate_models,
                default=candidate_models,
                help="Only the checked models will be queried."
            )

        submitted = st.form_submit_button("Load capacity data", type="primary")

    st.markdown('</div>', unsafe_allow_html=True)

    if submitted:
        if not picked_models:
            st.warning("Please select at least one model.")
            return None
        st.session_state.selected_providers = picked_providers
        st.session_state.selected_models = picked_models
        st.session_state.capacity_data_loaded = False
        st.session_state.all_results_cache = {}
        st.session_state.loading_results = []
        st.cache_data.clear()
        st.rerun()

    return None


def main():
    """Main Streamlit application."""
    # Header
    st.markdown('<div class="main-header">Azure AI Model Capacity Dashboard</div>', unsafe_allow_html=True)

    # Parent filter: choose providers/models before fetching capacity.
    selected_models = render_model_selector()
    if selected_models is None:
        st.info("Choose providers and models above, then click **Load capacity data** to begin.")
        return

    # Load data with progress display for the selected models only.
    raw_data = load_capacity_data_with_progress(model_names_filter=selected_models)
    
    if not raw_data:
        st.error("No capacity data available. Please check your configuration.")
        return
    
    # Load region filter metadata
    region_filter_metadata = load_region_filter_metadata()
    
    # Display region mode indicator
    if region_filter_metadata.get('is_filtered'):
        regions_list = region_filter_metadata.get('filtered_regions_list', [])
        regions_display = ", ".join(regions_list)
        st.info(f"📍 **Region Mode**: SUBSET\n\n**Selected Regions** ({len(regions_list)}): {regions_display}")
    
    # Process data to get available SKUs
    temp_processed_data, temp_model_versions, all_skus = process_capacity_data(raw_data, region_filter_metadata=region_filter_metadata)
    
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
                processed_data, all_model_versions, _ = process_capacity_data(raw_data, selected_sku=sku, region_filter_metadata=region_filter_metadata)
    
                # Get all unique regions for this SKU
                all_regions = sorted(list(set(row['Region'] for row in processed_data)))
                
                # Filters for this tab
                st.markdown('<div class="filter-container">', unsafe_allow_html=True)
                st.subheader(f"Filters for {sku}")
                
                filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([3, 3, 2, 1])
                
                with filter_col1:
                    region_filter_options = ["All Regions"] + all_regions
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