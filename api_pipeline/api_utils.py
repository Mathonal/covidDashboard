import requests
import math
import pandas as pd
from datetime import datetime
import time
import os
import logging

#External param
from api_config import (
    WORKDATAFOLDER,RAWFOLDER,INCFOLDER,
    COLUMNTOKEEP,COLUMNTOCOMPUTE,
    MAFACTOR
    )

import pathlib
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("../",WORKDATAFOLDER).resolve()

#===========================================
# EXTRACTION
#===========================================
def getRawDataToCSV(countryname):
    """
        get raw data from COVIDAPI for input country
        delete useless column
        write a CSV file in input folder : 
            workdatafolder+'/raw_'+countryname+'_ALLTable.csv'
    """ 
    # request loop integrated in getPandaFrameForCountry function
    # if error, it's a big one, just skip this country
    try :
        rawdf=pd.DataFrame(getPandaFrameForCountry(countryname))
    except :
        logging.error('getRawDataToCSV : API Error for {}. 5 loop failure'
            .format(countryname))
        return False
    else :
        # pre-treat DF 
        # 1 drop useless column
        rawdf.drop(rawdf.columns.difference(COLUMNTOKEEP), axis=1,inplace=True)
        # correct date
        correctDateOnPandaFrame(rawdf)
        # 3 write csv with raw files
        filepath = DATA_PATH.joinpath(RAWFOLDER,'raw_'+countryname+'_ALLTable.csv')
        rawdf.to_csv(filepath,index=False)
        logging.info('written raw CSV for {} at {}'.format(countryname,filepath))
        return True

def getPandaFrameForCountry(countryname):
    """
        return full data off covid19api for input countryname
        JSON format to transform in dataframe
        response.status_code : 200 : ok
        503 : Service Unavailable (wait a bit)
        502 : bad gateway (same as service overloaded)
        429 : too many request (wait a bit)

        if error at response : TRIES 5 times with 4 second interruption
    """
    # API config
    url = "https://api.covid19api.com/total/country/"+countryname
    payload = {}
    headers= {} 
    # request loop config
    Rcode = 0
    trycount = 0
    while Rcode != 200 and trycount < 5:
        response = requests.request("GET", url, headers=headers, data = payload)
        Rcode = response.status_code
        if Rcode != 200 :
            try : message = response.json()
            except : message = ''
            
            logging.warning('[{}] request code for {} : {}'
               .format(Rcode,countryname,message))
            time.sleep(4)  
        else : logging.debug('request OK for {}'.format(Rcode,countryname))
        trycount += 1
    return response.json()

def correctDateOnPandaFrame(pandasdataframe):
    """
        correct the specific date column format in covid19 api results
        2020-01-22T00:00:00Z
    """
    for i,elem in pandasdataframe.iterrows():
        splitdate = elem['Date'].split('T')
        newdate = datetime.strptime(splitdate[0], "%Y-%m-%d").date()
        pandasdataframe.at[i,'Date'] = newdate

#===========================================
# INCIDENCE COMPUTE
#===========================================

def buildbrutIncidence(rawData,countColumnName):
    """
        Epidemic incidence calculation : substract valueT-1 to ValueT of a column, 
        nullify aberations (<0)
        return a pandas.Series 
    """
    newdf = rawData[[countColumnName]]
    newdf['shift'] = newdf[countColumnName].shift(periods=1,fill_value=0)
    newdf['delta'] = newdf[countColumnName]-newdf['shift']
    #ZEROING negative values
    newdf['delta'] = newdf['delta'].apply(lambda x: 0 if x < 0 else x)
    return newdf['delta']
    
def incidenceMovingAverage(rawData,IncColumnName,nbfactor=2):
    """
        based on moving average calculation : get T-nbfactor lasts values from T and get a mean
        (firsts values are approximations on available values)
        return a pandas.Series
    """
    newdf = rawData[[IncColumnName]]
    listval = []
    #Loop Values
    for i in range(0,newdf.shape[0]):
        curval = 0
        if i < nbfactor:
            curval = pd.Series([newdf[IncColumnName][j] for j in range(0,i+1)]).mean()
        else :
            curval = pd.Series([newdf[IncColumnName][j] for j in range(i-nbfactor+1,i+1)]).mean()     
        listval.append(round(curval,1))
    return pd.Series(listval)

