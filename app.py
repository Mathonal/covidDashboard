import dash
import dash_bootstrap_components as dbc
# =========================================
# defining the app component for pages import as common reference
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[{"name": "viewport", "content": "width=device-width"}],
    suppress_callback_exceptions=True)
server = app.server