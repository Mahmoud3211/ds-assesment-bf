import pandas as pd
import numpy as np
from datetime import datetime
import os
from helpers.config import get_settings, ManageDir
from helpers.dfc_algo import DFCAlgo
from tqdm import tqdm

def main():
    # Load datasets
    settings = get_settings()
    manage_dir = ManageDir()
    dfc_algo = DFCAlgo()
    forecast_path = manage_dir.get_forecast_path()
    inventory_path = manage_dir.get_inventory_path()
    
    if not (os.path.exists(forecast_path) and os.path.exists(inventory_path)):
        print("Error: Dataset files not found. Please run generate_datasets.py first.")
        return
    
    forecast_df = pd.read_csv(forecast_path)
    inventory_df = pd.read_csv(inventory_path)
    
    # Calculate Days Forward Coverage
    coverage_df = dfc_algo.calculate_dfc(forecast_df, inventory_df, save_csv=True)
    
    # Display summary statistics
    print("\nDays Forward Coverage Summary:")
    print(f"Total products analyzed: {len(coverage_df)}")
    print(f"Average days forward coverage: {coverage_df[settings.COVERAGE_DAYS_FORWARD_COVERAGE].mean():.2f} days")
    print(f"Minimum days forward coverage: {coverage_df[settings.COVERAGE_DAYS_FORWARD_COVERAGE].min()} days")
    print(f"Maximum days forward coverage: {coverage_df[settings.COVERAGE_DAYS_FORWARD_COVERAGE].max()} days")
    
    # Display products with low coverage (potential stock-outs)
    low_coverage = coverage_df[coverage_df[settings.COVERAGE_DAYS_FORWARD_COVERAGE] < 7]
    print(f"\nProducts with less than 7 days of coverage: {len(low_coverage)}")
    if not low_coverage.empty:
        print(low_coverage.head(10))
    
    # Display products with no inventory
    no_inventory = coverage_df[coverage_df[settings.COVERAGE_TOTAL_INVENTORY] == 0]
    print(f"\nProducts with no inventory: {len(no_inventory)}")
    if not no_inventory.empty and len(no_inventory) <= 10:
        print(no_inventory)

if __name__ == "__main__":
    main()
