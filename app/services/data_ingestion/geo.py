
import logging
import requests
import json
from typing import Dict, Any

from app.services.data_ingestion.base import BaseIngestor

logger = logging.getLogger(__name__)

class GeoIngestor(BaseIngestor):
    """
    Ingestor for Geographic Data (Country Shapes/Polygons).
    Required for 3D Globe visualizations.
    Fetches low-res GeoJSON from a stable CDN (e.g. GitHub/NaturalEarth).
    """
    
    @property
    def name(self) -> str:
        return "Geo"
        
    @property
    def interval_hours(self) -> int:
        # Geo boundaries rarely change. Update yearly.
        return 24 * 365 
        
    def ingest(self) -> Dict[str, Any]:
        logger.info(f"Starting {self.name} ingestion...")
        
        # Using a reliable public source for country polygons (GeoJSON)
        # 110m resolution is good for web globes (lightweight)
        GEO_URL = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json"
        
        try:
            response = requests.get(GEO_URL, timeout=30)
            response.raise_for_status()
            geojson = response.json()
            
            # We can save this raw JSON directly or parse it.
            # For data lake consistency, saving as a special file.
            # DuckDB can read JSON/Parquet. Parquet is bad for nested GeoJSON geometry unless we flatten.
            # For now, let's save as JSON because frontend (Plotly/WebGL) expects standard GeoJSON.
            
            # However, DataLakeService expects List[Dict] to save as Parquet.
            # Special handling: We might want to save this file directly as .json
            # OR parse features into a flat table: [id, name, geometry_string]
            
            features = geojson.get('features', [])
            records = []
            for f in features:
                props = f.get('properties', {})
                geom = f.get('geometry')
                # Try to find ISO code. Different sources use different keys.
                # This specific source uses 'id' as ISO-3
                iso_code = f.get('id', 'UNK') 
                country_name = props.get('name', 'Unknown')
                
                records.append({
                    'country': iso_code,
                    'name': country_name,
                    'geometry': json.dumps(geom), # Store as string for Parquet
                    'source': 'johan/world.geo.json'
                })
                
            if records:
                filename = "geo_countries.parquet"
                self.service.save_to_lake(records, filename)
                logger.info(f"Saved {len(records)} country shapes.")
                
            return {
                "status": "success",
                "records_count": len(records),
                "errors": [],
                "files_created": ["geo_countries.parquet"]
            }
            
        except Exception as e:
            logger.error(f"Geo ingestion failed: {e}")
            return {
                "status": "error",
                "records_count": 0,
                "errors": [str(e)],
                "files_created": []
            }
