import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import plotly.express as px
from datetime import datetime
import io
import time
from helpers.config import get_settings, ManageDir
from helpers.datasets import Datasets
from helpers.dfc_algo import DFCAlgo

# Get settings
settings = get_settings()
manage_dir = ManageDir()
datasets = Datasets()
dfc_algo = DFCAlgo()

# Set page configuration
st.set_page_config(
    page_title="Days Forward Coverage Dashboard",
    page_icon="📊",
    layout="wide"
)

# Initialize session state for tracking app state
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'forecast_df' not in st.session_state:
    st.session_state.forecast_df = None
if 'inventory_df' not in st.session_state:
    st.session_state.inventory_df = None
if 'coverage_df' not in st.session_state:
    st.session_state.coverage_df = None
if 'data_source' not in st.session_state:
    st.session_state.data_source = None

# Function to load data from files
@st.cache_data
def load_data_from_files():
    forecast_path = manage_dir.get_forecast_path()
    inventory_path = manage_dir.get_inventory_path()
    coverage_path = manage_dir.get_coverage_path()
    
    # Check if files exist
    forecast_exists = os.path.exists(forecast_path)
    inventory_exists = os.path.exists(inventory_path)
    coverage_exists = os.path.exists(coverage_path)
    
    # Load data if files exist
    forecast_df = pd.read_csv(forecast_path) if forecast_exists else None
    inventory_df = pd.read_csv(inventory_path) if inventory_exists else None
    coverage_df = pd.read_csv(coverage_path) if coverage_exists else None
    
    # Convert date columns to datetime
    if forecast_df is not None:
        forecast_df[settings.FORCAST_DATE] = pd.to_datetime(forecast_df[settings.FORCAST_DATE])
    
    if inventory_df is not None:
        inventory_df[settings.INVENTORY_EXPIRY_DATE] = pd.to_datetime(inventory_df[settings.INVENTORY_EXPIRY_DATE])
    
    return forecast_df, inventory_df, coverage_df, forecast_exists, inventory_exists, coverage_exists

# Function to generate synthetic data
def generate_data():
    start_date = datetime.strptime(settings.START_DATE, '%Y-%m-%d')
    end_date = datetime.strptime(settings.END_DATE, '%Y-%m-%d')
    
    # Generate product IDs
    product_ids = datasets.generate_product_ids(settings.NUM_PRODUCTS)
    
    # Generate forecast dataset
    with st.spinner('Generating forecast dataset...'):
        forecast_df = datasets.generate_forecast_dataset(product_ids, start_date, settings.FORECAST_DAYS)
    
    # Generate inventory dataset
    with st.spinner('Generating inventory dataset...'):
        inventory_df = datasets.generate_inventory_dataset(product_ids, start_date, end_date)
    
    # Convert date columns to datetime
    forecast_df[settings.FORCAST_DATE] = pd.to_datetime(forecast_df[settings.FORCAST_DATE])
    inventory_df[settings.INVENTORY_EXPIRY_DATE] = pd.to_datetime(inventory_df[settings.INVENTORY_EXPIRY_DATE])
    
    # Save datasets to CSV files
    forecast_df.to_csv(manage_dir.get_forecast_path(), index=False)
    inventory_df.to_csv(manage_dir.get_inventory_path(), index=False)
    
    return forecast_df, inventory_df

# Function to calculate Days Forward Coverage
def calculate_coverage(forecast_df, inventory_df):
    with st.spinner('Calculating Days Forward Coverage...'):
        coverage_df = dfc_algo.calculate_dfc(forecast_df, inventory_df, settings.START_DATE, save_csv=True)
    
    return coverage_df

# Dashboard title
st.title("Days Forward Coverage Dashboard")
st.markdown("### Mahmoud Nada's Data Scientist Technical Assessment")

# Data Source Selection
st.sidebar.header("Data Source")

# Create tabs for data source selection
data_source_tab = st.sidebar.radio(
    "Select Data Source:",
    ["Upload Data", "Generate Data", "Use Existing Data"]
)

