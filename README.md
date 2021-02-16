# covidDashboard

## quick presentation

The main goals of this project are :

1 - Request data using an API, control the response and process these data.

2 - Using Python/Flask/DASH to create a Dashboard and display informations, graphes, indicators etc. and deploy this app on PlateformAsAService cloud (I use Heroku)

3 - create a Data pipeline between 1 and 2 in order to keep our data up to date.

This project will be describe by these 3 axis, as it is, when treating data, how you are supposed to decompose your work, even your project.

*NOTE* : this work is supposed to be a demonstrator. I do use the FREE services on Clouds and I am often limited by what i can do (I will mention any time I discovered something (limitation or did not work as intended) and had to change things)

**More detailled are commented throughout each file !**

### summary
* Project architecture
    * Architecture Scheme
    * Architecture details

* Details on files/codes
    * GENERAL REMARKS
    * REQUESTING DATA
    * DISPLAYING DATA
    * DATA PIPELINE

## Project architecture

This project is build as an Flask/DASH app :
- global recommendations about flask application factory applies (https://hackersandslackers.com/flask-application-factory/)
- we use DASH to display data, so there are a few differences as DASH has its specificities.

### Architecture Scheme

    /app
    ├── Procfile.py (launch file used by HEROKU)
    ├── dockerfile  (docker file to build flas)
    ├── requirements.py
    │
    ├── config.py
    ├── .env
    ├── .gitignore
    │
    ├── wsgi.py
    ├── app.py
    ├── index.py
    │
    ├── modeling.py
    ├── utils.py
    │
    ├── /pages
    │   ├── app_overview.py
    │   ├── app_groupview.py
    │   └── app_countrydetails.py
    │
    ├── /api_pipeline
    │   ├── api_utils.py
    │   ├── Api_create_country_dict.ipynb
    │   ├── Pipeline_automation.ipynb
    │   └── /workdata
    │       ├── /inc
    │       └── /raw
    │
    ├── /workdata
    │   ├── country_concat_inner_translate_continent.csv
    │   ├── lastupdate.txt
    │   ├── /inc
    │   ├── /raw
    │
    └── /assets
        └── dash-logo.png


### Details on architecture

#### launch/build files

Procfile.py :launch file used by HEROKU
dockerfile  : docker file to build the flask/Dash server to work in local developpemnt
requirements.py : list of python librairies to get this project running

#### Config files 
config.py : contain parameters through out this project. Mostly folder names, column names from raw data.

.env : not included in Github folder. usually contains SECRET_KEY when needed. here it is used to simulate behavior on heroku cloud with the "ISHEROKU" variable checked when app launch. (see in index.py) 

.gitignore : used to ignore : 
* the /api_pipeline/workdata folder as it is a test folder. 
* temporary files coming from jupyter notebooks : pychache, checkpoints, .pyc files
* trash folder (when I create then during development some times)

#### Launch APP files

here is the difference coming from DASH :

1 - **wsgi.py** : entry point of the APP. import app from index file and run it.

2 - **app.py** : contain only app and server object (separate from wsgi). This file unique purpose is to be imported by each page of the app in order to get all the app context => this is what permit separation of DASH pages.

3 - **index.py** : this is the *MAIN display* of the app. It encapsulates all of the separates pages in *pages folder*. This allow to separate each pages, layout, and callback into it's own file and keep your DASH build a bit clearer.
    1- import app from app file
    2- import app pages from page folder
    3- perform setups (logging) and verification (type of environment) 
    4- setup a generic page layout that encapsulate the page content of child page
    5- setup app pages callbacks and link in URL forms and return corresponding layout from individual page.py


#### /pages files

Each file in this folder contains the configuration, layout and callbacks to its own page.
* the **MANDATORY** condition to this is the **from app import app** at the beginning of each file.
* *careful !* each callback or function names throughout all pages have to be unique 

If a function/display function/callback is common to several pages, it is removed from pages, written in the UTILS.PY file and imported back when needed.

**More detailled are commented throughout each pages**

For now, pages are organized as :
* **app_overview** : contains overview and sum up about all data available, gives current top incidence country, and a linear regression to compare result of countries between contaminated/mortality rates. This page do not have CALLBACK or way to modify displayed data.

* **app_groupview** : contains ways to compare countries with group selections and check boxes 

* **app_countrydetails** : contains ways to visualize data from one selected country.

#### /workdata files

contains base files froom which displayed data comes from :

* 1- *RAW and INC folders* : these files are updated by the globaldataupdate() function which requests from COVID19 API (in RAW) and enrichs them (with incidence computations) and write these new files in INC.

* 2- *Latestupdate.txt* : contains last date of data update if it has been completed. No need to run update several time a day...

* 3- *country_concat_inner_translate_continent.csv* : this file was built with tools in the api_pipeline folder. It contains the list of countries followed by the APP (in english and french), and their populations.

it is used for :
* building the country list to request from api 
* building the country list to display in the App
* run computation regarding counts of case per million population


#### /api_pipeline

contains :
* api_utils.py : which contains all final functions regarding API requesting / data transformation and data updates.

* jupyter notesbooks : (note used during app running) 
    * Pipeline automation : used for building/testing function before complete factorization in api_utils. 

    * Api_create_country_dict : contains one shot data formating of the country list and population file.

## Details on files/codes

### GENERAL REMARKS

Lot of try and error with the update data process. Had to deal with small scale issues of "coherence - availability" trade off. 
Main issues are :

- **limitations of API** : *With free configuration*, COVID19API limits its access and data available. I handle this with some temporisation between request, but this obviously extend duration of the GLOBALUPDATE process.

Put this process on threads : This reduce coherence but maintain availability until data has been updated (few minutes).

- **limitations of Cloud heroku** : *with free configuration*, several issues :
* 1 - worker computing power is limited so, updating process on threads can be longer, and computation during page display can slow display process. 
* 2 - worker go into sleep mode after 30 minutes of inactivit (no new request to serve), this limits availability because there is a few seconds delay to load the first page.
* 3 - it is possible to modify files on heroku server, but every time it go to sleep, it reinitialize folder to the github copy it is linked with. Meaning, every update on csv data files is wiped out at each shutdown, and re updated at each startup.

This is manageable by replacing CSV files with an external SQL database tools (which also has its limitations on free configuration). that's on of my next priorities.

### REQUESTING DATA

the api_utils.py first part ('extraction') contains functions I use to request and they are commented. 

In this part, I will focus on the configuration that I often use to build/verify/test/factorize "quickly".

In the project architecture, the **/api_pipeline** folder contains several Jupyter notebooks that I use to build and test functions on the fly. Once functions built, I can easily transfer them into api_utils.py, import them in my notebook and test them one more time before using them with flashdash app.

But ... In order to import api_utils painlessly in my notebook AND in my flask app, I have to tweak it a bit.

enter this small block at the beginning of api_utils :

    if __name__ == 'api_utils':
        import sys
        file = pathlib.Path(__file__).resolve()
        parent, root = file.parent, file.parents[1]
        sys.path.append(str(root))
        try:
            sys.path.remove(str(parent))
        except ValueError: # Already removed
            pass
        #need to ensure WORKDATAFOLDER is displaced to test folder with Jupyter
        WORKDATAFOLDER = 'api_pipeline/workdata'
    else :
        from config import WORKDATAFOLDER

In words :
If the main process is JUPYTER, its __name__ is *api_utils*, if it's flask api, its __name__ is *api_pipeline/api_utils*

For Jupyter, I have to : 
* relocate SYS.PATH to the parent folder (as it is when it's a flask process) because python cannot import things from parent directory of main process; and I need modeling.py and config.py in api_utils imports.

* make sure that the WORKDATAFOLDER is a the test folder.

Main advantage of this tweak is that I isolate testbed from the app : 
* my JupyterNotebooks are in a dedicated 'messytestfolder' and not in flaskapp ROOT, which is already crowded. 
* I can test/visualize results and tweak api_utils functions without messing with app architecture or data.

### DISPLAYING DATA

**UTILS.py** : contains common functions between different DASH pages.

* Display functions : like header of pages, links menu

* Compute functions : CARDS data with cumulative cases/death, percentage. Also graphes likes comparative incidence that are common to overview and group page.

### DATA PIPELINE