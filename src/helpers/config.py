from pydantic_settings import BaseSettings, SettingsConfigDict
import os
class Settings(BaseSettings):
    
    # General settings
    NUM_PRODUCTS: int
    FORECAST_DAYS: int
    START_DATE: str
    END_DATE: str

    BASE_DEMAND_MIN: int
    BASE_DEMAND_MAX: int
    MIN_BATCHES_PER_PRODUCT: int
    MAX_BATCHES_PER_PRODUCT: int
    BASE_INVENTORY_MIN: int
    BASE_INVENTORY_MAX: int

    DATA_DIR: str

    # Forcast dataset columns names
    FORCAST_FILE_NAME: str
    FORCAST_PRODUCT_ID: str
    FORCAST_DATE: str
    FORCAST_FORECASTED_SALES: str

    # Inventory dataset columns names
    INVENTORY_FILE_NAME: str
    INVENTORY_PRODUCT_ID: str
    INVENTORY_BATCH_ID: str
    INVENTORY_EXPIRY_DATE: str
    INVENTORY_INVENTORY: str

    # Coverage dataset columns names
    COVERAGE_FILE_NAME: str
    COVERAGE_PRODUCT_ID: str
    COVERAGE_DAYS_FORWARD_COVERAGE: str
    COVERAGE_TOTAL_INVENTORY: str

    class Config:
        env_file = ".env"
        
def get_settings() -> Settings:
    return Settings()
    
class ManageDir:
    def __init__(self):
        self.settings = get_settings()
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.data_dir = os.path.join(self.base_dir, self.settings.DATA_DIR)
        
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def get_forecast_path(self):
        return os.path.join(self.data_dir, self.settings.FORCAST_FILE_NAME)

    def get_inventory_path(self):
        return os.path.join(self.data_dir, self.settings.INVENTORY_FILE_NAME)

    def get_coverage_path(self):
        return os.path.join(self.data_dir, self.settings.COVERAGE_FILE_NAME)