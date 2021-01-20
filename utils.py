import pandas as pd
import numpy as np
import datetime
import threading

import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_core_components as dcc

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
        df = verify_priordata(name)

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
        #html.H2(f"{contaminationrate*100:.2f}% of {totalpop:.2f} millions", className="card-title",id='infected-rate'),
        #html.P(f"Population affected ; Total : {affectedvalue} (+{lastaffected} on last day)", className="card-text"),
        html.H2(f"{contaminationrate*100:.2f}% sur {totalpop:.2f} millions", className="card-title",id='infected-rate'),
        html.P(f"Population touchée ; Total : {affectedvalue} (+{lastaffected} hier)", className="card-text"),
    ],
    body=True,
    color="light",
    ),
    dbc.Card(
        [
            #html.H2(f"{mortalityrate*100:.2f}% of {affectedvalue/1000000:.2f} millions", className="card-title",id='mortality-rate'),
            #html.P(f"Mortality rate of affected ; Total : {deathvalue} (+{lastdeath} on last day)", className="card-text"),
            html.H2(f"{mortalityrate*100:.2f}% sur {affectedvalue/1000000:.2f} millions", className="card-title",id='mortality-rate'),
            html.P(f"Mortalité des cas confirmés ; Total : {deathvalue} (+{lastdeath} hier)", className="card-text"),
        ],
        body=True,
        color="dark",
        inverse=True,

    ),
    ]

    return cards

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
        print('Executing global data update')
        lastdfdate = open(LASTUPDATEFILE, 'w').write(
                today_object.strftime("%Y-%m-%d"))
        threading.Thread(target=update_alldata).start()
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
        getRawDataToCSV(countryname)
        updateIncidenceTable(countryname)
    print('global update finished')

def verify_priordata(paysname):
    """
        Function supposed to certify that 
        the incidence file exists for input country
        (function called during callbacks or app init)
    """
    # force call to api if Raw data not found
    try:
        rawdf = loadCSVData(paysname,'Raw')
    except FileNotFoundError:
        getRawDataToCSV(paysname)

    # read or create incidence file from raw file
    try:
        incdf = loadCSVData(paysname,'Inc')
    except FileNotFoundError:
        updateIncidenceTable(paysname)
        incdf = loadCSVData(paysname,'Inc')
    return incdf
