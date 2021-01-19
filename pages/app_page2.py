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
from utils import Header,LabeledSelect
from utils import loadCSVData
from modeling import col_map,country_map,continent_map

# get relative data folder
import pathlib
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("../workdata").resolve()


def getIncPerMillion(countrynamelist):
    # loading needeed data 
    dfpop = pd.read_csv(DATA_PATH.joinpath("population_2019.csv"),index_col=0)

    listoflist = []
    seriesdict = {}
    for name in countrynamelist :
        # load country data
        updateIncidenceTable(name)
        seriesdict[name] = loadCSVData(name,'Inc')['Confirmed_eMMincidence']

        # transformation

        #starting with absolute value of inc
        testserie = seriesdict[name].loc[(seriesdict[name]>100)].reset_index(drop=True)
        testserie = testserie/(float(dfpop['population'][name]))

        # starting with inc per million > 10
        #testserie = seriesdict[name]/(float(dfpop['population'][name]))
        #testserie = testserie.loc[(testserie>10)].reset_index(drop=True)
        #testserie = testserie    


        testdf = pd.DataFrame(testserie.tolist(),columns=[name])
        listoflist.append(testdf)
    
    comparativeinc= pd.concat(listoflist, axis=1)
    return comparativeinc

wdf = getIncPerMillion(list(country_map.keys()))

def appcontent(app):
  
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

    # Graph components
    graphs = [
        [
            dcc.Graph(id="graph-comparativeInc"),
        ],
    ]

    # LAYOUT STACKING
    #app.layout = dbc.Container(
    page1_layout = html.Div(dbc.Container(
        [
            Header("Dash Covid Visualization", app),
            html.Hr(), # Separation line
            #GLOBAL SELECTORS : 1 row with x label selectors, 1 row with date
            dbc.Row(dbc.Col(labelselectors[0])),
            html.Br(),
            dbc.Row(dbc.Col(labelselectors[1])),
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

@app.callback(
    Output("graph-comparativeInc", "figure"),
    [
    Input("abs-slider", "value"),
    Input("check-grouplist", "value"),
    ]
)
def update_comparative_incidence_figures(abscisserange,countrylist):
    # Loading default Dataframe and compute data
    print("inputlist : {}".format(countrylist))
    figlist = []
    for elem in continent_map.keys():
        if elem in countrylist :
            for x in list(continent_map[elem].keys()):
                figlist.append(x)

    if figlist == [] : figlist = countrylist
    print("FIGLIST : {}".format(figlist))
    # 4 - Filter dosplay based on chosen values
    # DATE RANGE
    wdf_filt = wdf.iloc[abscisserange[0]:abscisserange[1]]
    # 5 - draw graphe
    # comparative incidence graphe
    coef_fig = go.Figure(
        data=[
            go.Scatter(x=wdf_filt.index,y=wdf_filt[countryname],
                name=countryname,mode='lines') for countryname in figlist],
        layout=dict(
            title="Comparative incidence Graph (daily affecteds / million; start a inc > 1000per day)"
            )
    )

    return coef_fig