# Handle data source selection
if data_source_tab == "Upload Data":
    st.sidebar.subheader("Upload Data Files")
    
    # File uploaders
    forecast_file = st.sidebar.file_uploader("Upload Forecast Data (CSV)", type="csv")
    inventory_file = st.sidebar.file_uploader("Upload Inventory Data (CSV)", type="csv")
    coverage_file = st.sidebar.file_uploader("Upload Days Forward Coverage Data (CSV)", type="csv", help="Optional")
    
    if st.sidebar.button("Load Uploaded Data"):
        # Check if required files are uploaded
        if forecast_file is None or inventory_file is None:
            st.sidebar.error("Please upload both forecast and inventory data files.")
        else:
            # Load data from uploaded files
            st.session_state.forecast_df = pd.read_csv(forecast_file)
            st.session_state.inventory_df = pd.read_csv(inventory_file)
            
            # Convert date columns to datetime
            st.session_state.forecast_df[settings.FORCAST_DATE] = pd.to_datetime(st.session_state.forecast_df[settings.FORCAST_DATE])
            st.session_state.inventory_df[settings.INVENTORY_EXPIRY_DATE] = pd.to_datetime(st.session_state.inventory_df[settings.INVENTORY_EXPIRY_DATE])
            
            # Check if coverage file is uploaded
            if coverage_file is not None:
                st.session_state.coverage_df = pd.read_csv(coverage_file)
            else:
                st.session_state.coverage_df = None
            
            st.session_state.data_loaded = True
            st.session_state.data_source = "upload"
            st.sidebar.success("Data loaded successfully!")
            st.rerun()

elif data_source_tab == "Generate Data":
    st.sidebar.subheader("Generate Synthetic Data")
    
    if st.sidebar.button("Generate Data"):
        # Generate synthetic data
        st.session_state.forecast_df, st.session_state.inventory_df = generate_data()
        st.session_state.coverage_df = None
        st.session_state.data_loaded = True
        st.session_state.data_source = "generate"
        st.sidebar.success("Data generated successfully!")
        st.rerun()

elif data_source_tab == "Use Existing Data":
    st.sidebar.subheader("Load Existing Data")
    
    if st.sidebar.button("Load Existing Data"):
        # Load data from files
        forecast_df, inventory_df, coverage_df, forecast_exists, inventory_exists, coverage_exists = load_data_from_files()
        
        if not forecast_exists or not inventory_exists:
            st.sidebar.error("Required data files not found. Please generate data first or upload files.")
        else:
            st.session_state.forecast_df = forecast_df
            st.session_state.inventory_df = inventory_df
            st.session_state.coverage_df = coverage_df
            st.session_state.data_loaded = True
            st.session_state.data_source = "existing"
            st.sidebar.success("Data loaded successfully!")
            st.rerun()

# Calculate Days Forward Coverage if needed
if st.session_state.data_loaded and st.session_state.forecast_df is not None and st.session_state.inventory_df is not None and st.session_state.coverage_df is None:
    st.sidebar.subheader("Calculate Days Forward Coverage")
    
    if st.sidebar.button("Calculate Coverage"):
        st.session_state.coverage_df = calculate_coverage(st.session_state.forecast_df, st.session_state.inventory_df)
        st.sidebar.success("Days Forward Coverage calculated successfully!")
        st.rerun()

# Reset dashboard
if st.session_state.data_loaded:
    if st.sidebar.button("Reset Dashboard"):
        st.session_state.data_loaded = False
        st.session_state.forecast_df = None
        st.session_state.inventory_df = None
        st.session_state.coverage_df = None
        st.session_state.data_source = None
        st.rerun()

