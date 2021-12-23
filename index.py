import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import os

from app import app
from pages import (
    app_countrydetails,
    app_groupview,
    app_overview,
)

# load .env in local, get from env in cloud
from dotenv import load_dotenv
load_dotenv()

from api_pipeline.api_utils import globaldataupdate

import logging
logging.basicConfig(level=logging.DEBUG,
 format=' %(threadName)s -- %(levelname)s -- %(message)s')
# %(processName)s %(asctime)s

logging.debug('Start of program')
# Pre-Update Data at launch (thread)
# verify data for country list before lauching or restarting app 
# (after sleep on keroku)

# ENVIRONMENT CHECK
herokuflag = os.getenv('ISHEROKU', 'dontexist') 
# normally give 'True', or 'dontexist' if not found
logging.debug('Heroku EnvVariable value: {}'.format(herokuflag))

# not authorizing heroku update, to long on display. only refresh data on local for now
# see if better results once on SQL base.
if herokuflag != 'True' : globaldataupdate()
else : logging.debug('No data update on heroku for display availability')

# =========================================
# Describe the GENERIC layout/ UI of the app
app.layout = html.Div(
    [dcc.Location(id="url", refresh=False), html.Div(id="page-content")]
)

# Update page from url
@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def display_page(pathname):
    if pathname == "/details-per-country":
        return app_countrydetails.appcontent(app) 
    elif pathname == "/overview" or pathname == "/": 
        return app_overview.appcontent(app)
    elif pathname == "/groupview" : 
        return app_groupview.appcontent(app)
    else : return 'ERROR 404'

# =========================================
if __name__ == "__main__":
    #app.run_server(debug=True, host='0.0.0.0',)
    app.run_server(host='0.0.0.0',debug=True)
    # reloader option prevent flask to intialize twice in debugg mode use_reloader=False,
    # option debug or use reloader can't seem to to any differences ...