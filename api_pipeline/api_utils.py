import requests
import math
import pandas as pd
from datetime import datetime
import time
import os

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
def getRawDataToCSV(paysname):
    """
        get raw data from COVIDAPI for input country
        delete useless column
        write a CSV file in input folder : 
            workdatafolder+'/raw_'+paysname+'_ALLTable.csv'
    """ 
    trycount = 0
    # try request loop
    while trycount < 5 :
        try :
            rawdf=pd.DataFrame(getPandaFrameForCountry(paysname))
        except :
            print('getRawDataToCSV : API Error for {}. loop {}'
                .format(paysname,str(trycount)))
            time.sleep(1)
        else : break
        finally : trycount +=1

    # drop useless column
    rawdf.drop(rawdf.columns.difference(COLUMNTOKEEP), axis=1,inplace=True)
    # correct date
    correctDateOnPandaFrame(rawdf)
    # write csv with raw files
    #filepath = WORKDATAFOLDER+'/raw_'+paysname+'_ALLTable.csv'
    filepath = DATA_PATH.joinpath(RAWFOLDER,'raw_'+paysname+'_ALLTable.csv')

    rawdf.to_csv(filepath,index=False)

def getPandaFrameForCountry(CountryName):
    """
        return full data off covid19api for input CountryName
        JSON format to transform in dataframe
    """
    url = "https://api.covid19api.com/total/country/"+CountryName
    payload = {}
    headers= {}
    response = requests.request("GET", url, headers=headers, data = payload)
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
    #print(newdf.shape[0])
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
    #print(newdf.shape[0])
    listval = []
    #Loop Values with sum alpha(1-alpha)^n * Xn
    for i in range(0,newdf.shape[0]):
        curval = 0
        curval = pd.Series([newdf[IncColumnName][j]*(alpha*math.pow((1-alpha),i-j)) 
                                for j in range(0,i+1)]).sum()   
        listval.append(round(curval,2))
        #print(i,round(curval,2))
    return pd.Series(listval)

#===========================================
# UPDATE INCIDENCE CSV
#===========================================

def loadCSVData(paysname,Datatype):
    if Datatype == 'Raw':
        #filepath = WORKDATAFOLDER+'/raw_'+paysname+'_ALLTable.csv'
        filepath = DATA_PATH.joinpath(RAWFOLDER,'raw_'+paysname+'_ALLTable.csv')
    elif Datatype == 'Inc':
        #filepath = WORKDATAFOLDER+'/incidence_'+paysname+'_Table.csv'
        filepath = DATA_PATH.joinpath(INCFOLDER,'incidence_'+paysname+'_Table.csv')
    try:
        paysdf = pd.read_csv(filepath)
    except:
        print('ERROR : file not found {}'.format(filepath))
        raise FileNotFoundError
    return paysdf

def updateIncidenceTable(paysname,testmode=False):
    """
        load Raw table and incidence table, 
        verify if they have the same number of line 
        and complete/update the Incidence table if needed
    """
    print('launch updateIncidenceTable')
    #loadexisting files
    try:
        rawdf = loadCSVData(paysname,'Raw')
    except FileNotFoundError:
        getRawDataToCSV(paysname)
        rawdf = loadCSVData(paysname,'Raw')
        # HERE IS an EXECUTION PROBLEM if raw data fails, no backup
        # there is a loop of requests in getrawdata function (3-5x) 

    try:
        incdf = loadCSVData(paysname,'Inc')
        incdfsize = incdf.shape[0]
    except FileNotFoundError:
        incdfsize = 0

    # comparing nb of lines
    datadelta = rawdf.shape[0]-incdfsize
    if datadelta > 0: # new lines to add
        print('new data detected for {} : {} more lines'
            .format(paysname,datadelta))
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
            #filepath = WORKDATAFOLDER+'/incidence_'+paysname+'_Table.csv'
            filepath = DATA_PATH.joinpath(INCFOLDER,'incidence_'+paysname+'_Table.csv')
        else :filepath = WORKDATAFOLDER+'/incidence_'+paysname+'_Tabletest.csv'
        
        # saving to pdf
        currentdf.to_csv(filepath,index=False)
        return True       

    else : 
        print('no recent data detected for {}, incidence update cancelled'.format(paysname))
        return False