# Sidebar filters (only show if coverage data is available)
if st.session_state.data_loaded and st.session_state.coverage_df is not None:
    st.sidebar.header("Filters")
    
    # Sort products by coverage (ascending)
    sorted_products = st.session_state.coverage_df.sort_values(settings.COVERAGE_PRODUCT_ID)[settings.COVERAGE_PRODUCT_ID].unique()
    
    # Select products
    selected_products = st.sidebar.multiselect(
        "Select Products:",
        options=sorted_products,
        default=sorted_products[:5]  # Default to 5 products with lowest coverage
    )
    
    # Filter by coverage range
    min_coverage = int(st.session_state.coverage_df[settings.COVERAGE_DAYS_FORWARD_COVERAGE].min())
    max_coverage = int(st.session_state.coverage_df[settings.COVERAGE_DAYS_FORWARD_COVERAGE].max())
    
    # coverage_range = st.sidebar.slider(
    #     "Days Forward Coverage Range:",
    #     min_value=min_coverage,
    #     max_value=max_coverage,
    #     value=(min_coverage, max_coverage)
    # )
    
    # Apply filters to coverage data
    filtered_coverage = st.session_state.coverage_df[
        (st.session_state.coverage_df[settings.COVERAGE_DAYS_FORWARD_COVERAGE] >= min_coverage) & 
        (st.session_state.coverage_df[settings.COVERAGE_DAYS_FORWARD_COVERAGE] <= max_coverage)
    ]
    
    if selected_products:
        filtered_coverage = filtered_coverage[filtered_coverage[settings.COVERAGE_PRODUCT_ID].isin(selected_products)]

# Main dashboard content
if not st.session_state.data_loaded:
    st.info("Please select a data source from the sidebar to get started.")
    
    st.markdown("""
    ### Getting Started
    
    This dashboard allows you to analyze Days Forward Coverage (DFC) for inventory management.
    
    You have three options to load data:
    
    1. **Upload Data**: Upload your own CSV files for forecast, inventory, and optionally DFC data
    2. **Generate Data**: Create synthetic data for testing and demonstration
    3. **Use Existing Data**: Load previously generated or saved data files
    
    If you only upload forecast and inventory data without DFC data, you can calculate it directly in the dashboard.
    """)
