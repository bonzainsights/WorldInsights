
import logging
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.services.data_lake_service import DataLakeService
from src.infrastructure.api_clients.worldbank import WorldBankClient
from src.infrastructure.api_clients.who import WHOClient
from src.infrastructure.api_clients.openmeteo import OpenMeteoClient
from src.infrastructure.api_clients.nasa import NASAClient

logger = logging.getLogger(__name__)

class DataRetrievalService:
    def __init__(self):
        self.lake = DataLakeService()
        self._clients = {
            'worldbank': WorldBankClient(),
            'who': WHOClient(),
            'weather': OpenMeteoClient(),
            'nasa': NASAClient()
        }

    def get_data(self, source: str, indicator: str, country: str = None, year: int = None) -> List[Dict]:
        source = source.lower()
        try:
            data = self._query_lake(source, indicator, country, year)
            if data and len(data) > 0:
                logger.info(f"Hit Data Lake for {source}:{indicator}")
                return data
        except Exception as e:
            logger.warning(f"Data Lake query failed: {e}")

        logger.info(f"Miss Data Lake for {source}:{indicator}. Falling back to API.")
        return self._fetch_from_api(source, indicator, country, year)

    def _query_lake(self, source: str, indicator: str, country: str = None, year: int = None) -> List[Dict]:
        # Note: DataLakeService.query now handles the path expansion if we use 'data_lake/' prefix
        file_pattern = f"data_lake/{source}_*.parquet"
        
        query = f"SELECT * FROM '{file_pattern}' WHERE 1=1"
        
        if indicator:
            query += f" AND indicator = '{indicator}'"
        if country:
            query += f" AND country = '{country}'"
        if year:
            query += f" AND year = {year}"
            
        logger.debug(f"Lake Query: {query}")
        result = self.lake.query(query)
        return result

    def _fetch_from_api(self, source: str, indicator: str, country: str = None, year: int = None) -> List[Dict]:
        client = self._clients.get(source)
        if not client:
            return []
            
        try:
            if source == 'weather':
                data, err = client.get_data(country, indicator, start_year=year, end_year=year)
            elif source in ['worldbank', 'nasa']:
                data, err = client.get_data(country, indicator, start_year=year, end_year=year)
            elif source == 'who':
                data, err = client.get_data(country, indicator)
                if year and data:
                    data = [d for d in data if d.get('year') == year]
            else:
                 return []

            if err:
                logger.warning(f"API Error: {err}")
                return []
            if data:
                return data
        except Exception as e:
            logger.error(f"API Fetch failed: {source} {e}")
            return []
        return []

    def get_globe_data(self, indicator_source: str, indicator_code: str, year: int) -> List[Dict]:
        # 1. Get Shapes
        shapes_query = "SELECT country as iso_code, name, geometry FROM 'data_lake/geo_countries.parquet'"
        
        # 2. Join
        data_file = f"data_lake/{indicator_source}_*.parquet"
        
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
            # DataLakeService query handles path expansion
            result = self.lake.query(join_query)
        except Exception as e:
            logger.error(f"Globe join query failed: {e}")
            return []
            
        return result
