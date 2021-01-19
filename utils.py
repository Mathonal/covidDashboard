import pandas as pd
import numpy as np
import datetime
import threading

import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_core_components as dcc

from api_pipeline.api_utils import updateIncidenceTable,getRawDataToCSV,loadCSVData
from modeling import country_map

# ====== DISPLAY FUNCTIONS ========

def Header(name, app):
    return html.Div([get_header(name, app), html.Br([]), get_menu()])

def get_header(name, app):
    title = html.H2(name, style={"margin-top": 5})
    logo = html.Img(
        src=app.get_asset_url("dash-logo.png"), style={"float": "right", "height": 50}
    )
    #update_button = html.Button('Last Data', id='update_button',n_clicks=0)
    #return dbc.Row([dbc.Col(title, md=7), dbc.Col(update_button, md=2), dbc.Col(logo, md=3)])

    return dbc.Row([dbc.Col(title, md=9), dbc.Col(logo, md=3)])

def get_menu():
    PagesList = [
            dbc.Card(dbc.CardLink(
                "overview",
                href="/overview",
                className="tab first",
            )),
            dbc.Card(dbc.CardLink(
                "Generic Data per country",
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

# ====== PIPELINE EXEC =============
def globaldataupdate(testmode=False):
    print('Entering global update verification')
    #datetime verification
    today_object = datetime.date.today()
    try:
        lastdfdate_str = list(open('lastupdate.txt', 'r'))[0]
        lastdfdate = datetime.datetime.strptime(lastdfdate_str, '%Y-%m-%d').date()
    except:
        lastdfdate = 0

    if testmode : lastdfdate = 0
    #limited to one global update daily
    if today_object != lastdfdate :
        print('Executing global data update')
        lastdfdate = open('lastupdate.txt', 'w').write(
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
