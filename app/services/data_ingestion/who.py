
import logging
from typing import Dict, Any
from app.services.data_ingestion.base import BaseIngestor
from app.infrastructure.api_clients.who import WHOClient

logger = logging.getLogger(__name__)

class WhoIngestor(BaseIngestor):
    """Ingestor for WHO Data, driven by indicators.yaml."""
    
    @property
    def name(self) -> str:
        return "WHO"
        
    @property
    def interval_hours(self) -> int:
        return self.config.WHO_UPDATE_INTERVAL_HOURS
        
    def ingest(self) -> Dict[str, Any]:
        logger.info(f"Starting {self.name} ingestion...")
        
        client = WHOClient()
        
        config_indicators = self.configured_indicators
        if not config_indicators:
             logger.warning(f"No indicators configured for {self.name}")
             return {"status": "skipped", "reason": "no_config"}
             
        indicators = [i['code'] for i in config_indicators]
        countries = ['USA', 'GBR', 'IND'] 
        
        all_data = []
        errors = []
        
        for indicator in indicators:
            for country in countries:
                 try:
                     data, err = client.get_data(country, indicator)
                     if data:
                         all_data.extend(data)
                     if err:
                         errors.append(f"{country}-{indicator}: {err}")
                 except Exception as e:
                     errors.append(f"{country}-{indicator}: {str(e)}")
                 
        if all_data:
            filename = "who_health.parquet"
            self.service.save_to_lake(all_data, filename)
            
        return {
            "status": "success" if all_data else "partial_failure",
            "records_count": len(all_data),
            "errors": errors,
            "files_created": ["who_health.parquet"] if all_data else []
        }
