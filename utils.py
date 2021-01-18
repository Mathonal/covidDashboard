import pandas as pd
import numpy as np
import datetime
import threading

from api_pipeline.api_utils import updateIncidenceTable,getRawDataToCSV,loadCSVData
from modeling import country_map

def globaldataupdate(testmode=False):
    print('Entering global update verification')
    #datetime verification
    today_object = datetime.date.today()
    try:
        lastdfdate = list(open('lastupdate.txt', 'r'))[0]
        lastdfdate = datetime.datetime.strptime(lastdfdate, '%Y-%m-%d').date()
    except:
        lastdfdate = 0

    if testmode : lastdfdate = 0
    #limited to one global update daily
    if today_object != lastdfdate :
        print('Executing global data update')
        lastdfdate = open('lastupdate.txt', 'w').write(
                today_object.strftime("%Y-%m-%d"))
        threading.Thread(target=update_alldata).start()

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
