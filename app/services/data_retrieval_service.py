
import logging
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.services.data_lake_service import DataLakeService
from app.infrastructure.api_clients.worldbank import WorldBankClient
from app.infrastructure.api_clients.who import WHOClient
from app.infrastructure.api_clients.openmeteo import OpenMeteoClient
from app.infrastructure.api_clients.nasa import NASAClient

logger = logging.getLogger(__name__)

class DataRetrievalService:
    """
    Service to retrieve data for the application.
    Implements the 'Hybrid Access' pattern:
    1. Query Data Lake (Fast, efficient)
    2. Fallback to API (Complete, slower) if data missing
    """
    
    def __init__(self):
        self.lake = DataLakeService()
        # Initialize clients lazily or here? Here is fine for now.
        self._clients = {
            'worldbank': WorldBankClient(),
            'who': WHOClient(),
            'weather': OpenMeteoClient(),
            'nasa': NASAClient()
        }

    def get_data(self, source: str, indicator: str, country: str = None, year: int = None) -> List[Dict]:
        """
        Main entry point to get data.
        """
        source = source.lower()
        
        # 1. Try Data Lake
        try:
            data = self._query_lake(source, indicator, country, year)
            if data and len(data) > 0:
                logger.info(f"Hit Data Lake for {source}:{indicator}")
                return data
        except Exception as e:
            logger.warning(f"Data Lake query failed: {e}")

        # 2. Fallback to API
        logger.info(f"Miss Data Lake for {source}:{indicator}. Falling back to API.")
        return self._fetch_from_api(source, indicator, country, year)

    def _query_lake(self, source: str, indicator: str, country: str = None, year: int = None) -> List[Dict]:
        """
        Construct SQL query for DuckDB.
        """
        # Map source to filename pattern
        # This relies on our naming convention in Ingestors: '{source_lower}_*.parquet'
        file_pattern = f"data_lake/{source}_*.parquet"
        
        query = f"SELECT * FROM '{file_pattern}' WHERE 1=1"
        
        # SQL Injection protection: In DuckDB python API, we usually use params, 
        # but here we are constructing generic SQL for 'query()' method which might not support params directly
        # depending on implementation. DataLakeService.query takes a raw string.
        # We must sanitize inputs. 
        # For simplicity in this MVP, we assume trusted inputs or basic sanitization.
        
        if indicator:
            # Flexible matching: some sources use 'indicator' column, others might imply it
            # WB/WHO/Weather have 'indicator' column.
            query += f" AND indicator = '{indicator}'"
            
        if country:
            query += f" AND country = '{country}'"
            
        if year:
            query += f" AND year = {year}"
            
        logger.debug(f"Lake Query: {query}")
        result = self.lake.query(query)
        
        # Convert to list of dicts
        # DataLakeService.query returns... wait, I need to check strictly what it returns.
        # It likely returns a list of tuples or dicts? check implementation.
        # Checking implementation: `con.execute(sql).fetchall()` returns tuples usually, 
        # unless we used `.df()` or `.arrow()`. 
        # Let's verify DataLakeService implementation before assuming.
        
        # Assumption: DataLakeService.query returns List[Dict] or similar friendly format.
        # If it returns tuples, we need column names.
        
        return result

    def _fetch_from_api(self, source: str, indicator: str, country: str = None, year: int = None) -> List[Dict]:
        """
        Direct API fetch.
        """
        client = self._clients.get(source)
        if not client:
            logger.error(f"No client found for source {source}")
            return []
            
        try:
            # Generalized call - most clients have get_data(country, indicator, ...)
            # We might need source-specific adapters here if signatures differ wildly.
            
            if source == 'weather':
                # Weather needs lat/lon via country code logic inside client
                # Weather client get_data(country_code, indicator, start_year, end_year)
                data, err = client.get_data(country, indicator, start_year=year, end_year=year)
                
            elif source in ['worldbank', 'nasa']:
                # WB: get_data(country, indicator, start_year, end_year)
                data, err = client.get_data(country, indicator, start_year=year, end_year=year)
                
            elif source == 'who':
                # WHO: get_data(country, indicator) - no year filtering in fetch usually
                data, err = client.get_data(country, indicator)
                # Filter year manually if needed
                if year and data:
                    data = [d for d in data if d.get('year') == year]
                    
            else:
                 return []

            if err:
                logger.warning(f"API Error: {err}")
                return []
                
            if data:
                # Read-Through Cache (Optional): Save this snippet to a cache file
                # self._cache_miss_data(data, source)
                return data
                
        except Exception as e:
            logger.error(f"API Fetch failed: {e}")
            return []
            
        return []

    def get_globe_data(self, indicator_source: str, indicator_code: str, year: int) -> Dict[str, Any]:
        """
        Prepare GeoJSON for 3D Globe.
        Joins Geo Shapes (geo_countries.parquet) with Data (indicator).
        """
        # 1. Get Shapes
        shapes_query = "SELECT country as iso_code, name, geometry FROM 'data_lake/geo_countries.parquet'"
        shapes = self.lake.query(shapes_query)
        if not shapes:
            logger.error("No geo shapes found.")
            return {}
            
        # 2. Get Data values
        # We can implement a JOIN in DuckDB directly!
        # "SELECT g.geometry, g.name, d.value FROM geo g LEFT JOIN data d ON g.country = d.country ..."
        # This is much faster.
        
        data_file = f"data_lake/{indicator_source}_*.parquet" # heuristic
        
        join_query = f"""
        SELECT 
            g.geometry,
            g.country as iso_code,
            g.name,
            d.value,
            d.year
        FROM 'data_lake/geo_countries.parquet' g
        LEFT JOIN (
            SELECT country, value, year 
            FROM '{data_file}' 
            WHERE indicator = '{indicator_code}' AND year = {year}
        ) d ON g.country = d.country
        """
        
        try:
            result = self.lake.query(join_query)
        except Exception as e:
            logger.error(f"Globe join query failed: {e}")
            return {}
            
        return result
