
import logging
from typing import Dict, Any

from app.services.data_ingestion.base import BaseIngestor
from app.infrastructure.api_clients.openmeteo import OpenMeteoClient

logger = logging.getLogger(__name__)

class WeatherIngestor(BaseIngestor):
    """Ingestor for OpenMeteo Weather Data."""
    
    @property
    def name(self) -> str:
        return "Weather"
        
    @property
    def interval_hours(self) -> int:
        return self.config.WEATHER_UPDATE_INTERVAL_HOURS
        
    def ingest(self) -> Dict[str, Any]:
        logger.info(f"Starting {self.name} ingestion...")
        
        client = OpenMeteoClient()
        countries, _ = client.get_countries()
        
        # Target year 2024 for stability
        target_year = 2024
        
        all_data = []
        errors = []
        
        for country in countries:
            code = country['code']
            try:
                data, err = client.get_data(
                    code, 
                    'temperature_2m_mean', 
                    start_year=target_year, 
                    end_year=target_year
                )
                if data:
                    all_data.extend(data)
                if err:
                    errors.append(f"{code}: {err}")
            except Exception as e:
                errors.append(f"{code}: {str(e)}")
                
        if all_data:
            filename = f"weather_{target_year}.parquet"
            self.service.save_to_lake(all_data, filename)
            logger.info(f"Saved {len(all_data)} weather records.")
            
        return {
            "status": "success" if all_data else "partial_failure",
            "records_count": len(all_data),
            "errors": errors,
            "files_created": [f"weather_{target_year}.parquet"] if all_data else []
        }
