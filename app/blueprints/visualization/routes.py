from flask import render_template
from . import visualization_bp

@visualization_bp.route('/globe')
def globe():
    """
    Render 3D Globe Visualization page.
    The actual data fetching happens via client-side JS calls to /api/v1/data/globe.
    """
    return render_template('visualization/globe.html')
