
import logging
from typing import Dict, Any

from app.services.data_ingestion.base import BaseIngestor
from app.infrastructure.api_clients.openmeteo import OpenMeteoClient

logger = logging.getLogger(__name__)

class WeatherIngestor(BaseIngestor):
    """Ingestor for OpenMeteo Weather Data, driven by indicators.yaml."""
    
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
        target_year = 2024
        
        config_indicators = self.configured_indicators
        # Weather API is tricky, 'temperature_2m_mean' is usually the standard one we support
        # But let's try to support whatever is in config if client supports it
        if config_indicators:
             indicators = [i['code'] for i in config_indicators]
        else:
             indicators = ['temperature_2m_mean']

        all_data = []
        errors = []
        
        for indicator in indicators:
            for country in countries:
                code = country['code']
                try:
                    data, err = client.get_data(
                        code, 
                        indicator, 
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
