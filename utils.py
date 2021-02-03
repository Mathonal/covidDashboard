import pandas as pd
import numpy as np
import datetime
import logging

import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_core_components as dcc

import plotly.graph_objs as go

from api_pipeline.api_utils import updateIncidenceTable,getRawDataToCSV,loadCSVData

#External param
from config import (
    LASTUPDATEFILE,
    WORKDATAFOLDER
    )

# get relative data folder
import pathlib
PATH = pathlib.Path(__file__)
DATA_PATH = PATH.joinpath("../workdata").resolve()

DFPOP = pd.read_csv(DATA_PATH.joinpath(
    "country_concat_inner_translate_continent.csv"),index_col=0)

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
                "Vue par Continent",
                href="/groupview",
                className="tab",
            )),
            dbc.Card(dbc.CardLink(
                "Details par pays",
                href="/details-per-country",
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
    #DFPOP = pd.read_csv(DATA_PATH.joinpath("population_2019.csv"),index_col=0)
    #DFPOP = pd.read_csv("workdata/country_concat_inner_translate_continent.csv",index_col=0)
    affectedvalue = 0
    lastaffected = 0
    deathvalue = 0
    lastdeath = 0
    totalpop = 0 
    for name in figlist :
        #df = verify_priordata(name)
        try :
            df = loadCSVData(name,'Inc')
        except:
            continue

        lastline = df.shape[0]-1

        affectedvalue += df['Confirmed'][lastline]
        lastaffected += df['Confirmed_brutincidence'][lastline]
        deathvalue += df['Deaths'][lastline]
        lastdeath += df['Deaths_brutincidence'][lastline]
        totalpop += float(DFPOP['population'][name])  # population noted in millions

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
    #DFPOP = pd.read_csv("workdata/population_2019.csv",index_col=0)
    perflist = []
    indexlist = []

    for name in countrylist :
        try: df = loadCSVData(name,'Inc')
        except : continue

        lastline = df.shape[0]-1

        indexlist.append(name)
        perflist.append([df['Confirmed'][lastline],
            df['Deaths'][lastline],
            float(DFPOP['population'][name])])

    perfdf = pd.DataFrame(data=perflist,columns=['Confirmed','Deaths','population']
        ,index=indexlist)

    # LINEAR REGRESSION
    X = perfdf['Confirmed']/perfdf['population']
    Y = perfdf['Deaths']/perfdf['population']
    modelreg = np.polyfit(X, Y, 1)
    predict = np.poly1d(modelreg)
    
    logging.info('regression model on {} country : {}'.format(len(indexlist),modelreg))

    # Line trace 
    stepline = round(max(X)/100)
    linex=range(0,round(max(X)),stepline)
    liney=predict(linex)

    graphperf = go.Figure(
        data=[
            #go.Scatter(x=wdf_filt.index,y=wdf_filt[countryname],
            go.Scatter(x=X,y=Y,
                marker=dict(
                    size=perfdf['population'],
                    sizeref=2.*max(perfdf['population'])/(12.**2),
                    sizemin=4                   
                    ),
                mode='markers',
                text=perfdf.index),
            go.Scatter(x=list(linex),y=list(liney))
            ],
        layout=dict(
            #title="Comparative incidence Graph",
            title="Comparaison Nombre décès / Nombre de cas par pays",
            xaxis={
                "autorange": True,
                "showline": True,
                "title": "Nombre de cas / million",
                #"title": "days since first incidence > 100/day",
                "type": "log",
                         },
            yaxis={
                 "autorange": True,
                 "showgrid": True,
                 "showline": True,
                 #"title": "new daily affected / million population",
                 "title": "Nombre de décès / million",
                 #"type": "log",
                 "zeroline": False,
                 }
            )
    )

    graphperf.update_layout(showlegend=False)
    return dcc.Graph(figure=graphperf)

def getIncPerMillion(countrynamelist,dataScope='date'):
    # loading needeed data 
    #DFPOP = pd.read_csv(DATA_PATH.joinpath("population_2019.csv"),index_col=0)

    listoflist = []
    seriesdict = {}
    updatedcountrylist = countrynamelist.copy()

    for name in countrynamelist :
        # load country data
        # updateIncidenceTable(name) cutting update for faster display 
        try :
            allframe = loadCSVData(name,'Inc')
        except:
            logging.error('cannot open inc for {} : country ignored'.format(name))
            updatedcountrylist.remove(name)
            continue
        # need to add a error treatment if file not found
        seriesdict[name] = allframe['Confirmed_eMMincidence']
        
        # transformation
        #starting with absolute value of inc
        if dataScope == 'date' :
            testserie = seriesdict[name]#.loc[(seriesdict[name]>100)].reset_index(drop=True)
        else : testserie = seriesdict[name].loc[(seriesdict[name]>100)].reset_index(drop=True)

        testserie = testserie/(float(DFPOP['population'][name]))
        
        #starting with inc per million > 10
        #testserie = seriesdict[name]/(float(DFPOP['population'][name]))
        #testserie = testserie.loc[(testserie>10)].reset_index(drop=True)
        #testserie = testserie    
        if dataScope == 'date' : 
            testdf = pd.DataFrame(testserie.tolist(),columns=[name],
                index=[datetime.datetime.strptime(x, '%Y-%m-%d').date() for x in allframe['Date']])
        else : testdf = pd.DataFrame(testserie.tolist(),columns=[name])
        listoflist.append(testdf)
    
    if listoflist == []:
        comparativeinc = None
    else : comparativeinc= pd.concat(listoflist, axis=1)

    return comparativeinc,updatedcountrylist

def comparativeIncidenceFigure(wdf_filt,countrylist,title):
    # draw graphe comparative incidence graphe
    figureToPrint = go.Figure(
        data=[
            go.Scatter(x=wdf_filt.index,y=wdf_filt[countryname],
                name=countryname,mode='lines') for countryname in countrylist],
        layout=dict(
            #title="Comparative incidence Graph",
            title=title,
            xaxis={
                "autorange": True,
                "showline": True,
                #"title": "days since first incidence > 100/day",
                #"title": "days since first incidence > 100/day",
                #"type": "category",
                         },
            yaxis={
                 "autorange": True,
                 "showgrid": True,
                 "showline": True,
                 #"title": "new daily affected / million population",
                 "title": "Nouveaux cas quotidien par million d'habitants",
                 "type": "linear",
                 "zeroline": False,
                 }
            )
    )
    return figureToPrint 

