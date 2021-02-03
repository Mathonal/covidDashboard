from app import app
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

from utils import Header,LabeledSelect
from utils import (
    get_affecteddeaths_carddata,
    graphcountryperf,
    getIncPerMillion,
    comparativeIncidenceFigure
    )
from modeling import col_map,country_map,continent_map

# get relative data folder
import pathlib
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("../workdata").resolve()



def appcontent(app):
    # default loading
    wdf,clist = getIncPerMillion(list(country_map.keys()),'date')

    # ================== CARD LAYOUT =========================

    # Card components on all data available (world)
    worldcards = get_affecteddeaths_carddata(
        list(country_map.keys()))

    # ================== PERF LAYOUT =========================

    Worldperfo = graphcountryperf(list(country_map.keys()))

    # ================== TOP incidence LAYOUT =========================
    # Get list countries with of top incidence
    # last date value
    lastvaldf = wdf.iloc[[-1]].T
    # sort values 
    lastvaldf.sort_values(lastvaldf.columns[0],inplace=True,ascending=False)
    # get first names
    top10list = list(lastvaldf.index[0:10])

    # 5 - draw graphe
    toptentitle="Graphe des plus fortes incidences actuelles (par million de personnes)"
    toptengraph = dcc.Graph(figure=comparativeIncidenceFigure(wdf,top10list,toptentitle))

    # ================== LAYOUT=========================
    groupDist = ['Continent','World']#,'Country']

    cards = [
        dbc.Card(id='globalaffected_card'),
        dbc.Card(id='globalmortality_card'),
        #dbc.Card(id='mortality_card2')
        ] 

    # LAYOUT STACKING
    #app.layout = dbc.Container(
    page_layout = html.Div(dbc.Container(
        [
            Header(app),
            html.Hr(), # Separation line
            html.H4("Monde"),
            dbc.Row([dbc.Col(card) for card in worldcards]), # 1 row with Xcard in column
            html.Br(),
            dbc.Row(dbc.Col(dbc.Card([Worldperfo,
                html.P("Note d'interprétation : les pays à droite du graphique sont \
                    les plus touchés par l'épidémie ; les pays en dessous de la courbe ont \
                    une meilleure gestion de leur crise par leur sytème de santé (mortalité \
                    des infectés moins élevée) OU ALORS ont un comptage incomplet"),
                ]))),
            html.Br(),
            dbc.Row(dbc.Col(dbc.Card([toptengraph,
                html.P("Note d'interprétation : Ces pays sont ceux présentant les plus importantes \"vagues\" épidémique \
                    en cours comparativement à leur population"),
                ]))),
            html.Hr(), # Separation line
        ],
        fluid=False,
    ))
    return page_layout