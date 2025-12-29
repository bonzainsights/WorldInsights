
import logging
import time
import yaml
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.core.data_config import DataConfig
from app.services.data_lake_service import DataLakeService

logger = logging.getLogger(__name__)

class BaseIngestor(ABC):
    """
    Abstract base class for data ingestors.
    Handles configuration, service access, and update scheduling logic.
    Now supports loading indicators from data_lake/indicators.yaml.
    """
    
    def __init__(self, service: DataLakeService):
        self.service = service
        self.config = DataConfig()
        self._indicators_config = self._load_indicators_config()
        
    def _load_indicators_config(self) -> Dict[str, Any]:
        """Load indicators.yaml if it exists."""
        try:
            # Assume indicators.yaml is in data_lake/ dir
            # Or define a path in DataConfig. For now, relative to project root.
            # Base path logic:
            if self.config.STORAGE_TYPE == 'local':
                 config_path = os.path.join(self.config.DATA_LAKE_PATH, 'indicators.yaml')
                 if os.path.exists(config_path):
                     with open(config_path, 'r') as f:
                         return yaml.safe_load(f) or {}
            
            # TODO: Support S3 loading for config file itself if needed.
            # Fallback for now: try local project root path just in case
            local_fallback = "data_lake/indicators.yaml"
            if os.path.exists(local_fallback):
                with open(local_fallback, 'r') as f:
                    return yaml.safe_load(f) or {}
                    
        except Exception as e:
            logger.warning(f"Failed to load indicators.yaml: {e}")
            
        return {}

    @property
    def configured_indicators(self) -> List[Dict[str, str]]:
        """
        Get list of configured indicators for this source from YAML.
        Returns empty list if not found.
        """
        source_key = self.name.lower()
        if self._indicators_config and source_key in self._indicators_config:
            return self._indicators_config[source_key].get('indicators', [])
        return []

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
        prefix = f"{self.name.lower()}"
        
        found_file = False
        for f in files:
            if f['filename'].startswith(prefix):
                 found_file = True
                 if 'modified_ts' in f:
                     ts = f['modified_ts']
                 else:
                     try:
                         dt = datetime.fromisoformat(f['modified'])
                         ts = dt.timestamp()
                     except:
                         continue
                         
                 if ts > latest_ts:
                     latest_ts = ts
                     
        if not found_file:
            # logger.info(f"Source {self.name}: No files found. Update required.")
            return True 
            
        # Check diff
        hours_since = (time.time() - latest_ts) / 3600
        is_stale = hours_since >= self.interval_hours
        
        # status = "STALE" if is_stale else "FRESH"
        # logger.info(f"Source {self.name}: {status} (Last run {hours_since:.2f}h ago).")
        
        return is_stale
