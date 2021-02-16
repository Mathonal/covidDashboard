from app import app
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import numpy as np
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
    
    # ================== LAYOUT=========================
    toptentypelist = ['date',10,100,500,1000]#,'Country']

    labelselectors = [
            LabeledSelect(
                id="select-toptentype",
                options=[{"label": k, "value": k} for k in toptentypelist],
                value=toptentypelist[0],
                label="Filtre temporalité : date ou seuil d'incidence / million",
            ), 
        ]

    # ================== CARD LAYOUT =========================

    # Card components on all data available (world)
    worldcards = get_affecteddeaths_carddata(
        list(country_map.keys()))

    # ================== PERF LAYOUT =========================
    Worldperfo = graphcountryperf(list(country_map.keys()))

    # ================== TOP incidence LAYOUT =================
    toptengraph = dcc.Graph(id="graph-topten")

    # ================== LAYOUT=========================
    groupDist = ['Continent','World']#,'Country']

    cards = [
        dbc.Card(id='globalaffected_card'),
        dbc.Card(id='globalmortality_card'),
        #dbc.Card(id='mortality_card2')
        ] 

    # ================== LAYOUT STACKING =========================
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
            dbc.Row(dbc.Col(dbc.Card([dbc.Row(dbc.Col(labelselectors[0])),
                toptengraph,
                html.P("Note d'interprétation : Ces pays sont ceux présentant les plus importantes \"vagues\" épidémique \
                    en cours comparativement à leur population"),
                html.P("Avec une selection \"seuil d'incidence\", le graphe ne compare plus les pays aux mêmes dates;\
                il présente l'évolution de l'incidence à partir du dépassement de la valeur seuil.\
                Ainsi, la date la plus recente est le dernier point de chaque courbe"),
                ]))),
            html.Hr(), # Separation line
        ],
        fluid=False,
    ))
    return page_layout

 # GRAPHES

@app.callback(
    Output("graph-topten", "figure"),
    Input("select-toptentype", "value"),
)
def update_topten_figure(selectedvalue):
    # selected value is passed as string even if it is a number
    try :
        selectedvalue = int(selectedvalue)
    except : pass

    # loading data depending on abscisse type ['string' or 'Int'] 
    curwdf,clist = getIncPerMillion(list(country_map.keys()),selectedvalue)
    
    # Get list countries with of top incidence
    # getting last available value for each country
    # accounting for the fact that this value does not have the same
    # coordinate for all country (due to non updated or treshold selection)
    lastvallist = []
    # LOOP getting the last number of column 
    # (if empty cell, values are NaN)
    for i,elem in enumerate(curwdf.columns):
        inc = 1
        # parses lasts values until find number or arrive at the end of columns
        while np.isnan(curwdf.iloc[-inc,i]) and inc<curwdf.shape[0]:
            inc +=1
        lastvallist.append(curwdf.iloc[-inc,i])

    #lastvaldf = curwdf.iloc[[-1]].T # this works only if all countries are up to date
    lastvaldf = pd.DataFrame(lastvallist,index=curwdf.columns)
    # sort values to get highest
    lastvaldf.sort_values(lastvaldf.columns[0],inplace=True,ascending=False)
    # get first names
    top10list = list(lastvaldf.index[0:10])
    # filter df and only keep topten country
    # before update figure to be sure that X is dimmensionned correctly
    curwdf = curwdf.loc[:,top10list].dropna(how='all')
    # draw graph
    toptentitle="Graphe des plus fortes incidences actuelles (par million de personnes)"
    #toptengraph = dcc.Graph(figure=comparativeIncidenceFigure(curwdf,top10list,toptentitle))

    return comparativeIncidenceFigure(curwdf,top10list,toptentitle)