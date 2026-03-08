"""
Visualization Service for WorldInsights.

This service generates Plotly chart configurations for various chart types,
including 2D charts (line, bar, scatter) and 3D visualizations (scatter3d,
surface, globe).

Following Clean Architecture:
- Service layer - contains business logic
- No framework dependencies
- Returns Plotly configuration dictionaries
- Type hints and docstrings throughout
"""
from typing import Dict, List, Any, Optional
from collections import defaultdict
import pandas as pd
import numpy as np

from app.core.logging import get_logger


logger = get_logger(__name__)


class VisualizationService:
    """
    Service for generating Plotly chart configurations.
    
    Features:
    - 2D charts: line, bar, scatter
    - 3D charts: scatter3d, surface
    - Globe visualization
    - Consistent styling across chart types
    - Responsive layouts
    
    Example usage:
        >>> service = VisualizationService()
        >>> config = service.create_2d_chart(data, 'line', 'NY.GDP.MKTP.CD', ['USA', 'GBR'])
        >>> config = service.create_globe_chart(data, 'SP.POP.TOTL')
    """
    
    # Color palette for multiple countries/series
    COLORS = [
        '#3B82F6',  # Blue
        '#EF4444',  # Red
        '#10B981',  # Green
        '#F59E0B',  # Amber
        '#8B5CF6',  # Violet
        '#EC4899',  # Pink
        '#06B6D4',  # Cyan
        '#F97316',  # Orange
        '#84CC16',  # Lime
        '#14B8A6',  # Teal
    ]
    
    # Country name cache (in production, fetch from service)
    COUNTRY_NAMES = {
        'USA': 'United States',
        'GBR': 'United Kingdom',
        'CHN': 'China',
        'JPN': 'Japan',
        'DEU': 'Germany',
        'FRA': 'France',
        'IND': 'India',
        'BRA': 'Brazil',
        'CAN': 'Canada',
        'AUS': 'Australia',
        'ITA': 'Italy',
        'ESP': 'Spain',
        'MEX': 'Mexico',
        'KOR': 'South Korea',
        'RUS': 'Russia',
        'ZAF': 'South Africa',
        'NGA': 'Nigeria',
        'EGY': 'Egypt',
        'ARG': 'Argentina',
        'SAU': 'Saudi Arabia',
    }
    
    def __init__(self):
        """Initialize VisualizationService."""
        logger.info("VisualizationService initialized")
    
    def create_2d_chart(
        self,
        data: List[Dict],
        chart_type: str,
        indicator: str,
        countries: List[str],
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a 2D chart configuration (line, bar, or scatter).
        
        Args:
            data: List of data records with keys: country, year, indicator, value
            chart_type: One of 'line', 'bar', 'scatter'
            indicator: Indicator code
            countries: List of country codes
            title: Optional chart title
        
        Returns:
            Plotly chart configuration dictionary
        """
        if not data:
            return self._create_empty_chart_config("No data available")
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(data)
        
        if df.empty:
            return self._create_empty_chart_config("No data available")
        
        # Get indicator name (use code if name not available)
        indicator_name = indicator
        
        # Build title
        if not title:
            title = f"{indicator_name} by Country"
        
        # Group data by country
        traces = []
        
        for i, country in enumerate(countries):
            country_data = df[df['country'] == country].sort_values('year')
            
            if country_data.empty:
                continue
            
            country_name = self.COUNTRY_NAMES.get(country, country)
            color = self.COLORS[i % len(self.COLORS)]
            
            if chart_type == 'line':
                trace = {
                    'type': 'scatter',
                    'mode': 'lines+markers',
                    'x': country_data['year'].tolist(),
                    'y': country_data['value'].tolist(),
                    'name': country_name,
                    'line': {'color': color, 'width': 2},
                    'marker': {'size': 6},
                    'hovertemplate': f'<b>{country_name}</b><br>Year: %{{x}}<br>Value: %{{y:,.2f}}<extra></extra>'
                }
            elif chart_type == 'bar':
                # For bar charts, use latest year
                latest = country_data.iloc[-1] if not country_data.empty else None
                if latest is not None:
                    trace = {
                        'type': 'bar',
                        'x': [country_name],
                        'y': [latest['value']],
                        'name': country_name,
                        'marker': {'color': color},
                        'hovertemplate': f'<b>{country_name}</b><br>Value: %{{y:,.2f}}<extra></extra>'
                    }
            elif chart_type == 'scatter':
                # Scatter needs 2 indicators - use first two years as x/y
                if len(country_data) >= 2:
                    x_data = country_data.iloc[:-1]['value'].tolist()
                    y_data = country_data.iloc[1:]['value'].tolist()
                    trace = {
                        'type': 'scatter',
                        'mode': 'markers',
                        'x': x_data,
                        'y': y_data,
                        'name': country_name,
                        'marker': {'color': color, 'size': 10},
                        'hovertemplate': f'<b>{country_name}</b><br>X: %{{x:,.2f}}<br>Y: %{{y:,.2f}}<extra></extra>'
                    }
            
            if trace:
                traces.append(trace)
        
        if not traces:
            return self._create_empty_chart_config("No data available for selected countries")
        
        # Build layout
        layout = self._create_layout(
            title=title,
            xaxis_title='Year' if chart_type == 'line' else 'Country',
            yaxis_title='Value',
            show_legend=len(traces) > 1
        )
        
        # Configure for chart type
        if chart_type == 'bar':
            layout['barmode'] = 'group'
            layout['xaxis']['type'] = 'category'
        elif chart_type == 'scatter':
            layout['xaxis']['title'] = f'{indicator_name} (t-1)'
            layout['yaxis']['title'] = f'{indicator_name} (t)'
        
        return {
            'data': traces,
            'layout': layout,
            'config': {
                'responsive': True,
                'displayModeBar': True,
                'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
                'displaylogo': False
            }
        }
    
    def create_3d_chart(
        self,
        data: List[Dict],
        chart_type: str,
        indicator: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a 3D chart configuration (scatter3d or surface).
        
        Args:
            data: List of data records
            chart_type: One of '3d_scatter', '3d_surface'
            indicator: Indicator code
            title: Optional chart title
        
        Returns:
            Plotly 3D chart configuration dictionary
        """
        if not data:
            return self._create_empty_chart_config("No data available")
        
        df = pd.DataFrame(data)
        
        if df.empty:
            return self._create_empty_chart_config("No data available")
        
        if chart_type == '3d_scatter':
            return self._create_3d_scatter(df, indicator, title)
        elif chart_type == '3d_surface':
            return self._create_3d_surface(df, indicator, title)
        else:
            return self._create_empty_chart_config(f"Unknown 3D chart type: {chart_type}")
    
    def _create_3d_scatter(
        self,
        df: pd.DataFrame,
        indicator: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create 3D scatter plot."""
        # Use year as X, value as Y, and country index as Z
        unique_countries = df['country'].unique()
        
        traces = []
        for i, country in enumerate(unique_countries):
            country_data = df[df['country'] == country].sort_values('year')
            
            if len(country_data) < 2:
                continue
            
            country_name = self.COUNTRY_NAMES.get(country, country)
            color = self.COLORS[i % len(self.COLORS)]
            
            trace = {
                'type': 'scatter3d',
                'mode': 'lines+markers',
                'x': country_data['year'].tolist(),
                'y': country_data['value'].fillna(0).tolist(),
                'z': [i] * len(country_data),
                'name': country_name,
                'line': {'width': 4, 'color': color},
                'marker': {'size': 4, 'color': color},
                'hovertemplate': f'<b>{country_name}</b><br>Year: %{{x}}<br>Value: %{{y:,.2f}}<extra></extra>'
            }
            traces.append(trace)
        
        if not traces:
            return self._create_empty_chart_config("No data available for 3D visualization")
        
        title = title or f"3D Visualization: {indicator}"
        
        layout = {
            'title': {
                'text': title,
                'font': {'size': 18, 'family': 'Inter, sans-serif'}
            },
            'scene': {
                'xaxis': {'title': 'Year'},
                'yaxis': {'title': 'Value'},
                'zaxis': {'title': 'Country', 'tickvals': list(range(len(unique_countries))), 'ticktext': [self.COUNTRY_NAMES.get(c, c) for c in unique_countries]},
                'camera': {
                    'eye': {'x': 1.5, 'y': 1.5, 'z': 1.2}
                },
                'bgcolor': 'rgba(249, 250, 251, 0.5)'
            },
            'margin': {'l': 0, 'r': 0, 't': 60, 'b': 0},
            'paper_bgcolor': 'rgba(0,0,0,0)',
            'plot_bgcolor': 'rgba(0,0,0,0)',
            'showlegend': True,
            'legend': {'x': 0, 'y': 1}
        }
        
        return {
            'data': traces,
            'layout': layout,
            'config': {
                'responsive': True,
                'displayModeBar': True,
                'displaylogo': False
            }
        }
    
    def _create_3d_surface(
        self,
        df: pd.DataFrame,
        indicator: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create 3D surface plot."""
        # Pivot data to create a surface: countries x years = values
        pivot = df.pivot_table(index='country', columns='year', values='value', aggfunc='first')
        
        if pivot.empty or pivot.shape[0] < 2 or pivot.shape[1] < 2:
            return self._create_empty_chart_config("Insufficient data for surface plot")
        
        # Fill NaN values
        pivot = pivot.fillna(method='ffill', axis=1).fillna(method='bfill', axis=1).fillna(0)
        
        # Create coordinate arrays
        countries = pivot.index.tolist()
        years = pivot.columns.tolist()
        values = pivot.values
        
        # Create country indices for Z-axis
        z_values = np.array([list(range(len(countries)))] * len(years)).T
        
        trace = {
            'type': 'surface',
            'x': years,
            'y': list(range(len(countries))),
            'z': values,
            'colorscale': 'Viridis',
            'hovertemplate': 'Year: %{x}<br>Country: %{y}<br>Value: %{z:.2f}<extra></extra>',
            'colorbar': {'title': 'Value', 'titleside': 'right'}
        }
        
        title = title or f"3D Surface: {indicator}"
        
        layout = {
            'title': {
                'text': title,
                'font': {'size': 18, 'family': 'Inter, sans-serif'}
            },
            'scene': {
                'xaxis': {'title': 'Year'},
                'yaxis': {'title': 'Country', 'tickvals': list(range(len(countries))), 'ticktext': [self.COUNTRY_NAMES.get(c, c) for c in countries]},
                'zaxis': {'title': 'Value'},
                'camera': {
                    'eye': {'x': 1.8, 'y': 1.8, 'z': 1.5}
                },
                'bgcolor': 'rgba(249, 250, 251, 0.5)'
            },
            'margin': {'l': 0, 'r': 0, 't': 60, 'b': 0},
            'paper_bgcolor': 'rgba(0,0,0,0)',
            'plot_bgcolor': 'rgba(0,0,0,0)'
        }
        
        return {
            'data': [trace],
            'layout': layout,
            'config': {
                'responsive': True,
                'displayModeBar': True,
                'displaylogo': False
            }
        }
    
    def create_globe_chart(
        self,
        data: List[Dict],
        indicator: str,
        year: Optional[int] = None,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a 3D globe visualization.
        
        Args:
            data: List of data records with country, year, value
            indicator: Indicator code
            year: Optional year to display (uses latest if not specified)
            title: Optional chart title
        
        Returns:
            Plotly globe chart configuration dictionary
        """
        if not data:
            return self._create_empty_chart_config("No data available for globe")
        
        df = pd.DataFrame(data)
        
        # Filter to latest year if not specified
        if year is None:
            year = df['year'].max()
        
        df_year = df[df['year'] == year]
        
        if df_year.empty:
            return self._create_empty_chart_config(f"No data available for year {year}")
        
        # Country coordinates (lat/lon) - simplified for major countries
        # In production, fetch from a geocoding service or database
        country_coords = {
            'USA': {'lat': 37.0902, 'lon': -95.7129},
            'GBR': {'lat': 55.3781, 'lon': -3.4360},
            'CHN': {'lat': 35.8617, 'lon': 104.1954},
            'JPN': {'lat': 36.2048, 'lon': 138.2529},
            'DEU': {'lat': 51.1657, 'lon': 10.4515},
            'FRA': {'lat': 46.2276, 'lon': 2.2137},
            'IND': {'lat': 20.5937, 'lon': 78.9629},
            'BRA': {'lat': -14.2350, 'lon': -51.9253},
            'CAN': {'lat': 56.1304, 'lon': -106.3468},
            'AUS': {'lat': -25.2744, 'lon': 133.7751},
            'ITA': {'lat': 41.8719, 'lon': 12.5674},
            'ESP': {'lat': 40.4637, 'lon': -3.7492},
            'MEX': {'lat': 23.6345, 'lon': -102.5528},
            'KOR': {'lat': 35.9078, 'lon': 127.7669},
            'RUS': {'lat': 61.5240, 'lon': 105.3188},
            'ZAF': {'lat': -30.5595, 'lon': 22.9375},
            'NGA': {'lat': 9.0820, 'lon': 8.6753},
            'EGY': {'lat': 26.8206, 'lon': 30.8025},
            'ARG': {'lat': -38.4161, 'lon': -63.6167},
            'SAU': {'lat': 23.8859, 'lon': 45.0792},
        }
        
        # Prepare data for scattergeo
        lats = []
        lons = []
        values = []
        countries = []
        hover_texts = []
        
        for _, row in df_year.iterrows():
            country = row['country']
            coords = country_coords.get(country)
            
            if coords:
                lats.append(coords['lat'])
                lons.append(coords['lon'])
                values.append(row['value'])
                country_name = self.COUNTRY_NAMES.get(country, country)
                countries.append(country_name)
                hover_texts.append(f"<b>{country_name}</b><br>Value: {row['value']:,.2f}")
        
        if not lats:
            return self._create_empty_chart_config("No geographic data available")
        
        # Normalize values for marker size
        values_array = np.array(values)
        min_val, max_val = np.nanmin(values_array), np.nanmax(values_array)
        if max_val > min_val:
            normalized = (values_array - min_val) / (max_val - min_val)
            sizes = 10 + normalized * 40  # Size range: 10-50
        else:
            sizes = [25] * len(values)
        
        trace = {
            'type': 'scattergeo',
            'mode': 'markers',
            'lat': lats,
            'lon': lons,
            'marker': {
                'size': sizes.tolist(),
                'color': values,
                'colorscale': 'Viridis',
                'colorbar': {'title': 'Value', 'thickness': 20},
                'line': {'color': 'white', 'width': 1},
                'opacity': 0.8
            },
            'text': hover_texts,
            'hoverinfo': 'text',
            'name': indicator
        }
        
        title = title or f"Global Distribution: {indicator} ({year})"
        
        layout = {
            'title': {
                'text': title,
                'font': {'size': 18, 'family': 'Inter, sans-serif'}
            },
            'geo': {
                'projection': {'type': 'orthographic'},  # 3D globe effect
                'showocean': True,
                'oceancolor': 'rgba(200, 230, 255, 0.5)',
                'showland': True,
                'landcolor': 'rgba(220, 235, 220, 0.5)',
                'showlakes': True,
                'lakecolor': 'rgba(200, 230, 255, 0.5)',
                'showcountries': True,
                'countrycolor': 'rgba(150, 150, 150, 0.3)',
                'showcoastlines': True,
                'coastlinecolor': 'rgba(100, 100, 100, 0.3)',
                'bgcolor': 'rgba(240, 248, 255, 0.8)',
                'resolution': 50,
                'lonaxis': {'showgrid': False},
                'lataxis': {'showgrid': False}
            },
            'margin': {'l': 0, 'r': 0, 't': 60, 'b': 0},
            'paper_bgcolor': 'rgba(0,0,0,0)',
            'plot_bgcolor': 'rgba(0,0,0,0)',
            'height': 600
        }
        
        return {
            'data': [trace],
            'layout': layout,
            'config': {
                'responsive': True,
                'displayModeBar': True,
                'displaylogo': False,
                'scrollZoom': True  # Enable zoom on scroll
            }
        }
    
    def _create_layout(
        self,
        title: str,
        xaxis_title: str = '',
        yaxis_title: str = '',
        show_legend: bool = True
    ) -> Dict[str, Any]:
        """
        Create a consistent layout configuration.
        
        Args:
            title: Chart title
            xaxis_title: X-axis title
            yaxis_title: Y-axis title
            show_legend: Whether to show legend
        
        Returns:
            Plotly layout dictionary
        """
        return {
            'title': {
                'text': title,
                'font': {'size': 16, 'family': 'Inter, sans-serif'}
            },
            'xaxis': {
                'title': xaxis_title,
                'gridcolor': 'rgba(200, 200, 200, 0.2)',
                'linecolor': 'rgba(200, 200, 200, 0.5)',
                'tickfont': {'size': 11}
            },
            'yaxis': {
                'title': yaxis_title,
                'gridcolor': 'rgba(200, 200, 200, 0.2)',
                'linecolor': 'rgba(200, 200, 200, 0.5)',
                'tickfont': {'size': 11}
            },
            'showlegend': show_legend,
            'legend': {
                'orientation': 'h',
                'y': -0.2,
                'x': 0,
                'font': {'size': 11}
            },
            'margin': {'l': 60, 'r': 20, 't': 60, 'b': 60},
            'paper_bgcolor': 'rgba(0,0,0,0)',
            'plot_bgcolor': 'rgba(0,0,0,0)',
            'hovermode': 'closest',
            'font': {'family': 'Inter, sans-serif', 'size': 12}
        }
    
    def _create_empty_chart_config(self, message: str) -> Dict[str, Any]:
        """
        Create an empty chart configuration with a message.
        
        Args:
            message: Message to display
        
        Returns:
            Plotly configuration with annotation
        """
        return {
            'data': [],
            'layout': {
                'title': {'text': 'No Data Available'},
                'annotations': [{
                    'text': message,
                    'xref': 'paper',
                    'yref': 'paper',
                    'showarrow': False,
                    'font': {'size': 14, 'color': '#6B7280'}
                }],
                'xaxis': {'visible': False},
                'yaxis': {'visible': False},
                'height': 400
            },
            'config': {
                'responsive': True,
                'displayModeBar': False
            }
        }
