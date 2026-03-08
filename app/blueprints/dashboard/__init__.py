"""
Dashboard Blueprint for WorldInsights.

This blueprint provides the dashboard builder functionality, allowing users to:
- Select data sources and indicators
- Choose countries and year ranges
- Select chart types
- Render interactive Plotly charts
- Save and load custom dashboards

Following Clean Architecture:
- This is the delivery layer (Flask-specific)
- Delegates to services for business logic
- Returns JSON for HTMX consumption
"""
from flask import Blueprint, render_template, request, jsonify, session
from typing import Dict, Any, Optional

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

from . import routes