else:
    # Forecast and Inventory Data Exploration - Shown First
    st.header("Data Exploration")
    
    # Create tabs for different datasets
    tab1, tab2 = st.tabs(["Forecast Data", "Inventory Data"])
    
    with tab1:
        st.subheader("Forecast Dataset")
        
        if st.session_state.forecast_df is not None:
            # Summary of forecast data
            st.write(f"Total products: {st.session_state.forecast_df[settings.FORCAST_PRODUCT_ID].nunique()}")
            st.write(f"Date range: {st.session_state.forecast_df[settings.FORCAST_DATE].min().strftime('%Y-%m-%d')} to {st.session_state.forecast_df[settings.FORCAST_DATE].max().strftime('%Y-%m-%d')}")
            
            # Sample of forecast data
            st.dataframe(st.session_state.forecast_df.head(100), use_container_width=True)
            
            # Aggregate forecast by date
            daily_forecast = st.session_state.forecast_df.groupby(settings.FORCAST_DATE)[settings.FORCAST_FORECASTED_SALES].sum().reset_index()
            
            # Plot daily forecast
            fig = px.line(
                daily_forecast,
                x=settings.FORCAST_DATE,
                y=settings.FORCAST_FORECASTED_SALES,
                title='Total Daily Forecast',
                labels={settings.FORCAST_FORECASTED_SALES: 'Forecasted Sales', settings.FORCAST_DATE: 'Date'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Distribution of forecast values
            fig = px.histogram(
                st.session_state.forecast_df,
                x=settings.FORCAST_FORECASTED_SALES,
                nbins=30,
                title='Distribution of Forecasted Sales',
                labels={settings.FORCAST_FORECASTED_SALES: 'Forecasted Sales'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Inventory Dataset")
        
        if st.session_state.inventory_df is not None:
            # Summary of inventory data
            st.write(f"Total products: {st.session_state.inventory_df[settings.INVENTORY_PRODUCT_ID].nunique()}")
            st.write(f"Total batches: {len(st.session_state.inventory_df)}")
            st.write(f"Expiry date range: {st.session_state.inventory_df[settings.INVENTORY_EXPIRY_DATE].min().strftime('%Y-%m-%d')} to {st.session_state.inventory_df[settings.INVENTORY_EXPIRY_DATE].max().strftime('%Y-%m-%d')}")
            
            # Sample of inventory data
            st.dataframe(st.session_state.inventory_df.head(100), use_container_width=True)
            
            # Batches per product distribution
            batches_per_product = st.session_state.inventory_df.groupby(settings.INVENTORY_PRODUCT_ID).size().reset_index(name='batch_count')
            
            fig = px.histogram(
                batches_per_product,
                x='batch_count',
                nbins=20,
                title='Distribution of Batches per Product',
                labels={'batch_count': 'Number of Batches'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Expiry date distribution
            fig = px.histogram(
                st.session_state.inventory_df,
                x=settings.INVENTORY_EXPIRY_DATE,
                title='Distribution of Expiry Dates',
                labels={settings.INVENTORY_EXPIRY_DATE: 'Expiry Date'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Total inventory by product
            total_inventory = st.session_state.inventory_df.groupby(settings.INVENTORY_PRODUCT_ID)[settings.INVENTORY_INVENTORY].sum().reset_index()
            total_inventory = total_inventory.sort_values(settings.INVENTORY_INVENTORY, ascending=False).head(20)
            
            fig = px.bar(
                total_inventory,
                x=settings.INVENTORY_PRODUCT_ID,
                y=settings.INVENTORY_INVENTORY,
                title='Top 20 Products by Total Inventory',
                labels={settings.INVENTORY_INVENTORY: 'Total Inventory', settings.INVENTORY_PRODUCT_ID: 'Product ID'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Days Forward Coverage Analysis - Shown After Data Exploration
    if st.session_state.coverage_df is not None:
        st.header("Days Forward Coverage Analysis")
        
        # Create a two-column layout
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Days Forward Coverage Overview")
            
            # Summary statistics
            st.metric("Average Coverage", f"{st.session_state.coverage_df[settings.COVERAGE_DAYS_FORWARD_COVERAGE].mean():.1f} days")
            
            # Coverage distribution
            fig = px.histogram(
                st.session_state.coverage_df, 
                x=settings.COVERAGE_DAYS_FORWARD_COVERAGE,
                nbins=30,
                title='Distribution of Days Forward Coverage',
                labels={settings.COVERAGE_DAYS_FORWARD_COVERAGE: 'Days Forward Coverage'},
                color_discrete_sequence=['#3366CC']
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # # Time Series Chart (DFC Over Time)
            # st.subheader("Days Forward Coverage Over Time")
            
            # # Add a container for the loading indicator
            # loading_container = st.empty()
            
            # # Initialize or get the previous selection from session state
            # if 'selected_product_for_timeseries' not in st.session_state:
            #     # Default to a product with medium coverage
            #     medium_coverage_products = st.session_state.coverage_df.sort_values(settings.COVERAGE_DAYS_FORWARD_COVERAGE)
            #     if not medium_coverage_products.empty:
            #         default_product = medium_coverage_products.iloc[len(medium_coverage_products)//2][settings.COVERAGE_PRODUCT_ID]
            #     else:
            #         default_product = None
            #     st.session_state.selected_product_for_timeseries = default_product
            #     st.session_state.is_calculating_dfc = False
            
            # # Track if we need to show the loading indicator
            # if 'is_calculating_dfc' not in st.session_state:
            #     st.session_state.is_calculating_dfc = False
            
            # # Show loading indicator if calculation is in progress
            # if st.session_state.is_calculating_dfc:
            #     with loading_container:
            #         st.info(f"⏳ Loading DFC data for {st.session_state.selected_product_for_timeseries}... Please wait.")
            
            # # Product selection dropdown
            # selected_product = st.selectbox(
            #     "Select Product to View DFC Over Time:",
            #     options=st.session_state.coverage_df[settings.COVERAGE_PRODUCT_ID].unique(),
            #     index=list(st.session_state.coverage_df[settings.COVERAGE_PRODUCT_ID].unique()).index(st.session_state.selected_product_for_timeseries) 
            #           if st.session_state.selected_product_for_timeseries in st.session_state.coverage_df[settings.COVERAGE_PRODUCT_ID].unique() else 0,
            #     key="dfc_product_selector"
            # )
            
            # # Check if product selection has changed
            # if selected_product != st.session_state.selected_product_for_timeseries:
            #     st.session_state.selected_product_for_timeseries = selected_product
            #     st.session_state.is_calculating_dfc = True
            #     st.rerun()
            
            # # Calculate DFC over time for the selected product
            # with st.spinner(f"Calculating DFC over time for {selected_product}..."):
            #     # Show loading message in the container while calculating
            #     with loading_container:
            #         st.info(f"⏳ Loading DFC data for {selected_product}... Please wait.")
                    
            #     # Set flag to indicate calculation is in progress
            #     st.session_state.is_calculating_dfc = True
            #     dfc_over_time = dfc_algo.calculate_dfc_over_time(
            #         st.session_state.forecast_df, 
            #         st.session_state.inventory_df, 
            #         selected_product
            #     )
                
            #     # Clear the calculating flag once done
            #     st.session_state.is_calculating_dfc = False
                
            #     # Show success message in the loading container
            #     with loading_container:
            #         if not dfc_over_time.empty:
            #             st.success(f"✅ DFC data for {selected_product} loaded successfully!")
            #         else:
            #             st.warning(f"⚠️ No DFC data available for {selected_product}.")
                        
            #     # Add a small delay to ensure the success message is visible
            #     time.sleep(0.5)
            
            # if not dfc_over_time.empty:
            #     # Create time series chart
            #     fig = px.line(
            #         dfc_over_time,
            #         x='date',
            #         y='days_forward_coverage',
            #         title=f'Days Forward Coverage Over Time for {selected_product}',
            #         labels={'date': 'Date', 'days_forward_coverage': 'Days Forward Coverage'},
            #         markers=True
            #     )
                
            #     # Add a reference line at 7 days (critical threshold)
            #     fig.add_shape(
            #         type="line",
            #         x0=dfc_over_time['date'].min(),
            #         y0=7,
            #         x1=dfc_over_time['date'].max(),
            #         y1=7,
            #         line=dict(color="red", width=2, dash="dash"),
            #     )
                
            #     # Add annotation for the reference line
            #     fig.add_annotation(
            #         x=dfc_over_time['date'].max(),
            #         y=7,
            #         text="Critical Threshold (7 days)",
            #         showarrow=False,
            #         yshift=10,
            #         font=dict(color="red")
            #     )
                
            #     st.plotly_chart(fig, use_container_width=True)
                
            #     # Add insights about the DFC trend
            #     initial_dfc = dfc_over_time.iloc[0]['days_forward_coverage']
            #     final_dfc = dfc_over_time.iloc[-1]['days_forward_coverage']
            #     min_dfc = dfc_over_time['days_forward_coverage'].min()
            #     max_dfc = dfc_over_time['days_forward_coverage'].max()
                
            #     st.info(f"**DFC Trend Analysis for {selected_product}**:  \n"
            #            f"- Started with {initial_dfc} days of coverage  \n"
            #            f"- Ended with {final_dfc} days of coverage  \n"
            #            f"- Minimum: {min_dfc} days, Maximum: {max_dfc} days  \n"
            #            f"- {'⚠️ Product falls below critical threshold (7 days) at some point' if min_dfc < 7 else '✅ Product maintains healthy coverage throughout the period'}")
            # else:
            #     st.warning(f"No data available to calculate DFC over time for {selected_product}.")

        
        with col2:
            st.subheader("Top and Bottom Products by Coverage")
            
            # Create tabs for different views
            tab1, tab2 = st.tabs(["Top 10 Products", "Bottom 10 Products"])
            
            with tab1:
                top_products = st.session_state.coverage_df.nlargest(10, settings.COVERAGE_DAYS_FORWARD_COVERAGE)
                fig = px.bar(
                    top_products,
                    x=settings.COVERAGE_PRODUCT_ID,
                    y=settings.COVERAGE_DAYS_FORWARD_COVERAGE,
                    title='Top 10 Products by Days Forward Coverage',
                    labels={settings.COVERAGE_DAYS_FORWARD_COVERAGE: 'Days', settings.COVERAGE_PRODUCT_ID: 'Product ID'},
                    color=settings.COVERAGE_DAYS_FORWARD_COVERAGE,
                    color_continuous_scale='Viridis'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                st.subheader("Bottom 10 Products by Days Forward Coverage")
                bottom_products = st.session_state.coverage_df.nsmallest(10, settings.COVERAGE_DAYS_FORWARD_COVERAGE)
                
                # Format the table for better display
                display_columns = [
                    settings.COVERAGE_PRODUCT_ID, 
                    settings.COVERAGE_DAYS_FORWARD_COVERAGE,
                    settings.COVERAGE_TOTAL_INVENTORY
                ]
                
                # Display as a table with formatting
                st.dataframe(
                    bottom_products[display_columns],
                    use_container_width=True,
                    column_config={
                        settings.COVERAGE_PRODUCT_ID: "Product ID",
                        settings.COVERAGE_DAYS_FORWARD_COVERAGE: st.column_config.NumberColumn(
                            "Days Forward Coverage",
                            format="%d days",
                            help="Number of days the current inventory can cover"
                        ),
                        settings.COVERAGE_TOTAL_INVENTORY: st.column_config.NumberColumn(
                            "Total Inventory",
                            format="%d units",
                            help="Total inventory quantity available"
                        )
                    },
                    hide_index=True
                )
            
            # Products with critical coverage section (moved here for UI consistency)
            st.subheader("Products with Critical Coverage (< 7 days)")
            critical_products = st.session_state.coverage_df[st.session_state.coverage_df[settings.COVERAGE_DAYS_FORWARD_COVERAGE] < 7].sort_values(settings.COVERAGE_DAYS_FORWARD_COVERAGE)
            
            if critical_products.empty:
                st.success("No products with critical coverage! All products have at least 7 days of coverage.")
            else:
                # Format the table for better display
                display_columns = [
                    settings.COVERAGE_PRODUCT_ID, 
                    settings.COVERAGE_DAYS_FORWARD_COVERAGE,
                    settings.COVERAGE_TOTAL_INVENTORY
                ]
                
                # Display as a table with formatting
                st.dataframe(
                    critical_products[display_columns],
                    use_container_width=True,
                    column_config={
                        settings.COVERAGE_PRODUCT_ID: "Product ID",
                        settings.COVERAGE_DAYS_FORWARD_COVERAGE: st.column_config.NumberColumn(
                            "Days Forward Coverage",
                            format="%d days",
                            help="Number of days the current inventory can cover"
                        ),
                        settings.COVERAGE_TOTAL_INVENTORY: st.column_config.NumberColumn(
                            "Total Inventory",
                            format="%d units",
                            help="Total inventory quantity available"
                        )
                    },
                    hide_index=True
                )
                
                # Add warning message with count
                critical_count = len(critical_products)
                st.warning(f"⚠️ {critical_count} product{'s' if critical_count > 1 else ''} with less than 7 days of coverage. These products may need immediate attention.")
        
        # Coverage by product (for selected products)
        if 'selected_products' in locals() and selected_products:
            st.subheader(f"Coverage Details for Selected Products")
            
            # Filter data for selected products
            selected_coverage = st.session_state.coverage_df[st.session_state.coverage_df[settings.COVERAGE_PRODUCT_ID].isin(selected_products)]
            
            # Bar chart for selected products
            fig = px.bar(
                selected_coverage.sort_values(settings.COVERAGE_DAYS_FORWARD_COVERAGE),
                x=settings.COVERAGE_PRODUCT_ID,
                y=settings.COVERAGE_DAYS_FORWARD_COVERAGE,
                title='Days Forward Coverage for Selected Products',
                labels={settings.COVERAGE_DAYS_FORWARD_COVERAGE: 'Days', settings.COVERAGE_PRODUCT_ID: 'Product ID'},
                color=settings.COVERAGE_DAYS_FORWARD_COVERAGE,
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Detailed table
            st.dataframe(selected_coverage.sort_values(settings.COVERAGE_DAYS_FORWARD_COVERAGE, ascending=False), use_container_width=True)

# Footer
st.markdown("---")
st.markdown("Mahmoud Nada's Data Scientist Technical Assessment Dashboard")
