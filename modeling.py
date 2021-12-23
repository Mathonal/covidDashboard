import pandas as pd

# get relative data folder
import pathlib
PATH = pathlib.Path(__file__)
DATA_PATH = PATH.joinpath("../workdata").resolve()

# ==============    GLOBAL LISTS/DICTS AND DESCRIPTION =============
# BUGGED country : rawfile empty
#['Aruba', 'Bermuda', 'Greenland', 'Guam', 'Kiribati', 'New Caledonia',
# 'French Polynesia', 'Puerto Rico', 'American Samoa', 'Chad', 'Thailand',
# 'Timor-Leste', 'Tonga', 'Turkmenistan', 'Cayman Islands', 
# 'Northern Mariana Islands', 'Isle of Man']


countrydf = pd.read_csv(PATH.joinpath(DATA_PATH,
    "country_concat_inner_translate_continent.csv"))

def get_continentmapandlist(pdc):
    Continentlist = pdc['continent'].unique()
    Continentlist.sort()
    
    resultdict = {}
    for continentname in Continentlist:
        pdextract = pdc[['country','countryfr']].loc[
            (pdc['continent'] == continentname)]
        somedict = {row[1]['country']:row[1]['countryfr'] 
        for row in pdextract.iterrows()}
        resultdict[continentname] = somedict
    return resultdict,list(Continentlist)

def get_countrymap(pdc):
    pdc_filt = pdc.sort_values('countryfr')
    resultdict = {}
    for row in pdc_filt.iterrows():
        resultdict[row[1]['country']] = row[1]['countryfr']
    return resultdict

country_map = get_countrymap(countrydf)
continent_map,continentslist = get_continentmapandlist(countrydf)

col_map = {
    "Confirmed":"Nombre de cas confirmés cumulés",
    "Deaths":"Nombre de décès cumulés",
    "Recovered":"Nombre de guérisons cumulées ",
    "Active":"Nombre de cas actifs cumulés",
    #"Date":"Dates",
    "Confirmed_brutincidence":"Incidence brute des cas confirmés ",
    "Confirmed_MMincidence":"Moyenne mobile d'incidence des cas confirmés (7jours)",
    "Confirmed_eMMincidence":"Moyenne exponentielle d'incidence des cas confirmés",
    "Deaths_brutincidence":"Incidence brute des décès",
    "Deaths_MMincidence":"Moyenne mobile d'incidence des décès (7jours)",
    "Deaths_eMMincidence":"Moyenne exponentielle d'incidence de décès",
    "Recovered_brutincidence":"Incidence brute des guérisons",
    "Recovered_MMincidence":"Moyenne mobile d'incidence des guérisons (7jours)",
    "Recovered_eMMincidence":"Moyenne exponentielle d'incidence de guérisons",
    "Active_brutincidence":"Incidence brute des cas actifs",
    "Active_MMincidence":"Moyenne mobile d'incidence des cas actifs (7jours)",
    "Active_eMMincidence":"Moyenne exponentielle d'incidence de cas actifs",
}

col_map_eng = {
    "Confirmed":"Cumulative Confirmed case",
    "Deaths":"Cumulative Deaths case",
    "Recovered":"Cumulative Recovered case",
    "Active":"Cumulative Active case",
    #"Date":"Dates",
    "Confirmed_brutincidence":"Confirmed cases daily incidence",
    "Confirmed_MMincidence":"Confirmed cases moving average (7days)",
    "Confirmed_eMMincidence":"Confirmed cases exponential moving average",
    "Deaths_brutincidence":"Deaths cases daily incidence",
    "Deaths_MMincidence":"Deaths cases moving average (7days)",
    "Deaths_eMMincidence":"Deaths cases exponential moving average",
    "Recovered_brutincidence":"Recovered cases daily incidence",
    "Recovered_MMincidence":"Recovered cases moving average (7days)",
    "Recovered_eMMincidence":"Recovered cases exponential moving average",
    "Active_brutincidence":"Active cases daily incidence",
    "Active_MMincidence":"Active cases moving average (7days)",
    "Active_eMMincidence":"Active cases exponential moving average",
}

