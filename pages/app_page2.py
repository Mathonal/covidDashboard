import datetime
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

#from sklearn.metrics import accuracy_score
pd.options.mode.chained_assignment = None

from api_pipeline.api_utils import updateIncidenceTable
from utils import Header,LabeledSelect
from utils import update_alldata,verify_priordata,globaldataupdate
from modeling import col_map,country_map

#from app import app
#default loading country (first in list)
DEFAULTCOUNTRY = list(country_map.keys())[0]
# verify data for country list before lauching or restarting app 
# (after sleep on keroku)
# globaldataupdate()

def appcontent(app):
    # Loading default Dataframe and compute data
    df = verify_priordata(DEFAULTCOUNTRY)
   
    # ================== LAYOUT=========================

    # LAYOUT STACKING
    #app.layout = dbc.Container(
    page_layout = dbc.Container(
        [
            Header("Dash Covid Visualization", app),
            html.Hr(), # Separation line
            Header("Dash Covid Visualization", app),
            html.Hr(), # Separation line
        ],
        fluid=False,
    )



    return page_layout
# =========================================
# # STARTING THE APP
# app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
# server = app.server
# appcontent(app)

# if __name__ == "__main__":
#     app.run_server(debug=True,host='0.0.0.0')