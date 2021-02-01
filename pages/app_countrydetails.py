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

from app import app

from api_pipeline.api_utils import updateIncidenceTable
from utils import Header,LabeledSelect,refreshdatesliderange
from utils import loadCSVData,update_alldata,verify_priordata,globaldataupdate,get_affecteddeaths_carddata
from modeling import col_map,country_map

# get relative data folder
import pathlib
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("../workdata").resolve()

#default loading country (first in list)
DEFAULTCOUNTRY = list(country_map.keys())[0]
# verify data for country list before lauching or restarting app 
# (after sleep on keroku)
# globaldataupdate()

def appcontent(app):
    # Loading default Dataframe and compute data
    # df = verify_priordata(DEFAULTCOUNTRY)
    df = loadCSVData(DEFAULTCOUNTRY,'Inc')
   
    # ================== LAYOUT=========================

    labelselectors = [
            LabeledSelect(
                id="select-country",
                options=[{"label": v, "value": k} for k,v in country_map.items()],
                value=list(country_map.keys())[0],
                #label="Filter by Country",
                label="Filtre par pays",
            ),
            LabeledSelect(
                id="select-type",
                options=[{"label": v, "value": k} for k, v in list(col_map.items())[0:4]],
                value='Confirmed',
                #label="Filter by data type",
                label="Filtre par type de cas",
            ), 
        ]

    daterangeselector = dcc.RangeSlider(
            id='date-slider',
            # label="Filter time range",
            # marks={i: '{}'.format(df['Date'][i]) for i in range(0,df.shape[0]-1,(df.shape[0]-1)//5)},
            min=0,
            max=df.shape[0]-1,
            value=[0, df.shape[0]-1]
            )

    incidencetypeselector = dcc.Checklist(
            id='inc-type',
            options=[
            # {'label': 'brut incidence', 'value': 'brut'},
            # {'label': 'moving average (7days)', 'value': 'MA'},
            # {'label': 'exponential moving average', 'value': 'EMA'}
            {'label': 'Incidence brute', 'value': 'brut'},
            {'label': 'Moyenne mobile', 'value': 'MA'},
            {'label': 'Moyenne exponentielle', 'value': 'EMA'}
            ],
            value=['MA', 'EMA'],
            labelStyle={'display': 'inline-block'}
            )

    # Card components
    cards = [
        dbc.Card(id='affected_card'),
        dbc.Card(id='mortality_card'),
        #dbc.Card(id='mortality_card2')
        ] 
    # Graph components
    graphs = [
        [
            dcc.Graph(id="graph-cumul"),
        ],
        [
            incidencetypeselector,
            dcc.Graph(id="graph-incidence"),
            
        ],
    ]

    # LAYOUT STACKING
    #app.layout = dbc.Container(
    page1_layout = html.Div(dbc.Container(
        [
            Header(app),
            html.Hr(), # Separation line
            dbc.Row([dbc.Col(card) for card in cards]), # 1 row with Xcard in column
            html.Br(),
            #GLOBAL SELECTORS : 1 row with x label selectors, 1 row with date
            dbc.Row([dbc.Col(selector) for selector in labelselectors]),
            dbc.Col(dbc.Col(daterangeselector)),

            #dbc.Row([dbc.Col(graph) for graph in graphs]),
            dbc.Row(dbc.Col(dbc.Card(graphs[0]))),
            html.Br(),
            dbc.Row(dbc.Col(dbc.Card(graphs[1]))),

            html.P(id='placeholder')
        ],
        fluid=False,
    ))
    return page1_layout

#GRAPHS
@app.callback(
    [Output("graph-cumul", "figure"),
    Output("graph-incidence", "figure"),
    Output('date-slider', 'marks'),
    Output('date-slider', 'max'),
    #Output("date-slider", "value"),
    ],
    [Input("select-country", "value"),
    Input("select-type", "value"),
    Input("date-slider", "value"),
    Input("inc-type", "value")]
)
def update_figures(country_val, datatype_val, daterange, inctype_val):
    # 1 - load country file
    #filepath = "workdata/incidence_"+country_val+"_Table.csv"
    #filepath = DATA_PATH.joinpath("incidence_"+country_val+"_Table.csv")
    #df = pd.read_csv(filepath)
    #df = verify_priordata(country_val)
    df = loadCSVData(country_val,'Inc')
    
    # missing something to refresh sliderange value if data length is different
    # from country to country

    # 3 refresh sliderange
    slidemarksdict,slidemaxval = refreshdatesliderange(df)

    # 4 - Filter dosplay based on chosen values
    # DATE RANGE
    xdf_filt = df.iloc[daterange[0]:daterange[1]]
    # DATA TYPES
    if 'brut' not in inctype_val :
        xdf_filt.drop([colname for colname in xdf_filt.columns if 'brut' in colname],
            axis=1,inplace=True)
    if 'MA' not in inctype_val :
        xdf_filt.drop([colname for colname in xdf_filt.columns if '_MM' in colname],
            axis=1,inplace=True)
    if 'EMA' not in inctype_val :
        xdf_filt.drop([colname for colname in xdf_filt.columns if '_eMM' in colname],
            axis=1,inplace=True)
    
    # 5 - draw graphe
    # cumulative graphe
    coef_fig = go.Figure(
        data=[go.Scatter(
            x=xdf_filt['Date'],
            y=xdf_filt[datatype_val],
            #color="condition",
            mode='lines')],
        layout=dict(
            title="Graphe de cumul",
            #title="Cumulative Graph (Total from beginning)",
            yaxis={
                 "autorange": True,
                 "showgrid": True,
                 "showline": True,
                 "title": "Nombre total",#"title": "Total number",
                 "type": "linear",
                 "zeroline": False,
                 },
            )
    )

    #incidence graphe
    incidencelist = [colname for colname in xdf_filt.columns if datatype_val in colname]
    incidencelist.pop(0) # first one is the cumul count
    coef_fig2 = go.Figure(
        data=[go.Scatter(x=xdf_filt['Date'],y=xdf_filt[col],name=col_map[col],mode='lines') 
             for col in incidencelist],
        layout=dict(
            #title="Incidence Graph (new cases / day)",
            title="Graphe d'incidence (Nouveaux cas par jour)",
            legend={
            "x": -0.0277108433735,
            "y": -0.142606516291,
            "orientation": "h"},
            yaxis={
                 "autorange": True,
                 "showgrid": True,
                 "showline": True,
                 "title": "Nombre supplémentaire / jour",#"title": "New people / day",
                 "type": "linear",
                 "zeroline": False,
                 },   
        )
    )

    return coef_fig,coef_fig2,slidemarksdict,slidemaxval #,daterange

#CARD
@app.callback(
    [Output("affected_card", "children"),
    Output("mortality_card", "children")],
    Input("select-country", "value"),
    )
def computeCardsComponents(country_val):
    #df = verify_priordata(country_val)
    print('updating global cards')
    #figlist = getFinalCountryList(group_val)

    cardlist = get_affecteddeaths_carddata([country_val])

    return cardlist[0],cardlist[1]

# =========================================
# # STARTING THE APP
# app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
# server = app.server
# appcontent(app)

# if __name__ == "__main__":
#     app.run_server(debug=True,host='0.0.0.0')