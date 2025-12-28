
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List

from app.core.data_config import DataConfig
from app.services.data_lake_service import DataLakeService

logger = logging.getLogger(__name__)

class BaseIngestor(ABC):
    """
    Abstract base class for data ingestors.
    Handles configuration, service access, and update scheduling logic.
    """
    
    def __init__(self, service: DataLakeService):
        self.service = service
        self.config = DataConfig()
        
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the data source."""
        pass
        
    @property
    @abstractmethod
    def interval_hours(self) -> int:
        """Update interval in hours."""
        pass
        
    @abstractmethod
    def ingest(self) -> Dict[str, Any]:
        """
        Perform ingestion.
        Returns metadata about the operation (status, records_count, errors).
        """
        pass
        
    def should_update(self) -> bool:
        """
        Check if update is needed based on last modification time of the most recent file.
        Returns True if update is needed (or never ran), False otherwise.
        """
        latest_ts = 0
        files = self.service.get_file_info()
        
        # Heuristic: Find files starting with {name_lower}_
        # e.g. weather_2024.parquet for 'Weather'
        prefix = f"{self.name.lower()}_"
        
        found_file = False
        for f in files:
            if f['filename'].startswith(prefix):
                 found_file = True
                 # We stored 'modified_ts' in local file info
                 if 'modified_ts' in f:
                     ts = f['modified_ts']
                 else:
                     # Fallback to parsing string if needed, but service now provides ts
                     try:
                         dt = datetime.fromisoformat(f['modified'])
                         ts = dt.timestamp()
                     except:
                         continue
                         
                 if ts > latest_ts:
                     latest_ts = ts
                     
        if not found_file:
            logger.info(f"Source {self.name}: No files found. Update required.")
            return True 
            
        # Check diff
        hours_since = (time.time() - latest_ts) / 3600
        is_stale = hours_since >= self.interval_hours
        
        status = "STALE" if is_stale else "FRESH"
        logger.info(f"Source {self.name}: {status} (Last run {hours_since:.2f}h ago. Interval: {self.interval_hours}h).")
        
        return is_stale
