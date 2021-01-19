import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app import app
from pages import (
    app_page1,
    app_page2,
)

from utils import globaldataupdate

# Pre-Update Data at launch (thread)
globaldataupdate()

# =========================================
# Describe the GENERIC layout/ UI of the app
app.layout = html.Div(
    [dcc.Location(id="url", refresh=False), html.Div(id="page-content")]
)

# Update page from url
@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def display_page(pathname):
    if pathname == "/generic-per-country":
        return app_page2.appcontent(app) 
    elif pathname == "/overview" or pathname == "/": 
        return app_page1.appcontent(app)
    else : return '404'

# =========================================
if __name__ == "__main__":
    app.run_server(debug=True,host='0.0.0.0')