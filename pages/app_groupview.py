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
    comparativeIncidenceFigure,
    )
from modeling import col_map,country_map,continent_map

# get relative data folder
import pathlib
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("../workdata").resolve()



def appcontent(app):
    wdf,clist = getIncPerMillion(list(country_map.keys()),'date')
    # ================== LAYOUT=========================
    groupDist = ['Continent','World']#,'Country']

    labelselectors = [
            LabeledSelect(
                id="select-grouptype",
                options=[{"label": k, "value": k} for k in groupDist],
                value=groupDist[0],
                label="Filter by groups",
            ),
            dcc.Checklist(
            id='check-grouplist',
            # options=[
            # {'label': 'brut incidence   ', 'value': 'brut'},
            # {'label': 'moving average (7days)   ', 'value': 'MA'},
            # {'label': 'exponential moving average', 'value': 'EMA'}
            # ],
            # value=['MA', 'EMA'],
            labelStyle={'display': 'inline-block'}
            ) 
        ]

    absrangeselector = dcc.RangeSlider(
        id='abs-slider',
        # label="Filter time range",
        # marks={i: '{}'.format(df['Date'][i]) for i in range(0,df.shape[0]-1,(df.shape[0]-1)//5)},
        min=0,
        max=wdf.shape[0]-1,
        value=[0, wdf.shape[0]-1]
        )

    # Card components
    cards = [
        dbc.Card(id='groupaffected_card'),
        dbc.Card(id='groupmortality_card'),
        #dbc.Card(id='mortality_card2')
        ] 

    # Graph components
    graphs = [
        [
            dcc.Graph(id="graph-groupcomparativeInc"),
        ],
    ]

    # LAYOUT STACKING
    #app.layout = dbc.Container(
    page1_layout = html.Div(dbc.Container(
        [
            Header(app),
            html.Hr(), # Separation line
            html.H4("Selection"),
            #GLOBAL SELECTORS : 1 row with x label selectors, 1 row with date
            dbc.Row(dbc.Col(labelselectors[0])),
            dbc.Row(dbc.Col(labelselectors[1])),
            html.Br(),
            dbc.Row([dbc.Col(card) for card in cards]), # 1 row with Xcard in column
            html.Br(),
            dbc.Col(dbc.Col(absrangeselector)),
            #dbc.Row([dbc.Col(graph) for graph in graphs]),
            dbc.Row(dbc.Col(dbc.Card(graphs[0]))),
            html.Br(),
            html.P(id='placeholder')
        ],
        fluid=False,
    ))
    return page1_layout

# SELECTORS
@app.callback(
    [
    Output("check-grouplist", "options"),Output("check-grouplist", "value")
    ],
    Input("select-grouptype", "value")
)
def update_groupselect(grouptype):
    print(grouptype)
    if grouptype == "Continent":
        checkoptions=[
        {"label": 'Europe', "value": 'Europe'},
        {"label": 'Amerique', "value": 'America'},
        {"label": 'Asie', "value": 'Asia'},
        {"label": 'Afrique', "value": 'Africa'},
        ]
        checkvalue = ['Europe']

    elif grouptype == "World": 
        checkoptions=[{"label": v, "value": k} for k,v in country_map.items()]
        checkvalue = [k for k in country_map.keys()]

    else : 
        checkoptions =[{"label": 'meuh', "value": 1}]
        checkvalue = []

    return checkoptions,checkvalue


# GRAPHES 
@app.callback(
    Output("graph-groupcomparativeInc", "figure"),
    [
    Input("abs-slider", "value"),
    Input("check-grouplist", "value"),
    ]
)
def update_comparative_incidence_figures(abscisserange,countrylist):
    # Loading default Dataframe and compute data
    figlist = getFinalCountryList(countrylist)
    #wdf,figlist = getIncPerMillion(list(country_map.keys()),'date')
    wdf,figlist = getIncPerMillion(figlist,'date')

    # 4 - Filter dosplay based on chosen values
    # DATE RANGE
    wdf_filt = wdf.iloc[abscisserange[0]:abscisserange[1]]
    # 5 - draw graphe
    title="Graphe d'incidence comparative des cas confirmés par million de personnes"
    return comparativeIncidenceFigure(wdf_filt,figlist,title)

# CARDS
def getFinalCountryList(inputlist):
    finallist = []
    for elem in continent_map.keys():
        if elem in inputlist :
            for x in list(continent_map[elem].keys()):
                finallist.append(x)

    if finallist == [] : finallist = inputlist
    return finallist

@app.callback(
    [Output("groupaffected_card", "children"),
    Output("groupmortality_card", "children")],
    Input("check-grouplist", "value"),
    )
def computeCardsComponents(group_val):
    print('updating group cards')
    figlist = getFinalCountryList(group_val)
    cardlist = get_affecteddeaths_carddata(figlist)

    return cardlist[0],cardlist[1]