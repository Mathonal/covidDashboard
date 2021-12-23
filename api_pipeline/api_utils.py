import requests
import math
import pandas as pd
import datetime
import time
import threading
import os
import logging
import pathlib

# ****************************************
# PARAMETERS FROM CONFIG FILE
# have to verify if api_utils is imported from APP (sys.path on parent folder)
# or if it is imported from jupiter notebook (sys.path on current folder)

# HAVE to change sys.path for jupyter 
# because python cannot import module from parent directory of main process

# main process is jupyter, for app it's : api_pipeline/api_utils
if __name__ == 'api_utils': 
    import sys
    file = pathlib.Path(__file__).resolve()
    parent, root = file.parent, file.parents[1]
    sys.path.append(str(root))
    # Additionally remove the current file's directory from sys.path
    try:
        sys.path.remove(str(parent))
    except ValueError: # Already removed
        pass

    #need to ensure WORKDATAFOLDER is displaced to test folder with Jupyter
    WORKDATAFOLDER = 'api_pipeline/workdata'
else :
    from config import WORKDATAFOLDER
# ****************************************

# REST OF PARAMETERS ARE UNCHANGED
from config import (
        RAWFOLDER,INCFOLDER,
        COLUMNTOKEEP,COLUMNTOCOMPUTE,
        MAFACTOR,
        LASTUPDATEFILE
        )
from modeling import country_map

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
    # if error, it's a big one, skip this country
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
        (most of errors are 429)
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
        newdate = datetime.datetime.strptime(splitdate[0], "%Y-%m-%d").date()
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
    """
        specific functions to handle CSV loads in this project :
        - try to load CSV corresponding to country and type of file
        - return pandas data frame

        raise most common errors : "No file" and "empty file"
    """

    if Datatype == 'Raw':
        filepath = DATA_PATH.joinpath(RAWFOLDER,'raw_'+countryname+'_ALLTable.csv')
    elif Datatype == 'Inc':
        filepath = DATA_PATH.joinpath(INCFOLDER,'incidence_'+countryname+'_Table.csv')
    
    try:
        paysdf = pd.read_csv(filepath)
    except FileNotFoundError :
        # happens when new country in list or file deleted
        logging.debug('{} file for {} not found at : {}'
            .format(Datatype,countryname,filepath))
        raise FileNotFoundError
    except : 
        # file exists but DF is empty : happens with raw data file sometimes 
        logging.debug('{} file for {} exist but is empty'
            .format(Datatype,countryname))
        raise BufferError #buffer seems appropriate

    return paysdf

def updateIncidenceTable(countryname,testmode=False):
    """
        load Raw table and incidence table corresponding to ONE country, 
        verify if they have the same number of line 
        and complete/update the Incidence table if needed.

        There is an optimization to do when computing Inc file... 
        actual functions recompute all column from first day instead 
        of only computing missing values

        TESTMODE is meant for Jupyter use, to compare results/execs.
    """
    logging.info('entering updateIncidenceTable for {}'.format(countryname))
    # LOADING RAWFILE
    try:
        rawdf = loadCSVData(countryname,'Raw')
    except FileNotFoundError:
        # this try is not suppose to fail, as this function is called 
        # at the condition that an execution of getRawDataToCSV goes well 
        if not getRawDataToCSV(countryname) : # retry 
            logging.error('Re-attempt to request data for {} failed'
            .format(countryname))
            raise BufferError # parent process will ignore this country

        try : rawdf = loadCSVData(countryname,'Raw')
        except BufferError: raise BufferError
    except BufferError: raise BufferError 
    # this is when rawfile and DF are empty

    # LOADING INCIDENCE FILE
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
            #recompute all incidence table, can be optimized
            currentdf[brutname] = buildbrutIncidence(currentdf,colname)           
            currentdf[colname+'_MMincidence'] = incidenceMovingAverage(currentdf,brutname,MAFACTOR)
            currentdf[colname+'_eMMincidence'] = incidenceExpMovingAverage(currentdf,brutname,0.1)
        
        # testmode write file in other name to compare with old file.
        if not testmode :
            filepath = DATA_PATH.joinpath(INCFOLDER,'incidence_'+countryname+'_Table.csv')
        else : filepath = DATA_PATH.joinpath(INCFOLDER,'incidence_'+countryname+'_Tabletest.csv')
        # saving to pdf
        currentdf.to_csv(filepath,index=False)
        return True       

    else : 
        logging.info('incidence update skipped for {} : no recent data detected '.format(countryname))
        return False

def update_data(countrylist):
    """
        Run an update data on all countries defined in modeling
        loop supposed to be run in THREAD because 
        can be a bit long due to requesting API site 
    """
    logging.info('beginning global update thread')
    threadslist = []
    ignorelist = []
    for countryname in countrylist:
        # need to call a refresh of raw data from API
        if getRawDataToCSV(countryname) : 
            # before verifying if differences exists between raw and incidence tables
            try : 
                updateIncidenceTable(countryname)
            except BufferError :
                logging.error('update_alldata : RAWfile for {} is \
                empty, will be ignored'.format(countryname))
                ignorelist.append(countryname)
        else : 
            logging.error('update_alldata : RAW for {} not updated \
            (attempts failed)'.format(countryname))
            ignorelist.append(countryname)

    today_object = datetime.date.today()
    lastdfdate = open(LASTUPDATEFILE, 'w').write(
                today_object.strftime("%Y-%m-%d"))
    logging.info('update done with {} exceptions : {}'
        .format(len(ignorelist),ignorelist))

# ====== PIPELINE EXEC =============
def globaldataupdate(testmode=False):
    """
        determine if a global data update is launched :
            - last update file do not exist
            - date written in last update file is outdated
            - if testmode is true 
    """
    logging.debug('Entering global update verification')
    #datetime verification
    today_object = datetime.date.today()
    try:
        lastdfdate_str = list(open(LASTUPDATEFILE, 'r'))[0]
        lastdfdate = datetime.datetime.strptime(lastdfdate_str, '%Y-%m-%d').date()
    except:
        logging.warning('No last update found : will force data sync')
        lastdfdate_str = 0
        lastdfdate = 0

    if testmode : lastdfdate = 0

    #limited to one global update daily
    if today_object != lastdfdate :
        logging.warning('Executing global data update since {}'.format(lastdfdate_str))
        threading.Thread(target=update_data,args=(country_map.keys(),), daemon=True).start()
    else : 
        logging.info('global data already up to date : {}'.format(lastdfdate_str))
        #verifying is RAWDATA file exist for each country
        missinglist = []
        for country in country_map.keys():
            try: rawdf = loadCSVData(countryname,'Raw')
            except FileNotFoundError : missinglist.append(countryname)
            except : pass #do nothing, this country is bugged
        if len(missinglist)>0:
            logging.warning('Executing reduced data update for \
                missing country : {}'.format(missinglist))
            threading.Thread(target=update_data,args=(missinglist), daemon=True).start()