
# ==============    GLOBAL LISTS/DICTS AND DESCRIPTION =============

# country_map = {
#     "France":"France",
#     "Germany":"Allemagne",   
#     "Belgium":"Belgique",
#     "China":"Chine",
#     "Spain":"Espagne",
#     "United States of America":"Etats-unis",
#     "Greece":"Grèce",
#     "India":"Inde",
#     "Ireland":"Ireland",
#     "Italy":"Italie",
#     "Netherlands":"Pays-bas",
#     "United Kingdom":"Royaume-unis",
#     "Russian Federation":"Russie",
#     "Sweden":"Suède",
#     "Switzerland":"Suisse",
# }

continent_map = {
    'Europe' : { 
        "France":"France",
        "Germany":"Allemagne",   
        "Belgium":"Belgique",
        "Spain":"Espagne",
        "Greece":"Grèce",
        "Ireland":"Ireland",
        "Italy":"Italie",
        "Netherlands":"Pays-bas",
        "United Kingdom":"Royaume-unis",
        "Sweden":"Suède",
        "Switzerland":"Suisse",
    },
    'America' : { 
        "United States of America":"Etats-unis",
        "Mexico" : "Mexique",
        #"Canada" : "Canada", bugg request return empty
        "Brazil":"Brazil",
    },
    'Asia' : { 
        "Russian Federation":"Russie",
        "India":"Inde",
        "China":"Chine",
    },
    'Africa' : {
        "South Africa" : "Afrique du sud",
        "Nigeria":"Nigeria",
        "Ethiopia":"Ethiopia"
    },
}

continentslist = ['Europe','America','Asia','Africa']

def get_countrymap():
    resultdict = {}
    for name in continentslist:
        somedict = {k:v for (k,v) in continent_map[name].items()}
        resultdict.update(somedict)
    return resultdict

country_map = get_countrymap()

col_map = {
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
