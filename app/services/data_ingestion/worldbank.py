
import logging
from typing import Dict, Any

from app.services.data_ingestion.base import BaseIngestor
from app.infrastructure.api_clients.worldbank import WorldBankClient

logger = logging.getLogger(__name__)

class WorldBankIngestor(BaseIngestor):
    """Ingestor for World Bank Data."""
    
    @property
    def name(self) -> str:
        return "WorldBank"
        
    @property
    def interval_hours(self) -> int:
        return self.config.WORLDBANK_UPDATE_INTERVAL_HOURS
        
    def ingest(self) -> Dict[str, Any]:
        logger.info(f"Starting {self.name} ingestion...")
        
        client = WorldBankClient()
        # Key Economic Indicators
        indicators = [
            'NY.GDP.MKTP.CD', # GDP
            'SP.POP.TOTL'     # Population
        ]
        countries = ['USA', 'CHN', 'GBR', 'DEU', 'JPN', 'IND']
        
        all_data = []
        errors = []
        
        for indicator in indicators:
            for country in countries:
                try:
                    data, err = client.get_data(country, indicator, start_year=2000, end_year=2024)
                    if data:
                        all_data.extend(data)
                    if err:
                        errors.append(f"{country}-{indicator}: {err}")
                except Exception as e:
                    errors.append(f"{country}-{indicator}: {str(e)}")
        
        if all_data:
            filename = "worldbank_indicators.parquet"
            self.service.save_to_lake(all_data, filename)
            logger.info(f"Saved {len(all_data)} WB records.")
            
        return {
            "status": "success" if all_data else "partial_failure",
            "records_count": len(all_data),
            "errors": errors,
            "files_created": ["worldbank_indicators.parquet"] if all_data else []
        }
