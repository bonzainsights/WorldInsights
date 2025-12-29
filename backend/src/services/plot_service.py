
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
from src.infrastructure.api_clients.worldbank import WorldBankClient
from src.infrastructure.api_clients.who import WHOClient
from src.infrastructure.api_clients.fao import FAOClient
from src.infrastructure.api_clients.openmeteo import OpenMeteoClient
from src.infrastructure.api_clients.nasa import NASAClient
import logging

logger = logging.getLogger(__name__)

class PlotService:
    def __init__(self):
        self.worldbank = WorldBankClient()
        self.who = WHOClient()
        self.fao = FAOClient()
        self.openmeteo = OpenMeteoClient()
        self.nasa = NASAClient()
        
        self.clients = {
            'worldbank': self.worldbank,
            'who': self.who,
            'fao': self.fao,
            'openmeteo': self.openmeteo,
            'nasa': self.nasa
        }
    
    def get_available_indicators(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        # For MVP backend, let's fetch WorldBank only for speed, or cached
        # Adding support for all:
        all_indicators = []
        errors = []
        
        try:
            wb_indicators, error = self.worldbank.get_indicators(per_page=100)
            if wb_indicators: all_indicators.extend([dict(i, source='worldbank') for i in wb_indicators])
        except Exception as e: errors.append(str(e))
            
        # ... logic for others similarly ...
        
        return all_indicators, ";".join(errors) if errors else None
    
    def get_available_countries(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        try:
            wb_countries, error = self.worldbank.get_countries()
            if wb_countries:
                return wb_countries, None
        except Exception as e:
            return None, str(e)
        return [], "No countries found"

    def fetch_plot_data(self, indicators: List[str], countries: List[str], start_year: Optional[int]=None, end_year: Optional[int]=None):
        # Simplification of original Logic
        all_data = []
        failed = []
        
        for indicator in indicators:
            source = 'worldbank' # Default
            # Simple heuristic
            if indicator.startswith('WHO'): source = 'who'
            elif 'temp' in indicator: source = 'openmeteo'
            
            client = self.clients.get(source)
            if not client: continue
            
            for country in countries:
                try:
                    data, err = client.get_data(country, indicator, start_year=start_year, end_year=end_year)
                    if data: all_data.extend(data)
                except:
                    failed.append(f"{country}:{indicator}")
                    
        return all_data, f"Failed: {failed}" if failed else None

    # Note: Correlations and Transformations can be calculated on Frontend for SPA, 
    # but Backend can provide if needed.
    # Omitting heavy logic for brevity in this initial port, can add if requested.
