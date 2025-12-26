"""
Plot Service for WorldInsights.

This service aggregates data from multiple API clients (World Bank, WHO, FAO, 
Open-Meteo, NASA) and provides unified interfaces for plotting and visualization.

Following Clean Architecture:
- Service layer - contains business logic
- No framework dependencies
- Delegates to infrastructure layer (API clients)
"""
from typing import Dict, List, Optional, Tuple, Any
from functools import lru_cache
import pandas as pd
import numpy as np
from app.core.logging import get_logger
from app.infrastructure.api_clients.worldbank import WorldBankClient
from app.infrastructure.api_clients.who import WHOClient
from app.infrastructure.api_clients.fao import FAOClient
from app.infrastructure.api_clients.openmeteo import OpenMeteoClient
from app.infrastructure.api_clients.nasa import NASAClient


logger = get_logger(__name__)


class PlotService:
    """
    Service for aggregating and transforming data for plotting.
    
    Features:
    - Aggregates indicators and countries from all data sources
    - Fetches data from multiple sources simultaneously
    - Transforms data for different chart types
    - Calculates correlations between indicators
    - Implements caching for performance
    
    Example usage:
        >>> service = PlotService()
        >>> indicators, error = service.get_available_indicators()
        >>> data, error = service.fetch_plot_data(['NY.GDP.MKTP.CD'], ['USA'], 2015, 2020)
    """
    
    def __init__(self):
        """Initialize PlotService with all API clients."""
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
        
        logger.info("PlotService initialized with all API clients")
    
    @lru_cache(maxsize=1)
    def get_available_indicators(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Aggregate indicators from all data sources.
        
        Returns:
            Tuple of (indicators_list, error_message)
            Each indicator dict contains:
                - code: str
                - name: str
                - description: str
                - source: str (worldbank, who, fao, openmeteo, nasa)
        """
        logger.info("Fetching available indicators from all sources")
        all_indicators = []
        errors = []
        
        # Fetch from World Bank
        try:
            wb_indicators, error = self.worldbank.get_indicators(per_page=100)
            if error:
                errors.append(f"World Bank: {error}")
                logger.warning(f"Failed to fetch World Bank indicators: {error}")
            elif wb_indicators:
                for ind in wb_indicators:
                    ind['source'] = 'worldbank'
                all_indicators.extend(wb_indicators)
                logger.info(f"Fetched {len(wb_indicators)} indicators from World Bank")
        except Exception as e:
            errors.append(f"World Bank: {str(e)}")
            logger.error(f"Exception fetching World Bank indicators: {str(e)}")
        
        # Fetch from WHO
        try:
            who_indicators, error = self.who.get_indicators(limit=100)
            if error:
                errors.append(f"WHO: {error}")
                logger.warning(f"Failed to fetch WHO indicators: {error}")
            elif who_indicators:
                for ind in who_indicators:
                    ind['source'] = 'who'
                all_indicators.extend(who_indicators)
                logger.info(f"Fetched {len(who_indicators)} indicators from WHO")
        except Exception as e:
            errors.append(f"WHO: {str(e)}")
            logger.error(f"Exception fetching WHO indicators: {str(e)}")
        
        # Fetch from FAO
        try:
            fao_indicators, error = self.fao.get_indicators()
            if error:
                errors.append(f"FAO: {error}")
                logger.warning(f"Failed to fetch FAO indicators: {error}")
            elif fao_indicators:
                for ind in fao_indicators:
                    ind['source'] = 'fao'
                all_indicators.extend(fao_indicators)
                logger.info(f"Fetched {len(fao_indicators)} indicators from FAO")
        except Exception as e:
            errors.append(f"FAO: {str(e)}")
            logger.error(f"Exception fetching FAO indicators: {str(e)}")
        
        # Fetch from Open-Meteo
        try:
            meteo_indicators, error = self.openmeteo.get_indicators()
            if error:
                errors.append(f"Open-Meteo: {error}")
                logger.warning(f"Failed to fetch Open-Meteo indicators: {error}")
            elif meteo_indicators:
                for ind in meteo_indicators:
                    ind['source'] = 'openmeteo'
                all_indicators.extend(meteo_indicators)
                logger.info(f"Fetched {len(meteo_indicators)} indicators from Open-Meteo")
        except Exception as e:
            errors.append(f"Open-Meteo: {str(e)}")
            logger.error(f"Exception fetching Open-Meteo indicators: {str(e)}")
        
        # Fetch from NASA
        try:
            nasa_indicators, error = self.nasa.get_indicators()
            if error:
                errors.append(f"NASA: {error}")
                logger.warning(f"Failed to fetch NASA indicators: {error}")
            elif nasa_indicators:
                for ind in nasa_indicators:
                    ind['source'] = 'nasa'
                all_indicators.extend(nasa_indicators)
                logger.info(f"Fetched {len(nasa_indicators)} indicators from NASA")
        except Exception as e:
            errors.append(f"NASA: {str(e)}")
            logger.error(f"Exception fetching NASA indicators: {str(e)}")
        
        if not all_indicators and errors:
            error_msg = "; ".join(errors)
            logger.error(f"Failed to fetch indicators from all sources: {error_msg}")
            return None, error_msg
        
        logger.info(f"Successfully aggregated {len(all_indicators)} indicators from {len(self.clients)} sources")
        return all_indicators, None
    
    @lru_cache(maxsize=1)
    def get_available_countries(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Aggregate countries from all data sources.
        
        Returns:
            Tuple of (countries_list, error_message)
            Each country dict contains:
                - code: str (ISO 3166-1 alpha-3)
                - name: str
                - source: str
        """
        logger.info("Fetching available countries from all sources")
        all_countries = []
        country_codes_seen = set()
        errors = []
        
        # Fetch from World Bank (most comprehensive)
        try:
            wb_countries, error = self.worldbank.get_countries()
            if error:
                errors.append(f"World Bank: {error}")
                logger.warning(f"Failed to fetch World Bank countries: {error}")
            elif wb_countries:
                for country in wb_countries:
                    code = country.get('code', '')
                    if code and code not in country_codes_seen:
                        country['source'] = 'worldbank'
                        all_countries.append(country)
                        country_codes_seen.add(code)
                logger.info(f"Fetched {len(wb_countries)} countries from World Bank")
        except Exception as e:
            errors.append(f"World Bank: {str(e)}")
            logger.error(f"Exception fetching World Bank countries: {str(e)}")
        
        # Fetch from WHO
        try:
            who_countries, error = self.who.get_countries()
            if error:
                errors.append(f"WHO: {error}")
                logger.warning(f"Failed to fetch WHO countries: {error}")
            elif who_countries:
                for country in who_countries:
                    code = country.get('code', '')
                    if code and code not in country_codes_seen:
                        country['source'] = 'who'
                        all_countries.append(country)
                        country_codes_seen.add(code)
                logger.info(f"Added {len([c for c in who_countries if c.get('code') not in country_codes_seen])} new countries from WHO")
        except Exception as e:
            errors.append(f"WHO: {str(e)}")
            logger.error(f"Exception fetching WHO countries: {str(e)}")
        
        # Fetch from FAO
        try:
            fao_countries, error = self.fao.get_countries()
            if error:
                errors.append(f"FAO: {error}")
                logger.warning(f"Failed to fetch FAO countries: {error}")
            elif fao_countries:
                for country in fao_countries:
                    code = country.get('code', '')
                    if code and code not in country_codes_seen:
                        country['source'] = 'fao'
                        all_countries.append(country)
                        country_codes_seen.add(code)
                logger.info(f"Added {len([c for c in fao_countries if c.get('code') not in country_codes_seen])} new countries from FAO")
        except Exception as e:
            errors.append(f"FAO: {str(e)}")
            logger.error(f"Exception fetching FAO countries: {str(e)}")
        
        if not all_countries and errors:
            error_msg = "; ".join(errors)
            logger.error(f"Failed to fetch countries from all sources: {error_msg}")
            return None, error_msg
        
        # Sort by name
        all_countries.sort(key=lambda x: x.get('name', ''))
        
        logger.info(f"Successfully aggregated {len(all_countries)} unique countries")
        return all_countries, None
    
    def fetch_plot_data(
        self,
        indicators: List[str],
        countries: List[str],
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch data for plotting from appropriate data sources.
        
        Args:
            indicators: List of indicator codes (e.g., ['NY.GDP.MKTP.CD', 'SP.POP.TOTL'])
            countries: List of country codes (e.g., ['USA', 'GBR'])
            start_year: Optional start year
            end_year: Optional end year
            
        Returns:
            Tuple of (data_list, error_message)
            Each data dict contains:
                - country: str
                - year: int
                - indicator: str
                - value: float
                - source: str
        """
        if not indicators:
            return None, "At least one indicator is required"
        
        if not countries:
            return None, "At least one country is required"
        
        logger.info(f"Fetching plot data for {len(indicators)} indicators, {len(countries)} countries")
        
        all_data = []
        errors = []
        
        # Determine which source each indicator belongs to
        indicator_sources = self._map_indicators_to_sources(indicators)
        
        for indicator in indicators:
            source = indicator_sources.get(indicator, 'worldbank')  # Default to World Bank
            client = self.clients.get(source)
            
            if not client:
                logger.warning(f"No client found for source: {source}")
                continue
            
            for country in countries:
                try:
                    data, error = client.get_data(
                        country_code=country,
                        indicator_code=indicator,
                        start_year=start_year,
                        end_year=end_year
                    )
                    
                    if error:
                        errors.append(f"{source}/{indicator}/{country}: {error}")
                        logger.warning(f"Failed to fetch data: {error}")
                    elif data:
                        all_data.extend(data)
                        logger.debug(f"Fetched {len(data)} data points for {country}/{indicator}")
                    
                except Exception as e:
                    errors.append(f"{source}/{indicator}/{country}: {str(e)}")
                    logger.error(f"Exception fetching data: {str(e)}")
        
        if not all_data and errors:
            error_msg = "; ".join(errors[:5])  # Limit error messages
            logger.error(f"Failed to fetch any data: {error_msg}")
            return None, error_msg
        
        logger.info(f"Successfully fetched {len(all_data)} data points")
        return all_data, None
    
    def _map_indicators_to_sources(self, indicators: List[str]) -> Dict[str, str]:
        """
        Map indicator codes to their data sources.
        
        Args:
            indicators: List of indicator codes
            
        Returns:
            Dict mapping indicator code to source name
        """
        mapping = {}
        
        for indicator in indicators:
            # Simple heuristic based on indicator code patterns
            if indicator.startswith('WHOSIS_') or indicator.startswith('MDG_'):
                mapping[indicator] = 'who'
            elif indicator.startswith('QC') or indicator.startswith('RL') or indicator.startswith('FS'):
                mapping[indicator] = 'fao'
            elif 'temperature' in indicator.lower() or 'precipitation' in indicator.lower():
                mapping[indicator] = 'openmeteo'
            elif 'solar' in indicator.lower() or 'radiation' in indicator.lower():
                mapping[indicator] = 'nasa'
            else:
                # Default to World Bank (most comprehensive)
                mapping[indicator] = 'worldbank'
        
        return mapping
    
    def transform_for_chart_type(
        self,
        data: List[Dict],
        chart_type: str
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Transform data into format suitable for specific chart type.
        
        Args:
            data: List of data records from fetch_plot_data
            chart_type: One of 'line', 'bar', 'scatter', 'choropleth'
            
        Returns:
            Tuple of (transformed_data, error_message)
            Format depends on chart_type:
            - line: {indicator: {country: {year: value}}}
            - bar: {country: {indicator: value}}
            - scatter: {country: {indicator1: value, indicator2: value}}
            - choropleth: {country: value}
        """
        if not data:
            return None, "No data to transform"
        
        valid_chart_types = ['line', 'bar', 'scatter', 'choropleth']
        if chart_type not in valid_chart_types:
            return None, f"Invalid chart type. Must be one of: {', '.join(valid_chart_types)}"
        
        logger.info(f"Transforming {len(data)} records for {chart_type} chart")
        
        try:
            if chart_type == 'line':
                return self._transform_for_line_chart(data), None
            elif chart_type == 'bar':
                return self._transform_for_bar_chart(data), None
            elif chart_type == 'scatter':
                return self._transform_for_scatter_chart(data), None
            elif chart_type == 'choropleth':
                return self._transform_for_choropleth(data), None
        except Exception as e:
            logger.error(f"Error transforming data for {chart_type}: {str(e)}")
            return None, f"Failed to transform data: {str(e)}"
    
    def _transform_for_line_chart(self, data: List[Dict]) -> Dict:
        """Transform data for time-series line chart."""
        result = {}
        
        for record in data:
            indicator = record.get('indicator', '')
            country = record.get('country', '')
            year = record.get('year', 0)
            value = record.get('value')
            
            if indicator not in result:
                result[indicator] = {}
            if country not in result[indicator]:
                result[indicator][country] = {}
            
            result[indicator][country][year] = value
        
        return result
    
    def _transform_for_bar_chart(self, data: List[Dict]) -> Dict:
        """Transform data for bar chart (latest year for each country)."""
        result = {}
        
        # Group by country and indicator, take latest year
        for record in data:
            country = record.get('country', '')
            indicator = record.get('indicator', '')
            year = record.get('year', 0)
            value = record.get('value')
            
            if country not in result:
                result[country] = {}
            
            if indicator not in result[country]:
                result[country][indicator] = {'year': year, 'value': value}
            elif year > result[country][indicator]['year']:
                result[country][indicator] = {'year': year, 'value': value}
        
        return result
    
    def _transform_for_scatter_chart(self, data: List[Dict]) -> Dict:
        """Transform data for scatter plot (requires 2 indicators)."""
        # Group by country, need values for both indicators
        df = pd.DataFrame(data)
        
        if df.empty:
            return {}
        
        # Get unique indicators
        indicators = df['indicator'].unique()
        
        if len(indicators) < 2:
            logger.warning("Scatter plot requires at least 2 indicators")
            return {}
        
        # Take first 2 indicators
        ind1, ind2 = indicators[0], indicators[1]
        
        # Pivot to get country x indicator matrix
        result = {}
        
        for country in df['country'].unique():
            country_data = df[df['country'] == country]
            
            # Get latest value for each indicator
            ind1_data = country_data[country_data['indicator'] == ind1].sort_values('year', ascending=False)
            ind2_data = country_data[country_data['indicator'] == ind2].sort_values('year', ascending=False)
            
            if not ind1_data.empty and not ind2_data.empty:
                result[country] = {
                    ind1: ind1_data.iloc[0]['value'],
                    ind2: ind2_data.iloc[0]['value']
                }
        
        return result
    
    def _transform_for_choropleth(self, data: List[Dict]) -> Dict:
        """Transform data for choropleth map (single indicator, latest year)."""
        result = {}
        
        # Take latest year for each country
        for record in data:
            country = record.get('country', '')
            year = record.get('year', 0)
            value = record.get('value')
            
            if country not in result:
                result[country] = {'year': year, 'value': value}
            elif year > result[country]['year']:
                result[country] = {'year': year, 'value': value}
        
        return result
    
    def calculate_correlations(
        self,
        data: List[Dict]
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Calculate correlations between indicators.
        
        Args:
            data: List of data records
            
        Returns:
            Tuple of (correlation_matrix, error_message)
            correlation_matrix is dict: {indicator1: {indicator2: correlation_value}}
        """
        if not data:
            return None, "No data provided for correlation"
        
        logger.info(f"Calculating correlations for {len(data)} records")
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Pivot to wide format: rows=country-year, columns=indicators
            pivot = df.pivot_table(
                index=['country', 'year'],
                columns='indicator',
                values='value',
                aggfunc='first'
            )
            
            # Calculate correlation matrix
            corr_matrix = pivot.corr()
            
            # Convert to nested dict
            result = {}
            for ind1 in corr_matrix.index:
                result[ind1] = {}
                for ind2 in corr_matrix.columns:
                    corr_value = corr_matrix.loc[ind1, ind2]
                    # Convert numpy types to Python types
                    if pd.notna(corr_value):
                        result[ind1][ind2] = float(corr_value)
                    else:
                        result[ind1][ind2] = None
            
            logger.info(f"Calculated correlations for {len(result)} indicators")
            return result, None
            
        except Exception as e:
            logger.error(f"Error calculating correlations: {str(e)}")
            return None, f"Failed to calculate correlations: {str(e)}"
