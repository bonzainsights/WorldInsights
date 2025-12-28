
import logging
from typing import Dict, Any
from app.services.data_ingestion.base import BaseIngestor
from app.infrastructure.api_clients.who import WHOClient

logger = logging.getLogger(__name__)

class WhoIngestor(BaseIngestor):
    """Ingestor for WHO Data."""
    
    @property
    def name(self) -> str:
        return "WHO"
        
    @property
    def interval_hours(self) -> int:
        return self.config.WHO_UPDATE_INTERVAL_HOURS
        
    def ingest(self) -> Dict[str, Any]:
        logger.info(f"Starting {self.name} ingestion...")
        
        client = WHOClient()
        # Life Expectancy at birth
        indicator = "WHOSIS_000001" 
        countries = ['USA', 'GBR', 'IND'] # Simplified for demo
        
        all_data = []
        errors = []
        
        for country in countries:
             try:
                 data, err = client.get_data(country, indicator)
                 if data:
                     all_data.extend(data)
                 if err:
                     errors.append(f"{country}: {err}")
             except Exception as e:
                 errors.append(f"{country}: {str(e)}")
                 
        if all_data:
            filename = "who_health.parquet"
            self.service.save_to_lake(all_data, filename)
            
        return {
            "status": "success" if all_data else "partial_failure",
            "records_count": len(all_data),
            "errors": errors,
            "files_created": ["who_health.parquet"] if all_data else []
        }
