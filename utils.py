import pandas as pd
import numpy as np
import datetime
import threading

import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_core_components as dcc

import plotly.graph_objs as go

from api_pipeline.api_utils import updateIncidenceTable,getRawDataToCSV,loadCSVData
from modeling import country_map

#External param
from api_config import LASTUPDATEFILE

# ====== DISPLAY FUNCTIONS ========

def Header(app):
    return html.Div([get_header(app), html.Br([]), get_menu()])

def get_header(app):
    title = html.H2("Dashboard suivi Covid19", style={"margin-top": 5})
    subtitle = html.H5("par Mathonal", style={"margin-top": 5})
    logo = html.Img(
        src=app.get_asset_url("dash-logo.png"), style={"float": "right", "height": 50}
    )
    return dbc.Row([dbc.Col(title, md=6),dbc.Col(subtitle, md=3), dbc.Col(logo, md=3)])

def get_menu():
    PagesList = [
            dbc.Card(dbc.CardLink(
                "Vue Globale",
                href="/overview",
                className="tab first",
            )),
            dbc.Card(dbc.CardLink(
                "Details par pays",
                href="/generic-per-country",
                className="tab",
            )),
            # dbc.Card(dbc.CardLink(
            #     "Portfolio & Management",
            #     href="/dash-financial-report/portfolio-management",
            #     className="tab",
            # )),
        ]

    # 1 row with Xcard in column
    return dbc.Row([dbc.Col(elem) for elem in PagesList])

def LabeledSelect(label, **kwargs):
    return dbc.FormGroup([dbc.Label(label), dbc.Select(**kwargs)])


def refreshdatesliderange(df):
    # 3 - renew slide range to DF size
    slidemax = df.shape[0]-1

    # define fixed intervals
    dictstep = round(slidemax/5)

    #first values of dataframe range
    slidemarksdict = {i: '{}'.format(df['Date'][i]) for i in range(
        0,slidemax,dictstep)}
    #last val of DATAFRAME : mandatory
    slidemarksdict[slidemax] = '{}'.format(df['Date'][slidemax])
    
    return slidemarksdict,slidemax

# ====== COMPUTE FUNCTIONS ==========

def get_affecteddeaths_carddata(figlist):
    #dfpop = pd.read_csv(DATA_PATH.joinpath("population_2019.csv"),index_col=0)
    dfpop = pd.read_csv("workdata/population_2019.csv",index_col=0)
    affectedvalue = 0
    lastaffected = 0
    deathvalue = 0
    lastdeath = 0
    totalpop = 0 
    for name in figlist :
        #df = verify_priordata(name)
        df = loadCSVData(name,'Inc')

        lastline = df.shape[0]-1

        affectedvalue += df['Confirmed'][lastline]
        lastaffected += df['Confirmed_brutincidence'][lastline]
        deathvalue += df['Deaths'][lastline]
        lastdeath += df['Deaths_brutincidence'][lastline]
        totalpop += float(dfpop['population'][name])  # population noted in millions

    #return affectedvalue,lastaffected,deathvalue,lastdeath,totalpop

    # compute RATES
    mortalityrate = deathvalue/affectedvalue
    contaminationrate = affectedvalue/(totalpop*1000000)

    # Card components    
    cards = [
    dbc.Card(
    [
        html.H4("Population touchée", className="card-text"),
        #html.H2(f"{contaminationrate*100:.2f}% of {totalpop:.2f} millions", className="card-title",id='infected-rate'),
        #html.P(f"Population affected ; Total : {affectedvalue} (+{lastaffected} on last day)", className="card-text"),
        html.H2(f"{contaminationrate*100:.2f}% sur {totalpop:.2f} millions", className="card-title",id='infected-rate'),
        html.P(f" Total : {affectedvalue} (+{lastaffected} hier)", className="card-text"),
        #html.P(f"Population touchée ; Total : {affectedvalue} (+{lastaffected} hier)", className="card-text"),
    ],
    body=True,
    color="light",
    ),
    dbc.Card(
        [
            html.H4("Mortalité des cas confirmés", className="card-text"),
            #html.H2(f"{mortalityrate*100:.2f}% of {affectedvalue/1000000:.2f} millions", className="card-title",id='mortality-rate'),
            #html.P(f"Mortality rate of affected ; Total : {deathvalue} (+{lastdeath} on last day)", className="card-text"),
            html.H2(f"{mortalityrate*100:.2f}% sur {affectedvalue/1000000:.2f} millions", className="card-title",id='mortality-rate'),
            html.P(f"Total : {deathvalue} (+{lastdeath} hier)", className="card-text"),
        ],
        body=True,
        color="dark",
        inverse=True,

    ),
    ]

    return cards

