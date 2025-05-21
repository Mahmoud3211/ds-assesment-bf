import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os
from tqdm import tqdm
from .config import get_settings, Settings, ManageDir
# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

class Datasets:
    def __init__(self):
        self.settings = get_settings()
        self.manage_dir = ManageDir()
    
    def generate_product_ids(self, num_products):
        """Generate unique product IDs."""
        return [f"P{i:04d}" for i in range(1, num_products + 1)]

    def generate_forecast_dataset(self, product_ids, start_date, num_days):
        """
        Generate a toy forecast dataset for the given products and date range.
        
        Args:
            product_ids: List of product IDs
            start_date: Start date for the forecast
        num_days: Number of days to forecast
        
        Returns:
            DataFrame with columns: product_id, date, forecasted_sales
        """
        data = []
    
        for product_id in tqdm(product_ids, desc="Generating forecast dataset"):
            # Base demand for this product (varies between products)
            base_demand = np.random.randint(self.settings.BASE_DEMAND_MIN, self.settings.BASE_DEMAND_MAX)
        
            # Variability factor for this product
            variability = np.random.uniform(0.1, 0.5)
        
            for day in range(num_days):
                current_date = start_date + timedelta(days=day)
            
                # Add some randomness and weekly patterns, 3 = Thursday, 4 = Friday, 5 = Saturday
                day_of_week_factor = 1.0 + (0.3 if current_date.weekday() in [3, 4, 5] else 0)  # Weekend boost
                random_factor = np.random.normal(1.0, variability)
            
                # Ensure random_factor is positive and reasonable
                random_factor = max(0.5, min(random_factor, 1.5))
            
                # Calculate forecasted quantity
                forecasted_qty = round(base_demand * day_of_week_factor * random_factor)
            
                data.append({
                    self.settings.FORCAST_PRODUCT_ID: product_id,
                    self.settings.FORCAST_DATE: current_date.strftime('%Y-%m-%d'),
                    self.settings.FORCAST_FORECASTED_SALES: forecasted_qty
                })
    
        return pd.DataFrame(data)

    def generate_inventory_dataset(self, product_ids, start_date, end_date):
        """
        Generate a toy inventory dataset with batches for each product.
        
        Args:
            product_ids: List of product IDs
            
        Returns:
            DataFrame with columns: product_id, batch_id, expiry_date, inventory 
        """
        data = []
        
        for product_id in tqdm(product_ids, desc="Generating inventory dataset"):
            # Determine number of batches for this product (at least MIN_BATCHES_PER_PRODUCT)
            num_batches = random.randint(self.settings.MIN_BATCHES_PER_PRODUCT, self.settings.MAX_BATCHES_PER_PRODUCT)
            
            # Base inventory level for this product
            base_inventory = np.random.randint(self.settings.BASE_INVENTORY_MIN, self.settings.BASE_INVENTORY_MAX)
            
            for batch_idx in range(num_batches):
                # Generate a batch ID
                batch_id = f"{product_id}_B{batch_idx + 1}"
                
                # Generate expiry date (within August 2024)
                # Earlier batches tend to expire sooner (still random)
                days_until_expiry = np.random.randint(
                    1 + batch_idx,  
                    (end_date - start_date).days + 1  # Maximum is August 31
                )
                expiry_date = end_date - timedelta(days=days_until_expiry)
                
                # Generate quantity for this batch
                # Distribute the base inventory across batches with some randomness
                quantity_factor = np.random.uniform(0.5, 1.5) / num_batches
                inventory = max(1, int(base_inventory * quantity_factor))
                
                data.append({
                    self.settings.INVENTORY_PRODUCT_ID: product_id,
                    self.settings.INVENTORY_BATCH_ID: batch_id,
                    self.settings.INVENTORY_EXPIRY_DATE: expiry_date.strftime('%Y-%m-%d'),
                    self.settings.INVENTORY_INVENTORY: inventory
                })
        
        return pd.DataFrame(data)

    def generate_datasets(self):
        """Generate forecast and inventory datasets."""
        
        start_date = datetime.strptime(self.settings.START_DATE, '%Y-%m-%d')
        end_date = datetime.strptime(self.settings.END_DATE, '%Y-%m-%d')

        # Generate product IDs
        product_ids = self.generate_product_ids(self.settings.NUM_PRODUCTS)
        
        # Generate forecast dataset
        forecast_df = self.generate_forecast_dataset(product_ids, start_date, self.settings.FORECAST_DAYS)
        
        # Generate inventory dataset
        inventory_df = self.generate_inventory_dataset(product_ids, start_date, end_date)
        
        # Save datasets to CSV files
        forecast_df.to_csv(self.manage_dir.get_forecast_path(), index=False)
        print(f"Generated forecast data for {len(product_ids)} products over {self.settings.FORECAST_DAYS} days") 
        
        inventory_df.to_csv(self.manage_dir.get_inventory_path(), index=False)
        print(f"Generated inventory data with {len(inventory_df)} batches")
        
        # Display sample of each dataset
        print("\nSample forecast data:")
        print(forecast_df.head())
        
        print("\nSample inventory data:")
        print(inventory_df.head())
        
        # Verify constraints
        self.verify_datasets(forecast_df, inventory_df, product_ids)

    def verify_datasets(self, forecast_df, inventory_df, product_ids):
        """Verify that the generated datasets meet all requirements."""
        print("\nVerifying datasets...")
        
        # Check forecast date range
        min_date = pd.to_datetime(forecast_df[self.settings.FORCAST_DATE]).min()
        max_date = pd.to_datetime(forecast_df[self.settings.FORCAST_DATE]).max()
        print(f"Forecast date range: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
        
        # Check inventory expiry dates
        min_expiry = pd.to_datetime(inventory_df[self.settings.INVENTORY_EXPIRY_DATE]).min()
        max_expiry = pd.to_datetime(inventory_df[self.settings.INVENTORY_EXPIRY_DATE]).max()
        print(f"Inventory expiry date range: {min_expiry.strftime('%Y-%m-%d')} to {max_expiry.strftime('%Y-%m-%d')}")
        
        # Check batches per product
        batches_per_product = inventory_df.groupby(self.settings.INVENTORY_PRODUCT_ID).size()
        min_batches = batches_per_product.min()
        print(f"Minimum batches per product: {min_batches}")
        
        # Check if all products have forecast and inventory
        products_with_forecast = forecast_df[self.settings.FORCAST_PRODUCT_ID].unique()
        products_with_inventory = inventory_df[self.settings.INVENTORY_PRODUCT_ID].unique()
        
        missing_forecast = set(product_ids) - set(products_with_forecast)
        missing_inventory = set(product_ids) - set(products_with_inventory)
        
        if missing_forecast:
            print(f"WARNING: {len(missing_forecast)} products missing from forecast data")
        else:
            print("All products have forecast data ✓")
            
        if missing_inventory:
            print(f"WARNING: {len(missing_inventory)} products missing from inventory data")
        else:
            print("All products have inventory data ✓")
