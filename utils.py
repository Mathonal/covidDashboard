# usefull libs
import pandas as pd
import numpy as np
import datetime
import logging
# DASH TOOLS
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import plotly.graph_objs as go
# MY TOOLS
from api_pipeline.api_utils import loadCSVData
#External param
from config import (
    LASTUPDATEFILE,
    WORKDATAFOLDER
    )
# get relative data folder
import pathlib
PATH = pathlib.Path(__file__)
DATA_PATH = PATH.joinpath("../workdata").resolve()

# LOAD POPULATION DATA (will not change > loaded as global)
DFPOP = pd.read_csv(DATA_PATH.joinpath(
    "country_concat_inner_translate_continent.csv"),index_col=0)

# ====== DISPLAY FUNCTIONS ========

def Header(app):
    """ 
        Assembling function of header and menu.
        clearer when called in layouts
    """
    return html.Div([get_header(app), html.Br([]), get_menu()])

def get_header(app):
    """ 
        construct simple head : title, author, dashlogo
        easy to modify
    """
    title = html.H2("Dashboard suivi Covid19", style={"margin-top": 5})
    author = html.H5("par Mathonal", style={"margin-top": 5})
    dashlogo = html.Img(
        src=app.get_asset_url("dash-logo.png"), style={"float": "right", "height": 50}
    )
    return dbc.Row([dbc.Col(title, md=6),dbc.Col(author, md=3), dbc.Col(dashlogo, md=3)])

def get_menu():
    """ Construct a link menu in form of 1 row with a group of cards """
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
    # POPULATION DF loaded after imports
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
    """
        build a data frame with incidence data from all country available
        - one column per country
        - incidence is rescale with country population for comparative purpose
        - INDEX base depends on dataScopeValue 
            - if STRING 'date' : keeps date referenciel
            - if integer : Nb of days since country passed Incidence threshold 
            value of X per millions
    """
    # POPULATION DATA is a global Dataframe  
    listoflist = []
    seriesdict = {}
    updatedcountrylist = countrynamelist.copy()

    for name in countrynamelist :
        # load country INC data as it is
        # not updateIncidenceTable(name) update for faster display 
        try :
            allframe = loadCSVData(name,'Inc')
        except: # ANY EXCEPT in laoding will result to skip the country
            logging.error('cannot open inc for {} : country ignored'.format(name))
            updatedcountrylist.remove(name)
            continue
        
        seriesdict[name] = allframe['Confirmed_eMMincidence']

        # Transformation
        # 1 - rescale incidence to country population
        testserie = seriesdict[name]/(float(DFPOP['population'][name]))
        # 2 - filter if treshold, and build Dataframe
        if type(dataScope) is int :
            # number is absolute treshold value of INCIDENCE /per million
            tresholdindex = testserie.loc[(
                testserie>dataScope)].index

            try : # if index is empty, no data, end this loop here
                testserie = testserie.loc[tresholdindex[0]:].reset_index(drop=True)
            except : continue

            testdf = pd.DataFrame(testserie.tolist(),columns=[name])
        else : 
            # keep dates as index, same temporality for every one
            testdf = pd.DataFrame(testserie.tolist(),columns=[name],
                index=[datetime.datetime.strptime(x, '%Y-%m-%d').date() 
                for x in allframe['Date']])

        listoflist.append(testdf)
    
    if listoflist == []:
        comparativeinc = None
    else : 
        comparativeinc= pd.concat(listoflist, axis=1).dropna(how='all')

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

