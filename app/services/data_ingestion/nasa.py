
import logging
from typing import Dict, Any
from app.services.data_ingestion.base import BaseIngestor
from app.infrastructure.api_clients.nasa import NASAClient

logger = logging.getLogger(__name__)

class NasaIngestor(BaseIngestor):
    """Ingestor for NASA POWER Data."""
    
    @property
    def name(self) -> str:
        return "NASA"
        
    @property
    def interval_hours(self) -> int:
        return self.config.NASA_UPDATE_INTERVAL_HOURS
        
    def ingest(self) -> Dict[str, Any]:
        logger.info("Starting NASA ingestion...")
        
        client = NASAClient()
        # Solar Irradiance for a few locations
        indicator = "ALLSKY_SFC_SW_DWN"
        countries = ['USA', 'CHN']
        target_year = 2023 # NASA Power usually has lag
        
        all_data = []
        errors = []
        
        for country in countries:
            try:
                data, err = client.get_data(country, indicator, start_year=target_year, end_year=target_year)
                if data:
                    all_data.extend(data)
                if err:
                    errors.append(f"{country}: {err}")
            except Exception as e:
                errors.append(f"{country}: {str(e)}")
                
        if all_data:
            filename = f"nasa_solar_{target_year}.parquet"
            self.service.save_to_lake(all_data, filename)
            
        return {
            "status": "success" if all_data else "partial_failure",
            "records_count": len(all_data),
            "errors": errors,
            "files_created": [f"nasa_solar_{target_year}.parquet"] if all_data else []
        }
