"""
Tests for PlotService.

Following TDD - these tests define expected behavior.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.plot_service import PlotService


class TestPlotService:
    """Test suite for PlotService."""
    
    @patch('app.services.plot_service.WorldBankClient')
    @patch('app.services.plot_service.WHOClient')
    @patch('app.services.plot_service.FAOClient')
    @patch('app.services.plot_service.OpenMeteoClient')
    @patch('app.services.plot_service.NASAClient')
    def test_initialization(self, mock_nasa, mock_meteo, mock_fao, mock_who, mock_wb):
        """Test PlotService initializes with all API clients."""
        service = PlotService()
        
        assert service.worldbank is not None
        assert service.who is not None
        assert service.fao is not None
        assert service.openmeteo is not None
        assert service.nasa is not None
        assert len(service.clients) == 5
    
    @patch('app.services.plot_service.WorldBankClient')
    @patch('app.services.plot_service.WHOClient')
    @patch('app.services.plot_service.FAOClient')
    @patch('app.services.plot_service.OpenMeteoClient')
    @patch('app.services.plot_service.NASAClient')
    def test_get_available_indicators_success(self, mock_nasa, mock_meteo, mock_fao, mock_who, mock_wb):
        """Test aggregating indicators from all sources."""
        # Mock World Bank indicators
        mock_wb_instance = mock_wb.return_value
        mock_wb_instance.get_indicators.return_value = (
            [
                {'code': 'NY.GDP.MKTP.CD', 'name': 'GDP', 'description': 'GDP in current US$'},
                {'code': 'SP.POP.TOTL', 'name': 'Population', 'description': 'Total population'}
            ],
            None
        )
        
        # Mock WHO indicators
        mock_who_instance = mock_who.return_value
        mock_who_instance.get_indicators.return_value = (
            [{'code': 'WHOSIS_000001', 'name': 'Life Expectancy', 'description': 'Life expectancy at birth'}],
            None
        )
        
        # Mock FAO indicators
        mock_fao_instance = mock_fao.return_value
        mock_fao_instance.get_indicators.return_value = (
            [{'code': 'QCL_1', 'name': 'Wheat Production', 'description': 'Wheat production'}],
            None
        )
        
        # Mock Open-Meteo indicators
        mock_meteo_instance = mock_meteo.return_value
        mock_meteo_instance.get_indicators.return_value = (
            [{'code': 'temperature_2m_mean', 'name': 'Mean Temperature', 'unit': '°C'}],
            None
        )
        
        # Mock NASA indicators
        mock_nasa_instance = mock_nasa.return_value
        mock_nasa_instance.get_indicators.return_value = (
            [{'code': 'T2M', 'name': 'Temperature at 2m', 'description': 'Temperature'}],
            None
        )
        
        service = PlotService()
        indicators, error = service.get_available_indicators()
        
        assert error is None
        assert len(indicators) == 6
        # Check that sources are tagged
        assert any(ind['source'] == 'worldbank' for ind in indicators)
        assert any(ind['source'] == 'who' for ind in indicators)
        assert any(ind['source'] == 'fao' for ind in indicators)
        assert any(ind['source'] == 'openmeteo' for ind in indicators)
        assert any(ind['source'] == 'nasa' for ind in indicators)
    
    @patch('app.services.plot_service.WorldBankClient')
    @patch('app.services.plot_service.WHOClient')
    @patch('app.services.plot_service.FAOClient')
    @patch('app.services.plot_service.OpenMeteoClient')
    @patch('app.services.plot_service.NASAClient')
    def test_get_available_indicators_partial_failure(self, mock_nasa, mock_meteo, mock_fao, mock_who, mock_wb):
        """Test that partial failures still return available indicators."""
        # World Bank succeeds
        mock_wb_instance = mock_wb.return_value
        mock_wb_instance.get_indicators.return_value = (
            [{'code': 'NY.GDP.MKTP.CD', 'name': 'GDP', 'description': 'GDP'}],
            None
        )
        
        # WHO fails
        mock_who_instance = mock_who.return_value
        mock_who_instance.get_indicators.return_value = (None, "API error")
        
        # Others return empty
        mock_fao_instance = mock_fao.return_value
        mock_fao_instance.get_indicators.return_value = ([], None)
        
        mock_meteo_instance = mock_meteo.return_value
        mock_meteo_instance.get_indicators.return_value = ([], None)
        
        mock_nasa_instance = mock_nasa.return_value
        mock_nasa_instance.get_indicators.return_value = ([], None)
        
        service = PlotService()
        indicators, error = service.get_available_indicators()
        
        # Should still return World Bank indicators
        assert error is None
        assert len(indicators) == 1
        assert indicators[0]['code'] == 'NY.GDP.MKTP.CD'
    
    @patch('app.services.plot_service.WorldBankClient')
    @patch('app.services.plot_service.WHOClient')
    @patch('app.services.plot_service.FAOClient')
    @patch('app.services.plot_service.OpenMeteoClient')
    @patch('app.services.plot_service.NASAClient')
    def test_get_available_countries_success(self, mock_nasa, mock_meteo, mock_fao, mock_who, mock_wb):
        """Test aggregating countries from all sources."""
        # Mock World Bank countries
        mock_wb_instance = mock_wb.return_value
        mock_wb_instance.get_countries.return_value = (
            [
                {'code': 'USA', 'name': 'United States'},
                {'code': 'GBR', 'name': 'United Kingdom'}
            ],
            None
        )
        
        # Mock WHO countries (with one duplicate)
        mock_who_instance = mock_who.return_value
        mock_who_instance.get_countries.return_value = (
            [
                {'code': 'USA', 'name': 'United States'},
                {'code': 'DEU', 'name': 'Germany'}
            ],
            None
        )
        
        # Mock FAO countries
        mock_fao_instance = mock_fao.return_value
        mock_fao_instance.get_countries.return_value = (
            [{'code': 'FRA', 'name': 'France'}],
            None
        )
        
        service = PlotService()
        countries, error = service.get_available_countries()
        
        assert error is None
        # Should deduplicate USA
        assert len(countries) == 4
        country_codes = [c['code'] for c in countries]
        assert 'USA' in country_codes
        assert 'GBR' in country_codes
        assert 'DEU' in country_codes
        assert 'FRA' in country_codes
    
    @patch('app.services.plot_service.WorldBankClient')
    @patch('app.services.plot_service.WHOClient')
    @patch('app.services.plot_service.FAOClient')
    @patch('app.services.plot_service.OpenMeteoClient')
    @patch('app.services.plot_service.NASAClient')
    def test_fetch_plot_data_success(self, mock_nasa, mock_meteo, mock_fao, mock_who, mock_wb):
        """Test fetching plot data from appropriate sources."""
        mock_wb_instance = mock_wb.return_value
        mock_wb_instance.get_data.return_value = (
            [
                {'country': 'USA', 'year': 2020, 'indicator': 'NY.GDP.MKTP.CD', 'value': 21000000000000, 'source': 'World Bank'},
                {'country': 'USA', 'year': 2019, 'indicator': 'NY.GDP.MKTP.CD', 'value': 21400000000000, 'source': 'World Bank'}
            ],
            None
        )
        
        service = PlotService()
        data, error = service.fetch_plot_data(
            indicators=['NY.GDP.MKTP.CD'],
            countries=['USA'],
            start_year=2019,
            end_year=2020
        )
        
        assert error is None
        assert len(data) == 2
        assert data[0]['country'] == 'USA'
        assert data[0]['indicator'] == 'NY.GDP.MKTP.CD'
    
    @patch('app.services.plot_service.WorldBankClient')
    @patch('app.services.plot_service.WHOClient')
    @patch('app.services.plot_service.FAOClient')
    @patch('app.services.plot_service.OpenMeteoClient')
    @patch('app.services.plot_service.NASAClient')
    def test_fetch_plot_data_multiple_indicators_countries(self, mock_nasa, mock_meteo, mock_fao, mock_who, mock_wb):
        """Test fetching data for multiple indicators and countries."""
        mock_wb_instance = mock_wb.return_value
        
        def mock_get_data(country_code, indicator_code, start_year=None, end_year=None):
            return (
                [{'country': country_code, 'year': 2020, 'indicator': indicator_code, 'value': 100, 'source': 'World Bank'}],
                None
            )
        
        mock_wb_instance.get_data.side_effect = mock_get_data
        
        service = PlotService()
        data, error = service.fetch_plot_data(
            indicators=['NY.GDP.MKTP.CD', 'SP.POP.TOTL'],
            countries=['USA', 'GBR'],
            start_year=2020,
            end_year=2020
        )
        
        assert error is None
        # Should have 2 indicators × 2 countries = 4 data points
        assert len(data) == 4
    
    @patch('app.services.plot_service.WorldBankClient')
    @patch('app.services.plot_service.WHOClient')
    @patch('app.services.plot_service.FAOClient')
    @patch('app.services.plot_service.OpenMeteoClient')
    @patch('app.services.plot_service.NASAClient')
    def test_fetch_plot_data_validation(self, mock_nasa, mock_meteo, mock_fao, mock_who, mock_wb):
        """Test input validation for fetch_plot_data."""
        service = PlotService()
        
        # No indicators
        data, error = service.fetch_plot_data(indicators=[], countries=['USA'])
        assert error is not None
        assert "indicator" in error.lower()
        
        # No countries
        data, error = service.fetch_plot_data(indicators=['NY.GDP.MKTP.CD'], countries=[])
        assert error is not None
        assert "country" in error.lower()
    
    @patch('app.services.plot_service.WorldBankClient')
    @patch('app.services.plot_service.WHOClient')
    @patch('app.services.plot_service.FAOClient')
    @patch('app.services.plot_service.OpenMeteoClient')
    @patch('app.services.plot_service.NASAClient')
    def test_transform_for_line_chart(self, mock_nasa, mock_meteo, mock_fao, mock_who, mock_wb):
        """Test data transformation for line chart."""
        service = PlotService()
        
        data = [
            {'country': 'USA', 'year': 2019, 'indicator': 'NY.GDP.MKTP.CD', 'value': 21400000000000},
            {'country': 'USA', 'year': 2020, 'indicator': 'NY.GDP.MKTP.CD', 'value': 21000000000000},
            {'country': 'GBR', 'year': 2019, 'indicator': 'NY.GDP.MKTP.CD', 'value': 2800000000000},
            {'country': 'GBR', 'year': 2020, 'indicator': 'NY.GDP.MKTP.CD', 'value': 2700000000000},
        ]
        
        transformed, error = service.transform_for_chart_type(data, 'line')
        
        assert error is None
        assert 'NY.GDP.MKTP.CD' in transformed
        assert 'USA' in transformed['NY.GDP.MKTP.CD']
        assert 'GBR' in transformed['NY.GDP.MKTP.CD']
        assert transformed['NY.GDP.MKTP.CD']['USA'][2019] == 21400000000000
        assert transformed['NY.GDP.MKTP.CD']['USA'][2020] == 21000000000000
    
    @patch('app.services.plot_service.WorldBankClient')
    @patch('app.services.plot_service.WHOClient')
    @patch('app.services.plot_service.FAOClient')
    @patch('app.services.plot_service.OpenMeteoClient')
    @patch('app.services.plot_service.NASAClient')
    def test_transform_for_bar_chart(self, mock_nasa, mock_meteo, mock_fao, mock_who, mock_wb):
        """Test data transformation for bar chart (takes latest year)."""
        service = PlotService()
        
        data = [
            {'country': 'USA', 'year': 2019, 'indicator': 'NY.GDP.MKTP.CD', 'value': 21400000000000},
            {'country': 'USA', 'year': 2020, 'indicator': 'NY.GDP.MKTP.CD', 'value': 21000000000000},
            {'country': 'GBR', 'year': 2020, 'indicator': 'NY.GDP.MKTP.CD', 'value': 2700000000000},
        ]
        
        transformed, error = service.transform_for_chart_type(data, 'bar')
        
        assert error is None
        assert 'USA' in transformed
        assert 'GBR' in transformed
        # Should take latest year (2020) for USA
        assert transformed['USA']['NY.GDP.MKTP.CD']['value'] == 21000000000000
        assert transformed['USA']['NY.GDP.MKTP.CD']['year'] == 2020
    
    @patch('app.services.plot_service.WorldBankClient')
    @patch('app.services.plot_service.WHOClient')
    @patch('app.services.plot_service.FAOClient')
    @patch('app.services.plot_service.OpenMeteoClient')
    @patch('app.services.plot_service.NASAClient')
    def test_transform_for_scatter_chart(self, mock_nasa, mock_meteo, mock_fao, mock_who, mock_wb):
        """Test data transformation for scatter plot."""
        service = PlotService()
        
        data = [
            {'country': 'USA', 'year': 2020, 'indicator': 'NY.GDP.MKTP.CD', 'value': 21000000000000},
            {'country': 'USA', 'year': 2020, 'indicator': 'SP.POP.TOTL', 'value': 331000000},
            {'country': 'GBR', 'year': 2020, 'indicator': 'NY.GDP.MKTP.CD', 'value': 2700000000000},
            {'country': 'GBR', 'year': 2020, 'indicator': 'SP.POP.TOTL', 'value': 67000000},
        ]
        
        transformed, error = service.transform_for_chart_type(data, 'scatter')
        
        assert error is None
        assert 'USA' in transformed
        assert 'GBR' in transformed
        # Should have both indicators for each country
        assert 'NY.GDP.MKTP.CD' in transformed['USA']
        assert 'SP.POP.TOTL' in transformed['USA']
    
    @patch('app.services.plot_service.WorldBankClient')
    @patch('app.services.plot_service.WHOClient')
    @patch('app.services.plot_service.FAOClient')
    @patch('app.services.plot_service.OpenMeteoClient')
    @patch('app.services.plot_service.NASAClient')
    def test_transform_for_choropleth(self, mock_nasa, mock_meteo, mock_fao, mock_who, mock_wb):
        """Test data transformation for choropleth map."""
        service = PlotService()
        
        data = [
            {'country': 'USA', 'year': 2019, 'indicator': 'NY.GDP.MKTP.CD', 'value': 21400000000000},
            {'country': 'USA', 'year': 2020, 'indicator': 'NY.GDP.MKTP.CD', 'value': 21000000000000},
            {'country': 'GBR', 'year': 2020, 'indicator': 'NY.GDP.MKTP.CD', 'value': 2700000000000},
        ]
        
        transformed, error = service.transform_for_chart_type(data, 'choropleth')
        
        assert error is None
        assert 'USA' in transformed
        assert 'GBR' in transformed
        # Should take latest year for each country
        assert transformed['USA']['value'] == 21000000000000
        assert transformed['USA']['year'] == 2020
    
    @patch('app.services.plot_service.WorldBankClient')
    @patch('app.services.plot_service.WHOClient')
    @patch('app.services.plot_service.FAOClient')
    @patch('app.services.plot_service.OpenMeteoClient')
    @patch('app.services.plot_service.NASAClient')
    def test_transform_invalid_chart_type(self, mock_nasa, mock_meteo, mock_fao, mock_who, mock_wb):
        """Test error handling for invalid chart type."""
        service = PlotService()
        
        data = [{'country': 'USA', 'year': 2020, 'indicator': 'NY.GDP.MKTP.CD', 'value': 100}]
        
        transformed, error = service.transform_for_chart_type(data, 'invalid_type')
        
        assert transformed is None
        assert error is not None
        assert "invalid" in error.lower()
    
    @patch('app.services.plot_service.WorldBankClient')
    @patch('app.services.plot_service.WHOClient')
    @patch('app.services.plot_service.FAOClient')
    @patch('app.services.plot_service.OpenMeteoClient')
    @patch('app.services.plot_service.NASAClient')
    def test_calculate_correlations(self, mock_nasa, mock_meteo, mock_fao, mock_who, mock_wb):
        """Test correlation calculation between indicators."""
        service = PlotService()
        
        # Create data with perfect positive correlation
        data = [
            {'country': 'USA', 'year': 2018, 'indicator': 'IND1', 'value': 10},
            {'country': 'USA', 'year': 2018, 'indicator': 'IND2', 'value': 20},
            {'country': 'USA', 'year': 2019, 'indicator': 'IND1', 'value': 20},
            {'country': 'USA', 'year': 2019, 'indicator': 'IND2', 'value': 40},
            {'country': 'USA', 'year': 2020, 'indicator': 'IND1', 'value': 30},
            {'country': 'USA', 'year': 2020, 'indicator': 'IND2', 'value': 60},
        ]
        
        correlations, error = service.calculate_correlations(data)
        
        assert error is None
        assert 'IND1' in correlations
        assert 'IND2' in correlations
        # Perfect positive correlation
        assert correlations['IND1']['IND2'] == pytest.approx(1.0, abs=0.01)
        assert correlations['IND2']['IND1'] == pytest.approx(1.0, abs=0.01)
        # Self-correlation should be 1
        assert correlations['IND1']['IND1'] == pytest.approx(1.0, abs=0.01)
    
    @patch('app.services.plot_service.WorldBankClient')
    @patch('app.services.plot_service.WHOClient')
    @patch('app.services.plot_service.FAOClient')
    @patch('app.services.plot_service.OpenMeteoClient')
    @patch('app.services.plot_service.NASAClient')
    def test_indicator_source_mapping(self, mock_nasa, mock_meteo, mock_fao, mock_who, mock_wb):
        """Test that indicators are correctly mapped to their sources."""
        service = PlotService()
        
        # Test WHO indicator
        mapping = service._map_indicators_to_sources(['WHOSIS_000001'])
        assert mapping['WHOSIS_000001'] == 'who'
        
        # Test FAO indicator
        mapping = service._map_indicators_to_sources(['QCL_123'])
        assert mapping['QCL_123'] == 'fao'
        
        # Test Open-Meteo indicator
        mapping = service._map_indicators_to_sources(['temperature_2m_mean'])
        assert mapping['temperature_2m_mean'] == 'openmeteo'
        
        # Test NASA indicator
        mapping = service._map_indicators_to_sources(['solar_radiation'])
        assert mapping['solar_radiation'] == 'nasa'
        
        # Test World Bank indicator (default)
        mapping = service._map_indicators_to_sources(['NY.GDP.MKTP.CD'])
        assert mapping['NY.GDP.MKTP.CD'] == 'worldbank'
