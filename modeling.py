#from aix360.algorithms.rbm import LogisticRuleRegression, FeatureBinarizer
import pandas as pd
#from sklearn.model_selection import train_test_split

# col_map = {
#     "trestbps": "Resting blood pressure (trestbps)",
#     "chol": "Cerum cholestoral (chol)",
#     "fbs": "Fasting blood sugar (fbs)",
#     "restecg": "Resting electrocardiographic results (restecg)",
#     "thalach": "Maximum heart rate achieved (thalach)",
#     "exang": "Exercise induced angina (exang)",
#     "oldpeak": "S-T depression induced by exercise relative to rest (oldpeak)",
#     "age": "Age",
#     "sex": "Sex",
#     "cp": "Chest pain type (cp)",
#     "slope": "Slope of peak exercise S-T segment (slope)",
#     "ca": "Number of major vessels (ca)",
#     "thal": "Defect type (thal)",
# }

country_map = {
    "France":"France",
    "Germany":"Allemagne",   
    "Belgium":"Belgique",
    "China":"Chine",
    "Spain":"Espagne",
    "United States of America":"Etats-unis",
    "Greece":"Grèce",
    "India":"Inde",
    "Ireland":"Ireland",
    "Italy":"Italie",
    "Netherlands":"Pays-bas",
    "United Kingdom":"Royaume-unis",
    "Russia":"Russie",
    "Sweden":"Suède",
    "Switzerland":"Suisse",
}

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

num2desc = {
    "sex": {0: "Female", 1: "Male"},
    "cp": {
        0: "typical angina",
        1: "atypical angina",
        2: "non-aginal pain",
        3: "asymptomatic",
    },
    "fbs": {0: "False", 1: "True"},
    "restecg": {
        0: "normal",
        1: "ST-T wave abnormality",
        2: "left ventricular hypertrophy",
    },
}

# Load and preprocess dataset
#df = pd.read_csv("workdata/incidence_France_Table.csv")
#for k, v in num2desc.items():
#    df[k] = df[k].replace(v)

#y = df.pop("target")
#dfTrain, dfTest, yTrain, yTest = train_test_split(df, y, random_state=0, stratify=y)

#fb = FeatureBinarizer(negations=True, returnOrd=True)
#dfTrain, dfTrainStd = fb.fit_transform(dfTrain)
#dfTest, dfTestStd = fb.transform(dfTest)

# Train model
#lrr = LogisticRuleRegression(lambda0=0.005, lambda1=0.001, useOrd=True)
#lrr.fit(dfTrain, yTrain, dfTrainStd)