# continent_map = {
#     'Europe' : { 
#         "France":"France",
#         "Germany":"Allemagne",   
#         "Belgium":"Belgique",
#         "Spain":"Espagne",
#         "Greece":"Grèce",
#         "Ireland":"Ireland",
#         "Italy":"Italie",
#         "Netherlands":"Pays-bas",
#         "Poland":"Pologne",
#         "Ukraine":"Ukraine",
#         "United Kingdom":"Royaume-unis",
#         "Sweden":"Suède",
#         "Switzerland":"Suisse",
#         "Turkey":"Turquie",
#         "Romania":"Roumanie",
#         "Portugal":"Portugal",
#         "Czech Republic":"Tchéquie",
#     },
#     'America' : { 
#         "United States of America":"Etats-unis",
#         "Mexico" : "Mexique",
#         "Canada" : "Canada", # bugg request return empty
#         "Brazil":"Brazil",
#         "Colombia":"Colombia",
#         "Argentina":"Argentina",
#         "Peru":"Perou",
#         "Chile":"Chili",
#         "Ecuador":"Equateur",
#         "Guatemala":"Guatemala",
#         "Dominican Republic":"Republique Dominicaine",
#         "Cuba":"Cuba",
#         "Haiti":"Haiti",
#         "Bolivia":"Bolivie",
#     },
#     'Asia' : {
#         "Afghanistan":"Afghanistan",
#         "India":"Inde",
#         "Indonesia":"Indonésie",
#         "Bangladesh":"Bangladesh",
#         "China":"Chine",
#         "Japan":"Japon",
#         "Myanmar":"Byrmanie",
#         "Pakistan":"Pakistan",
#         "Philippines":"Philippines",
#         "Russian Federation":"Russie",
#         "Thailand":"Thailande",
#         "Uzbekistan":"Uzbekistan",
#         "Malaysia":"Malaisie",
#         "Nepal":"Nepal",
#         "Australia":"Australie",
#         "Sri Lanka":"Sri Lanka",
#         "Kazakhstan":"Kazakhstan",
#         "Cambodia":"Cambodge",
#     },
#     'Africa' : {
#         "Algeria":"Algeria",
#         "Iraq":"Iraq",
#         "South Africa" : "Afrique du sud",
#         "Morocco":"Maroc",
#         "Nigeria":"Nigeria",
#         "Ethiopia":"Ethiopia",
#         "Kenya":"Kenya",
#         "Sudan":"Sudan",
#         "Saudi Arabia":"Arabie Saoudite",
#         "Uganda":"Uganda",
#         "Angola":"Angola",
#         "Mozambique":"Mozambique",
#         "Ghana":"Ghana",
#         "Madagascar":"Madagascar",
#         "Cameroon":"Cameroon",
#         "Niger":"Niger",
#         "Burkina Faso":"Burkina Faso",
#         "Mali":"Mali",
#         "Malawi":"Malawi",
#         "Zambia":"Zambie",
#         "Azerbaijan":"Azerbaijan",
#         "Jordan":"Jordan",
#         "South Sudan":"South Sudan",
#         "Benin":"Benin",
#         "Rwanda":"Rwanda",
#         "Guinea":"Guinea",
#         "Zimbabwe":"Zimbabwe",
#         "Somalia":"Somalie",
#         "Chad":"Chad",
#         "Burundi":"Burundi",
#         "Tunisia":"Tunisie",
#     },
# }

# continentslist = ['Europe','America','Asia','Africa']

# def get_countrymap():
#     resultdict = {}
#     for name in continentslist:
#         somedict = {k:v for (k,v) in continent_map[name].items()}
#         resultdict.update(somedict)
#     return resultdict
