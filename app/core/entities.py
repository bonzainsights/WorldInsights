"""
Domain entities for WorldInsights.

This module defines the core data models following Clean Architecture principles.
All entities are framework-agnostic and use Pydantic for validation.

Entities:
- Country: Country/region information
- Indicator: Data indicator/metric definition
- DataPoint: Single data observation
- DataSource: Information about data source
- AvailabilityMatrix: Country-indicator availability cache
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class DataSourceType(str, Enum):
    """Enumeration of supported data source types."""
    WORLD_BANK = "world_bank"
    WHO = "who"
    FAO = "fao"
    NASA = "nasa"
    NOAA = "noaa"
    UN_DATA = "un_data"
    OWID = "owid"
    IMF = "imf"
    UNESCO = "unesco"
    ILO = "ilo"
    ITU = "itu"
    UNWTO = "unwto"
    OPEN_METEO = "open_meteo"


class Country(BaseModel):
    """
    Country/region entity.
    
    Attributes:
        code: ISO 3166-1 alpha-3 country code (e.g., 'USA', 'GBR')
        name: Official country name
        iso2_code: ISO 3166-1 alpha-2 code (e.g., 'US', 'GB')
        iso_numeric: ISO 3166-1 numeric code (e.g., '840', '826')
        capital: Capital city name
        region: Geographic region (e.g., 'North America', 'Europe')
        subregion: Geographic subregion
        income_level: Income classification (e.g., 'High income', 'Low income')
        population: Latest population estimate
        area_km2: Land area in square kilometers
        currency_code: ISO 4217 currency code
        currency_name: Currency name
        languages: List of official languages
        data_sources: List of data sources that have data for this country
    """
    code: str = Field(..., description="ISO 3166-1 alpha-3 country code", min_length=3, max_length=3)
    name: str = Field(..., description="Official country name", min_length=1)
    iso2_code: Optional[str] = Field(None, description="ISO 3166-1 alpha-2 code", min_length=2, max_length=2)
    iso_numeric: Optional[str] = Field(None, description="ISO 3166-1 numeric code")
    capital: Optional[str] = Field(None, description="Capital city")
    region: Optional[str] = Field(None, description="Geographic region")
    subregion: Optional[str] = Field(None, description="Geographic subregion")
    income_level: Optional[str] = Field(None, description="Income classification")
    population: Optional[int] = Field(None, description="Latest population estimate", ge=0)
    area_km2: Optional[float] = Field(None, description="Land area in square kilometers", ge=0)
    currency_code: Optional[str] = Field(None, description="ISO 4217 currency code")
    currency_name: Optional[str] = Field(None, description="Currency name")
    languages: List[str] = Field(default_factory=list, description="Official languages")
    data_sources: List[str] = Field(default_factory=list, description="Available data sources")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "USA",
                "name": "United States",
                "iso2_code": "US",
                "iso_numeric": "840",
                "capital": "Washington, D.C.",
                "region": "North America",
                "subregion": "Northern America",
                "income_level": "High income",
                "population": 331000000,
                "area_km2": 9833517.0,
                "currency_code": "USD",
                "currency_name": "United States Dollar",
                "languages": ["English"],
                "data_sources": ["world_bank", "who", "fao", "nasa"]
            }
        }


class Indicator(BaseModel):
    """
    Data indicator/metric entity.
    
    Attributes:
        code: Unique indicator code (source-specific or normalized)
        name: Human-readable indicator name
        description: Detailed description of what the indicator measures
        source: Data source identifier (e.g., 'world_bank', 'who')
        unit: Unit of measurement (e.g., 'USD', 'people', 'percent')
        category: Indicator category (e.g., 'Economy', 'Health', 'Agriculture')
        subcategory: Indicator subcategory
        frequency: Data frequency (e.g., 'annual', 'quarterly', 'monthly')
        start_year: First year of available data
        end_year: Last year of available data
        countries_count: Number of countries with data for this indicator
        metadata: Additional source-specific metadata
    """
    code: str = Field(..., description="Unique indicator code", min_length=1)
    name: str = Field(..., description="Human-readable indicator name", min_length=1)
    description: Optional[str] = Field(None, description="Detailed description")
    source: str = Field(..., description="Data source identifier")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    category: Optional[str] = Field(None, description="Indicator category")
    subcategory: Optional[str] = Field(None, description="Indicator subcategory")
    frequency: str = Field(default="annual", description="Data frequency")
    start_year: Optional[int] = Field(None, description="First year of available data", ge=1900, le=2100)
    end_year: Optional[int] = Field(None, description="Last year of available data", ge=1900, le=2100)
    countries_count: Optional[int] = Field(None, description="Number of countries with data", ge=0)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "SP.POP.TOTL",
                "name": "Population, total",
                "description": "Total population is the sum of all residents regardless of legal status or citizenship.",
                "source": "world_bank",
                "unit": "people",
                "category": "Demographics",
                "subcategory": "Population",
                "frequency": "annual",
                "start_year": 1960,
                "end_year": 2023,
                "countries_count": 266,
                "metadata": {"world_bank_topic": "Population"}
            }
        }


class DataPoint(BaseModel):
    """
    Single data observation entity.
    
    This is the unified schema that all API responses are normalized to.
    
    Attributes:
        country_code: ISO 3166-1 alpha-3 country code
        country_name: Country name
        indicator_code: Indicator code
        indicator_name: Indicator name
        year: Year of the observation
        value: Numeric value of the observation
        unit: Unit of measurement
        source: Data source identifier
        original_value: Original value from source (before any transformations)
        original_unit: Original unit from source
        quality_flag: Data quality indicator (e.g., 'estimated', 'projected', 'actual')
        last_updated: When this data point was last updated
        metadata: Additional source-specific metadata
    """
    country_code: str = Field(..., description="ISO 3166-1 alpha-3 country code")
    country_name: str = Field(..., description="Country name")
    indicator_code: str = Field(..., description="Indicator code")
    indicator_name: str = Field(..., description="Indicator name")
    year: int = Field(..., description="Year of observation", ge=1900, le=2100)
    value: Optional[float] = Field(None, description="Numeric value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    source: str = Field(..., description="Data source identifier")
    original_value: Optional[Any] = Field(None, description="Original value from source")
    original_unit: Optional[str] = Field(None, description="Original unit from source")
    quality_flag: Optional[str] = Field(None, description="Data quality flag")
    last_updated: Optional[datetime] = Field(None, description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('value')
    def validate_value(cls, v):
        """Validate that value is a valid number or None."""
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        try:
            return float(v)
        except (ValueError, TypeError):
            return None
    
    class Config:
        json_schema_extra = {
            "example": {
                "country_code": "USA",
                "country_name": "United States",
                "indicator_code": "SP.POP.TOTL",
                "indicator_name": "Population, total",
                "year": 2023,
                "value": 331000000.0,
                "unit": "people",
                "source": "world_bank",
                "original_value": 331002651,
                "original_unit": "people",
                "quality_flag": "actual",
                "last_updated": "2024-01-15T00:00:00Z",
                "metadata": {"world_bank_source_id": "2"}
            }
        }


class DataSource(BaseModel):
    """
    Data source configuration and metadata entity.
    
    Attributes:
        id: Unique source identifier (e.g., 'world_bank', 'who')
        name: Human-readable source name
        description: Source description
        base_url: API base URL
        documentation_url: Link to API documentation
        enabled: Whether this source is currently enabled
        requires_auth: Whether authentication is required
        api_key_env_var: Environment variable name for API key (if required)
        rate_limit: Rate limit configuration
        cache_ttl: Default cache TTL in seconds
        status: Current status ('healthy', 'degraded', 'offline')
        last_health_check: Timestamp of last health check
        indicators_count: Number of available indicators
        countries_count: Number of countries covered
        data_range_start: Earliest year of data
        data_range_end: Latest year of data
        categories: List of data categories covered
        update_frequency: How often data is updated
        metadata: Additional source-specific metadata
    """
    id: str = Field(..., description="Unique source identifier")
    name: str = Field(..., description="Human-readable source name")
    description: Optional[str] = Field(None, description="Source description")
    base_url: str = Field(..., description="API base URL")
    documentation_url: Optional[str] = Field(None, description="API documentation URL")
    enabled: bool = Field(default=True, description="Whether source is enabled")
    requires_auth: bool = Field(default=False, description="Whether auth is required")
    api_key_env_var: Optional[str] = Field(None, description="API key env var name")
    rate_limit: Optional[str] = Field(None, description="Rate limit configuration")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    status: str = Field(default="unknown", description="Current status")
    last_health_check: Optional[datetime] = Field(None, description="Last health check")
    indicators_count: Optional[int] = Field(None, description="Number of indicators")
    countries_count: Optional[int] = Field(None, description="Number of countries")
    data_range_start: Optional[int] = Field(None, description="Earliest year")
    data_range_end: Optional[int] = Field(None, description="Latest year")
    categories: List[str] = Field(default_factory=list, description="Data categories")
    update_frequency: Optional[str] = Field(None, description="Update frequency")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "world_bank",
                "name": "World Bank Open Data",
                "description": "Over 16,000 development indicators for 200+ countries",
                "base_url": "https://api.worldbank.org/v2",
                "documentation_url": "https://datahelpdesk.worldbank.org/knowledgebase/api",
                "enabled": True,
                "requires_auth": False,
                "rate_limit": "10 per second",
                "cache_ttl": 86400,
                "status": "healthy",
                "indicators_count": 16000,
                "countries_count": 266,
                "data_range_start": 1960,
                "data_range_end": 2023,
                "categories": ["Economy", "Demographics", "Health", "Education", "Environment"],
                "update_frequency": "daily"
            }
        }


class AvailabilityMatrix(BaseModel):
    """
    Country-indicator availability cache entity.
    
    This matrix enables smart filtering:
    - Given country → return available indicators
    - Given indicator → return available countries
    - Given multiple selections → return intersection
    
    Attributes:
        country_indicators: Map of country_code → set of indicator_codes
        indicator_countries: Map of indicator_code → set of country_codes
        last_updated: When the matrix was last updated
        source: Data source this matrix is for
        version: Matrix version for cache invalidation
    """
    country_indicators: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Map of country_code → list of indicator_codes"
    )
    indicator_countries: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Map of indicator_code → list of country_codes"
    )
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    source: str = Field(..., description="Data source identifier")
    version: int = Field(default=1, description="Matrix version")
    
    def get_indicators_for_country(self, country_code: str) -> List[str]:
        """Get list of available indicators for a country."""
        return self.country_indicators.get(country_code.upper(), [])
    
    def get_countries_for_indicator(self, indicator_code: str) -> List[str]:
        """Get list of available countries for an indicator."""
        return self.indicator_countries.get(indicator_code, [])
    
    def get_available_countries(self, indicator_codes: List[str]) -> List[str]:
        """Get countries that have data for ALL specified indicators (intersection)."""
        if not indicator_codes:
            return list(self.country_indicators.keys())
        
        # Start with countries for first indicator
        result = set(self.indicator_countries.get(indicator_codes[0], []))
        
        # Intersect with countries for remaining indicators
        for code in indicator_codes[1:]:
            result &= set(self.indicator_countries.get(code, []))
        
        return list(result)
    
    def get_available_indicators(self, country_codes: List[str]) -> List[str]:
        """Get indicators that have data for ALL specified countries (intersection)."""
        if not country_codes:
            return list(self.indicator_countries.keys())
        
        # Start with indicators for first country
        result = set(self.country_indicators.get(country_codes[0].upper(), []))
        
        # Intersect with indicators for remaining countries
        for code in country_codes[1:]:
            result &= set(self.country_indicators.get(code.upper(), []))
        
        return list(result)
    
    class Config:
        json_schema_extra = {
            "example": {
                "country_indicators": {
                    "USA": ["SP.POP.TOTL", "NY.GDP.MKTP.CD", "SH.DYN.MORT"],
                    "GBR": ["SP.POP.TOTL", "NY.GDP.MKTP.CD"]
                },
                "indicator_countries": {
                    "SP.POP.TOTL": ["USA", "GBR", "FRA", "DEU"],
                    "NY.GDP.MKTP.CD": ["USA", "GBR", "FRA"]
                },
                "last_updated": "2024-01-15T12:00:00Z",
                "source": "world_bank",
                "version": 1
            }
        }


class QueryRequest(BaseModel):
    """
    Query request entity for complex multi-source queries.
    
    Attributes:
        countries: List of country codes to query
        indicators: List of indicator codes to query
        sources: List of data sources to query (empty = all enabled)
        start_year: Start year for time range
        end_year: End year for time range
        include_metadata: Whether to include metadata in response
        format: Response format ('json', 'csv')
        aggregation: Aggregation function if grouping ('sum', 'avg', 'min', 'max')
        group_by: Field to group results by ('country', 'indicator', 'year', 'source')
    """
    countries: List[str] = Field(default_factory=list, description="Country codes")
    indicators: List[str] = Field(default_factory=list, description="Indicator codes")
    sources: List[str] = Field(default_factory=list, description="Data sources")
    start_year: Optional[int] = Field(None, description="Start year", ge=1900, le=2100)
    end_year: Optional[int] = Field(None, description="End year", ge=1900, le=2100)
    include_metadata: bool = Field(default=True, description="Include metadata")
    format: str = Field(default="json", description="Response format")
    aggregation: Optional[str] = Field(None, description="Aggregation function")
    group_by: Optional[str] = Field(None, description="Group by field")
    
    class Config:
        json_schema_extra = {
            "example": {
                "countries": ["USA", "GBR", "FRA"],
                "indicators": ["SP.POP.TOTL", "NY.GDP.MKTP.CD"],
                "sources": ["world_bank", "who"],
                "start_year": 2018,
                "end_year": 2023,
                "include_metadata": True,
                "format": "json"
            }
        }


class QueryResponse(BaseModel):
    """
    Query response entity.
    
    Attributes:
        data: List of data points
        metadata: Query metadata
        pagination: Pagination information
        performance: Performance metrics
    """
    data: List[DataPoint] = Field(default_factory=list, description="Data points")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Query metadata")
    pagination: Dict[str, Any] = Field(default_factory=dict, description="Pagination info")
    performance: Dict[str, Any] = Field(default_factory=dict, description="Performance metrics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": [
                    {
                        "country_code": "USA",
                        "country_name": "United States",
                        "indicator_code": "SP.POP.TOTL",
                        "indicator_name": "Population, total",
                        "year": 2023,
                        "value": 331000000.0,
                        "unit": "people",
                        "source": "world_bank"
                    }
                ],
                "metadata": {
                    "query_time": "2024-01-15T12:00:00Z",
                    "sources_queried": ["world_bank"],
                    "countries_count": 1,
                    "indicators_count": 1,
                    "data_points_count": 1
                },
                "pagination": {
                    "total": 1,
                    "page": 1,
                    "per_page": 100,
                    "pages": 1
                },
                "performance": {
                    "total_time_ms": 150.5,
                    "cache_hits": 1,
                    "api_calls": 0
                }
            }
        }


class HealthStatus(BaseModel):
    """
    Health check status entity.
    
    Attributes:
        status: Overall status ('healthy', 'degraded', 'unhealthy')
        timestamp: Check timestamp
        version: Application version
        sources: Status of each data source
        cache: Cache status
        database: Database status
    """
    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    version: str = Field(default="2.0.0", description="Application version")
    sources: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Source statuses")
    cache: Dict[str, Any] = Field(default_factory=dict, description="Cache status")
    database: Dict[str, Any] = Field(default_factory=dict, description="Database status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-15T12:00:00Z",
                "version": "2.0.0",
                "sources": {
                    "world_bank": {"status": "healthy", "latency_ms": 120},
                    "who": {"status": "healthy", "latency_ms": 85}
                },
                "cache": {"status": "connected", "hit_rate": 0.85},
                "database": {"status": "connected", "size_mb": 150}
            }
        }
