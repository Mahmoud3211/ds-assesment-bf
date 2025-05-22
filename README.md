# Days Forward Coverage Dashboard

This project implements a comprehensive solution for inventory management and supply chain planning through the calculation and visualization of "Days Forward Coverage". The application includes a user-friendly dashboard that allows users to upload their own data, generate synthetic datasets, and analyze inventory coverage metrics.

## Project Overview

Days Forward Coverage (DFC) is a critical metric that measures how many days the current inventory can cover anticipated demand. This helps organizations:
- Understand current inventory levels
- Identify products at risk of stock-outs
- Plan future production and procurement effectively
- Optimize inventory management strategies

## Features

- **Interactive Dashboard**: Visualize Days Forward Coverage metrics with an intuitive Streamlit interface
- **Data Upload**: Upload your own forecast and inventory datasets
- **Synthetic Data Generation**: Generate realistic toy datasets with configurable parameters
- **Data Visualization**: Explore forecast and inventory data before calculating coverage
- **Coverage Analysis**: View top and bottom products by coverage, identify critical products
- **Filtering**: Filter products to focus on specific inventory situations

## Quick Start with Docker

The easiest way to run the application is using Docker. No Python installation or manual setup required!

### Prerequisites

- Docker installed on your system ([Get Docker](https://docs.docker.com/get-docker/))

### Build and Run

1. Clone this repository
2. Open a terminal in the project directory
3. Build the Docker image:

```bash
docker build -t my-username/dfc-dashboard .
```

4. Run the container:

```bash
docker run -d -p [your_port]:8501 --name dfc-dashboard my-username/dfc-dashboard:latest
```

5. Access the dashboard at [http://localhost:[your_port]](http://localhost:[your_port]) in your browser

### Docker Commands Reference

- **Stop the container**: `docker stop dfc-dashboard`
- **Start an existing container**: `docker start dfc-dashboard`
- **Remove the container**: `docker rm dfc-dashboard`
- **View logs**: `docker logs dfc-dashboard`

## Project Structure

```
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose configuration
├── README.md              # This documentation
├── requirements.txt       # Python dependencies
└── src/                   # Source code
    ├── dashboard.py       # Main Streamlit dashboard application
    ├── helpers/           # Helper modules
    │   ├── config.py      # Configuration settings
    │   ├── datasets.py    # Dataset generation utilities
    │   └── dfc_algo.py    # Days Forward Coverage algorithm
    └── data/              # Data directory (created at runtime)
```

## Dashboard User Guide

This section provides a quick guide to using the Days Forward Coverage Dashboard.

### Getting Started

1. **Launch the Dashboard**: After starting the application, you'll see the main dashboard interface with a sidebar on the left and the main content area.

2. **Data Source Selection**: In the sidebar, you'll find three options for loading data:
   - **Upload Data**: Upload your own CSV files for forecast and inventory data
   - **Generate Data**: Create synthetic datasets with configurable parameters
   - **Use Existing Data**: Load previously saved datasets from the data directory

3. **Data Requirements**: 
   - For uploading, ensure your CSV files match the expected format (see Data Format section)
   - When generating data, you can specify the number of products and date range

### Dashboard Navigation

#### Sidebar Controls

- **Data Source**: Select how to load data (upload, generate, or use existing)
- **Calculate Coverage**: Button appears when forecast and inventory data are loaded but DFC hasn't been calculated
- **Reset Dashboard**: Clear all loaded data and start fresh
- **Filters**: Filter products by ID when DFC data is available

#### Main Dashboard Sections

1. **Data Exploration**:
   - View visualizations of your forecast and inventory data
   - Explore patterns and distributions before calculating DFC

2. **Days Forward Coverage Analysis**:
   - Overview: See distribution of DFC across all products and summary statistics
   - Top/Bottom Products: Identify products with highest and lowest coverage
   - Critical Products: View products with less than 7 days of coverage (requiring attention)

### Using the Dashboard

#### Workflow

1. **Load Data**: Either upload your files, generate synthetic data, or use existing files
2. **Explore Data**: Review the forecast and inventory visualizations to understand your data
3. **Calculate Coverage**: Click the "Calculate Coverage" button in the sidebar
4. **Analyze Results**: Examine the DFC metrics and identify products needing attention
5. **Filter Products**: Use the sidebar filters to focus on specific products

#### Tips

- **Data Generation**: If you don't have your own data, use the "Generate Data" option to create realistic test datasets
- **Critical Products**: Pay special attention to products with less than 7 days of coverage (highlighted in the dashboard)
- **Reset**: If you want to start over or load different data, use the "Reset Dashboard" button
- **Hover Interactions**: Hover over charts to see detailed information about specific data points

## Data Format

The application works with the following data formats:

### Forecast Dataset

A CSV file with the following columns (as per the config file):
- `product_id`: Unique identifier for each product
- `date`: Date of the forecast (YYYY-MM-DD format)
- `forecasted_sales`: Predicted demand for that product on that date

### Inventory Dataset

A CSV file with the following columns (as per the config file):
- `product_id`: Unique identifier for each product
- `batch_id`: Unique identifier for each inventory batch
- `expiry_date`: Expiry date of the batch (YYYY-MM-DD format)
- `inventory`: Available quantity in the batch

## Implementation Details

### Days Forward Coverage Calculation

The calculation follows these steps:

1. Filter out expired inventory based on the reference date
2. Process forecast data chronologically
3. For each day and product:
   - Check if there's enough inventory to cover the forecasted demand
   - Update inventory using a FIFO (First In, First Out) approach
   - Account for expiry dates when determining available inventory
4. Count how many consecutive days can be covered with the available inventory

### Key Algorithms

- **FIFO Inventory Consumption**: Inventory is consumed in order of expiration date
- **Batch-Level Tracking**: Inventory is tracked at the batch level for accurate expiration handling
- **Dynamic Recalculation**: Coverage is recalculated when inventory or forecast data changes

## Running Without Docker (Alternative)

If you prefer to run the application without Docker:

1. Ensure Python 3.9 is installed
2. Clone this repository
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the dashboard:
   ```bash
   cd src
   streamlit run dashboard.py
   ```

## Running Core Functions Directly

If you want to use the core functionality without the dashboard interface, you can run the main scripts directly:

### Generate Datasets

To generate synthetic datasets for forecast and inventory data:

```bash
cd src
```

```bash
python generate_datasets.py
```

This will create the following files in the data directory (as specified in `src/.env`):
- Forecast data: `data/forecast_data.csv` (or as configured)
- Inventory data: `data/inventory_data.csv` (or as configured)

### Calculate Days Forward Coverage

To calculate Days Forward Coverage using existing datasets:

```bash
python days_forward_coverage.py
```

This will:
- Read the forecast and inventory datasets
- Calculate Days Forward Coverage for each product
- Save the results to `data/days_forward_coverage.csv` (or as configured in `src/.env`)
- Display summary statistics in the console

### Output Files

All generated files will be saved in the `data/` directory (or as configured in `src/.env`):

- **Forecast Data**: `data/forecast_data.csv` (default path)
- **Inventory Data**: `data/inventory_data.csv` (default path)
- **DFC Results**: `data/days_forward_coverage.csv` (default path)

You can modify these paths and other settings in the `src/.env` configuration file.

## Configuration

The application's behavior can be configured to be as generic as possible by modifying the `.env` file in the `src` directory. Key settings include:

- Data file paths and names
- Column name mappings
- Default date ranges
- Number of products for synthetic data

## Future Improvements

The following enhancements are planned for future iterations of this project:

### Data Integration
- Make uploading datasets more generic by supporting additional data sources:
  - SQL databases (MySQL, PostgreSQL, SQL Server)
  - NoSQL databases (MongoDB, Cassandra)

### Advanced Forecasting
- Implement statistical forecasting algorithms:
  - ARIMA (AutoRegressive Integrated Moving Average)
  - Prophet (Facebook's time series forecasting tool)
  - Exponential Smoothing methods

### Machine Learning Integration
- Incorporate machine learning models for demand prediction:
  - Regression models (Random Forest, XGBoost)
  - Deep learning approaches (LSTM, Transformer networks)
  - Ensemble methods for improved accuracy

### LLM-Powered Assistant
- Integrate Large Language Models to provide an AI inventory expert:
  - Natural language interface for querying inventory status
  - Intelligent recommendations for inventory optimization
  - Automated insights and explanations of DFC metrics
  - Conversational interface for non-technical users to interact with inventory data

### Comparative Analysis
- Develop tools to compare results between different approaches:
  - Accuracy metrics (MAPE, RMSE, MAE)
  - Visualization of prediction differences
  - Performance benchmarking
  - Sensitivity analysis for different parameters

## Author

Mahmoud Nada
