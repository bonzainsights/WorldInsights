
import os
from dotenv import load_dotenv

load_dotenv()

class DataConfig:
    """Configuration for Data Lake ingestion intervals and storage settings."""
    
    # Storage Configuration
    STORAGE_TYPE = os.getenv('DATA_STORAGE_TYPE', 'local').lower() # 'local' or 's3'
    DATA_LAKE_PATH = os.getenv('DATA_LAKE_PATH', 'data_lake') # Local path or S3 bucket URL
    
    # S3 Credentials (if needed)
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    
    # DuckDB Settings
    DUCKDB_MEMORY_LIMIT = os.getenv('DUCKDB_MEMORY_LIMIT', '1GB')

    # Update Intervals (in hours)
    # Default: Weather/Stocks/News every 6 hours, others every 30 days
    WEATHER_UPDATE_INTERVAL_HOURS = int(os.getenv('DATA_WEATHER_UPDATE_INTERVAL', 6))
    STOCKS_UPDATE_INTERVAL_HOURS = int(os.getenv('DATA_STOCKS_UPDATE_INTERVAL', 6))
    NEWS_UPDATE_INTERVAL_HOURS = int(os.getenv('DATA_NEWS_UPDATE_INTERVAL', 6))
    
    WORLDBANK_UPDATE_INTERVAL_HOURS = int(os.getenv('DATA_WORLDBANK_UPDATE_INTERVAL', 720))
    WHO_UPDATE_INTERVAL_HOURS = int(os.getenv('DATA_WHO_UPDATE_INTERVAL', 720))
    FAO_UPDATE_INTERVAL_HOURS = int(os.getenv('DATA_FAO_UPDATE_INTERVAL', 720))
    NASA_UPDATE_INTERVAL_HOURS = int(os.getenv('DATA_NASA_UPDATE_INTERVAL', 720))
    
    @classmethod
    def get_interval(cls, source_name: str) -> int:
        """Get update interval in hours for a specific source."""
        mapping = {
            'weather': cls.WEATHER_UPDATE_INTERVAL_HOURS,
            'stocks': cls.STOCKS_UPDATE_INTERVAL_HOURS,
            'news': cls.NEWS_UPDATE_INTERVAL_HOURS,
            'worldbank': cls.WORLDBANK_UPDATE_INTERVAL_HOURS,
            'who': cls.WHO_UPDATE_INTERVAL_HOURS,
            'fao': cls.FAO_UPDATE_INTERVAL_HOURS,
            'nasa': cls.NASA_UPDATE_INTERVAL_HOURS,
        }
        return mapping.get(source_name.lower(), 24) # Default to 24h if unknown
