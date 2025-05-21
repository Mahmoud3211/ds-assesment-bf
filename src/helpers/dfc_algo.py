import pandas as pd
from datetime import datetime, timedelta
import os
from tqdm import tqdm
from .config import get_settings, ManageDir

class DFCAlgo:
    def __init__(self):
        self.settings = get_settings()
        self.manage_dir = ManageDir()
    
    def _calculate_days_covered(self, product_forecast, product_inventory, start_date=None):
        """
        Helper method to calculate days forward coverage for a specific product.
        
        Args:
            product_forecast (DataFrame): Forecast data for a specific product
            product_inventory (DataFrame): Inventory data for a specific product
            start_date (datetime, optional): The reference date for calculation
            
        Returns:
            tuple: (days_covered, total_inventory)
        """
        # Make copies to avoid modifying the original data
        product_forecast = product_forecast.copy()
        product_inventory = product_inventory.copy()
        
        # Filter by start date if provided
        if start_date is not None:
            product_forecast = product_forecast[product_forecast[self.settings.FORCAST_DATE] >= start_date]
            product_inventory = product_inventory[product_inventory[self.settings.INVENTORY_EXPIRY_DATE] >= start_date]
        
        # Sort inventory by expiry date (FIFO - First In, First Out)
        product_inventory = product_inventory.sort_values(self.settings.INVENTORY_EXPIRY_DATE)
        
        # Sort forecast by date
        product_forecast = product_forecast.sort_values(self.settings.FORCAST_DATE)
        
        # Calculate total inventory
        total_inventory = product_inventory[self.settings.INVENTORY_INVENTORY].sum()
        
        # If no inventory or no forecast, return 0 days covered
        if product_inventory.empty or product_forecast.empty:
            return 0, total_inventory
        
        # Calculate days forward coverage
        days_covered = 0
        remaining_inventory = total_inventory
        
        for _, forecast_row in product_forecast.iterrows():
            forecast_date = forecast_row[self.settings.FORCAST_DATE]
            daily_demand = forecast_row[self.settings.FORCAST_FORECASTED_SALES]
            
            # Remove expired inventory for this date
            product_inventory = product_inventory[product_inventory[self.settings.INVENTORY_EXPIRY_DATE] >= forecast_date]
            
            # Recalculate remaining inventory after removing expired items
            if product_inventory.empty:
                remaining_inventory = 0
            else:
                remaining_inventory = product_inventory[self.settings.INVENTORY_INVENTORY].sum()
            
            # If we have enough inventory to cover this day's demand
            if remaining_inventory >= daily_demand:
                days_covered += 1
                
                # Update inventory (FIFO consumption)
                demand_to_fulfill = daily_demand
                
                for idx, inv_row in product_inventory.iterrows():
                    batch_quantity = inv_row[self.settings.INVENTORY_INVENTORY]
                    
                    if batch_quantity >= demand_to_fulfill:
                        # This batch can fulfill all remaining demand
                        product_inventory.at[idx, self.settings.INVENTORY_INVENTORY] = batch_quantity - demand_to_fulfill
                        break
                    else:
                        # This batch is fully consumed, move to next
                        demand_to_fulfill -= batch_quantity
                        product_inventory.at[idx, self.settings.INVENTORY_INVENTORY] = 0
            else:
                # Not enough inventory to cover demand, stop counting
                break
        
        return days_covered, total_inventory
    
    def calculate_dfc(self, forecast_df, inventory_df, current_date=None, save_csv=True):
        """
        Calculate Days Forward Coverage for each product based on forecast and inventory data.
        
        Args:
            forecast_df (DataFrame): Forecast dataset with columns:
                - FORCAST_PRODUCT_ID: Unique identifier for each product
                - FORCAST_DATE: Date of the forecast (YYYY-MM-DD format)
                - FORCAST_FORECASTED_SALES: Predicted demand for that product on that date
                
            inventory_df (DataFrame): Inventory dataset with columns:
                - INVENTORY_PRODUCT_ID: Unique identifier for each product
                - INVENTORY_BATCH_ID: Unique identifier for each inventory batch
                - INVENTORY_INVENTORY: Available quantity in the batch
                - INVENTORY_EXPIRY_DATE: Expiry date of the batch (YYYY-MM-DD format)
                
            current_date (str, optional): The reference date for the calculation (YYYY-MM-DD format).
                If None, the earliest date in the forecast will be used.
                
        Returns:
            DataFrame: Days Forward Coverage for each product with columns:
                - COVERAGE_PRODUCT_ID: Unique identifier for each product
                - COVERAGE_DAYS_FORWARD_COVERAGE: Number of days the current inventory can cover
        """        
        
        # Convert date columns to datetime
        forecast_df = forecast_df.copy()
        inventory_df = inventory_df.copy()
        
        forecast_df[self.settings.FORCAST_DATE] = pd.to_datetime(forecast_df[self.settings.FORCAST_DATE])
        inventory_df[self.settings.INVENTORY_EXPIRY_DATE] = pd.to_datetime(inventory_df[self.settings.INVENTORY_EXPIRY_DATE])
        
        # If current_date is not provided, use the earliest date in the forecast
        if current_date is None:
            current_date = forecast_df[self.settings.FORCAST_DATE].min()
        else:
            current_date = pd.to_datetime(current_date)
        
        # Filter out expired inventory
        valid_inventory = inventory_df[inventory_df[self.settings.INVENTORY_EXPIRY_DATE] >= current_date].copy()
        
        # Filter future forecast dates
        future_forecast = forecast_df[forecast_df[self.settings.FORCAST_DATE] >= current_date].copy()
        
        # Sort forecast by date
        future_forecast = future_forecast.sort_values([self.settings.FORCAST_PRODUCT_ID, self.settings.FORCAST_DATE])
        
        # Get unique product IDs from both datasets
        all_products = set(future_forecast[self.settings.FORCAST_PRODUCT_ID].unique()) | set(valid_inventory[self.settings.INVENTORY_PRODUCT_ID].unique())
        
        results = []
        
        for product_id in tqdm(all_products, desc="Calculating Days Forward Coverage"):
            # Get product forecast
            product_forecast = future_forecast[future_forecast[self.settings.FORCAST_PRODUCT_ID] == product_id].copy()
            
            if product_forecast.empty:
                # No forecast for this product, can't calculate coverage
                results.append({
                    self.settings.COVERAGE_PRODUCT_ID: product_id,
                    self.settings.COVERAGE_DAYS_FORWARD_COVERAGE: 0,
                    self.settings.COVERAGE_TOTAL_INVENTORY: 0,
                    'has_forecast': False
                })
                continue
            
            # Get product inventory
            product_inventory = valid_inventory[valid_inventory[self.settings.INVENTORY_PRODUCT_ID] == product_id].copy()
            
            if product_inventory.empty:
                # No inventory for this product
                results.append({
                    self.settings.COVERAGE_PRODUCT_ID: product_id,
                    self.settings.COVERAGE_DAYS_FORWARD_COVERAGE: 0,
                    self.settings.COVERAGE_TOTAL_INVENTORY: 0,
                    'has_forecast': True
                })
                continue
            
            # Use the helper method to calculate days covered and total inventory
            days_covered, total_inventory = self._calculate_days_covered(
                product_forecast, product_inventory
            )
            
            results.append({
                self.settings.COVERAGE_PRODUCT_ID: product_id,
                self.settings.COVERAGE_DAYS_FORWARD_COVERAGE: days_covered,
                self.settings.COVERAGE_TOTAL_INVENTORY: total_inventory
            }) 
        
        coverage_df = pd.DataFrame(results)
        
        if save_csv:
            coverage_df.to_csv(self.manage_dir.get_coverage_path(), index=False)
            print(f"Saved coverage data to {self.manage_dir.get_coverage_path()}")
        
        return coverage_df

    def calculate_dfc_over_time(self, forecast_df, inventory_df, product_id):
        """Calculate how Days Forward Coverage changes day by day for a specific product."""
        # Filter data for the specific product
        product_forecast = forecast_df[forecast_df[self.settings.FORCAST_PRODUCT_ID] == product_id].copy()
        product_inventory = inventory_df[inventory_df[self.settings.INVENTORY_PRODUCT_ID] == product_id].copy()
        
        if product_forecast.empty or product_inventory.empty:
            return pd.DataFrame()
        
        # Sort forecast by date
        product_forecast = product_forecast.sort_values(self.settings.FORCAST_DATE)
        
        # Get all dates in the forecast
        dates = product_forecast[self.settings.FORCAST_DATE].unique()
        
        results = []
        
        # For each date, calculate DFC as if that date was the current date
        for current_date in dates:
            # Filter inventory and forecast for this date using the helper method
            days_covered, total_inventory = self._calculate_days_covered(
                product_forecast, 
                product_inventory,
                start_date=current_date
            )
            
            results.append({
                'date': current_date,
                'days_forward_coverage': days_covered,
                'total_inventory': total_inventory
            })
        
        return pd.DataFrame(results)