def graphcountryperf(countrylist):
    dfpop = pd.read_csv("workdata/population_2019.csv",index_col=0)
    perflist = []
    indexlist = []

    for name in countrylist :
        df = loadCSVData(name,'Inc')
        lastline = df.shape[0]-1

        indexlist.append(name)
        perflist.append([df['Confirmed'][lastline],
            df['Deaths'][lastline],
            float(dfpop['population'][name])])

    perfdf = pd.DataFrame(data=perflist,columns=['Confirmed','Deaths','population']
        ,index=indexlist)

    # LINEAR REGRESSION
    modelreg = np.polyfit(perfdf['Confirmed'], perfdf['Deaths'], 1)
    predict = np.poly1d(modelreg)
    x=range(0,max(perfdf['Confirmed']),50000)
    y=predict(x)

    graphperf = go.Figure(
        data=[
            #go.Scatter(x=wdf_filt.index,y=wdf_filt[countryname],
            go.Scatter(x=perfdf['Confirmed'],
                y=perfdf['Deaths'],
                marker=dict(
                    size=perfdf['population'],
                    sizeref=2.*max(perfdf['population'])/(10.**2),
                    sizemin=5                   
                    ),
                mode='markers',
                text=perfdf.index),
            go.Scatter(x=list(x),y=list(y))
            ],
        layout=dict(
            #title="Comparative incidence Graph",
            title="Comparaison Nombre décès / Nombre de cas par pays",
            xaxis={
                "autorange": True,
                "showline": True,
                "title": "Nombre de cas",
                #"title": "days since first incidence > 100/day",
                "type": "log",
                         },
            yaxis={
                 "autorange": True,
                 "showgrid": True,
                 "showline": True,
                 #"title": "new daily affected / million population",
                 "title": "Nombre de décès",
                 "type": "log",
                 "zeroline": False,
                 }
            )
    )

    graphperf.update_layout(showlegend=False)
    return dcc.Graph(figure=graphperf)


# ====== PIPELINE EXEC =============
def globaldataupdate(testmode=False):
    print('Entering global update verification')
    #datetime verification
    today_object = datetime.date.today()
    try:
        lastdfdate_str = list(open(LASTUPDATEFILE, 'r'))[0]
        lastdfdate = datetime.datetime.strptime(lastdfdate_str, '%Y-%m-%d').date()
    except:
        lastdfdate = 0

    if testmode : lastdfdate = 0

    #limited to one global update daily
    if today_object != lastdfdate :
        print('Executing global data update to date : {}'.format(lastdfdate_str))
        threading.Thread(target=update_alldata).start()
        lastdfdate = open(LASTUPDATEFILE, 'w').write(
                today_object.strftime("%Y-%m-%d"))
    else : print('data already updated : {}'.format(lastdfdate_str))

def update_alldata():
    """
        Run an update data on all countries defined in modeling
        loop supposed to be run in THREAD because 
        can be a bit long due to requesting API site 
    """
    print('beginning global update thread')
    threadslist = []
    for countryname in country_map.keys():
        # need to call a refresh of raw data from API
        getRawDataToCSV(countryname)
        # before verifying if differences exists between raw and incidence tables
        updateIncidenceTable(countryname)
    print('global update finished')

def verify_priordata(paysname):
    """
        Function supposed to certify that 
        the incidence file exists for input country
        (function called during callbacks or app init)
    """
        # THIS PART IS ALREADY DONE IN updateIncidenceTable
        # force call to api if Raw data not found
        #try:
        #    rawdf = loadCSVData(paysname,'Raw')
        #except FileNotFoundError:
        #    getRawDataToCSV(paysname)

    # read or create incidence file from raw file
    # ONLY UPDATE IF incidence file not found, not if incidence file outdated
    try:
        incdf = loadCSVData(paysname,'Inc')
    except FileNotFoundError:
        updateIncidenceTable(paysname)
        incdf = loadCSVData(paysname,'Inc')
    return incdf