def incidenceExpMovingAverage(rawData,IncColumnName,alpha=0.1):
    """
        based on exponential moving average calculation : 
        get sum of T-nvalue * ( a(1-a)^n )
        return a pandas.Series
    """    
    newdf = rawData[[IncColumnName]]
    listval = []
    #Loop Values with sum alpha(1-alpha)^n * Xn
    for i in range(0,newdf.shape[0]):
        curval = 0
        curval = pd.Series([newdf[IncColumnName][j]*(alpha*math.pow((1-alpha),i-j)) 
                                for j in range(0,i+1)]).sum()   
        listval.append(round(curval,2))
    return pd.Series(listval)

#===========================================
# UPDATE INCIDENCE CSV
#===========================================

def loadCSVData(countryname,Datatype):
    if Datatype == 'Raw':
        #filepath = WORKDATAFOLDER+'/raw_'+countryname+'_ALLTable.csv'
        filepath = DATA_PATH.joinpath(RAWFOLDER,'raw_'+countryname+'_ALLTable.csv')
    elif Datatype == 'Inc':
        #filepath = WORKDATAFOLDER+'/incidence_'+countryname+'_Table.csv'
        filepath = DATA_PATH.joinpath(INCFOLDER,'incidence_'+countryname+'_Table.csv')
    try:
        paysdf = pd.read_csv(filepath)
    except:
        logging.debug('{} file for {} not found at : {}'
            .format(Datatype,countryname,filepath))
        raise FileNotFoundError
    return paysdf

def updateIncidenceTable(countryname,testmode=False):
    """
        load Raw table and incidence table, 
        verify if they have the same number of line 
        and complete/update the Incidence table if needed
    """
    logging.info('entering updateIncidenceTable for {}'.format(countryname))
    #loadexisting files

    # this try is not suppose to fail, as function launch at the condition
    # that an execution of getRawDataToCSV goes well
    try:
        rawdf = loadCSVData(countryname,'Raw')
    except FileNotFoundError:
        getRawDataToCSV(countryname)
        rawdf = loadCSVData(countryname,'Raw')
        # HERE IS an EXECUTION PROBLEM if raw data fails, no backup
        # there is a loop of requests in getrawdata function (5x) 

    try:
        incdf = loadCSVData(countryname,'Inc')
        incdfsize = incdf.shape[0]
    except FileNotFoundError:
        incdfsize = 0

    # comparing nb of lines
    datadelta = rawdf.shape[0]-incdfsize
    if datadelta > 0: # new lines to add
        logging.info('new data detected for {} : {} more lines'
            .format(countryname,datadelta))
        # add new raw data to Incidence DF
        startindex = max(0,incdfsize)
        deltadf = rawdf.loc[startindex:]
        if startindex ==0 : currentdf = deltadf
        else : currentdf = pd.concat([incdf,deltadf])
        
        # compute incidence types for each column 
        for colname in COLUMNTOCOMPUTE:
            brutname = colname+'_brutincidence'
            #recompute all incidence table
            currentdf[brutname] = buildbrutIncidence(currentdf,colname)           
            currentdf[colname+'_MMincidence'] = incidenceMovingAverage(currentdf,brutname,MAFACTOR)
            currentdf[colname+'_eMMincidence'] = incidenceExpMovingAverage(currentdf,brutname,0.1)
        
        # testmode write file in other name to compare with old file.
        if not testmode :
            #filepath = WORKDATAFOLDER+'/incidence_'+countryname+'_Table.csv'
            filepath = DATA_PATH.joinpath(INCFOLDER,'incidence_'+countryname+'_Table.csv')
        else :filepath = WORKDATAFOLDER+'/incidence_'+countryname+'_Tabletest.csv'
        
        # saving to pdf
        currentdf.to_csv(filepath,index=False)
        return True       

    else : 
        logging.info(', incidence update skipped for {} : no recent data detected '.format(countryname))
        return False
