import datetime
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

#from sklearn.metrics import accuracy_score

pd.options.mode.chained_assignment = None

from api_pipeline.api_utils import updateIncidenceTable
from utils import update_alldata,verify_priordata,globaldataupdate
from modeling import col_map,country_map

# verify data for country list before lauching or restarting app 
# (after sleep on keroku)
globaldataupdate()

def appcontent(app):

    def Header(name, app):
        title = html.H2(name, style={"margin-top": 5})
        logo = html.Img(
            src=app.get_asset_url("dash-logo.png"), style={"float": "right", "height": 50}
        )
        #update_button = html.Button('Last Data', id='update_button',n_clicks=0)
        #return dbc.Row([dbc.Col(title, md=7), dbc.Col(update_button, md=2), dbc.Col(logo, md=3)])

        return dbc.Row([dbc.Col(title, md=9), dbc.Col(logo, md=3)])

    def LabeledSelect(label, **kwargs):
        return dbc.FormGroup([dbc.Label(label), dbc.Select(**kwargs)])


    # Compute the explanation dataframe, GAM, and scores

    #df = pd.read_csv("workdata/incidence_France_Table.csv")
    df = verify_priordata('France')

    # compute few data
    lastline = df.shape[0]-1
    mortalityrate = df['Deaths'][lastline]/df['Confirmed'][lastline]

    dfpop = pd.read_csv("workdata/population_2019.csv",index_col=0)
    print(dfpop['population']['France'])
    contaminationrate = df['Confirmed'][lastline]/(float(dfpop['population']['France'])*1000000)

    # Card components
    cards = [
        dbc.Card(
        [
            html.H2(f"{contaminationrate*100:.2f}%", className="card-title",id='infected-rate'),
            html.P("population infected", className="card-text"),
        ],
        body=True,
        color="dark",
        inverse=True,
        ),
        dbc.Card(
            [
                html.H2(f"{mortalityrate*100:.2f}%", className="card-title",id='mortality-rate'),
                html.P("Mortality Rate (of infected)", className="card-text"),
            ],
            body=True,
            color="light",
        ),

        ]
    #     dbc.Card(
    #         [
    #             html.H2(f"{dfTrain.shape[0]} / {dfTest.shape[0]}", className="card-title"),
    #             html.P("Train / Test Split", className="card-text"),
    #         ],
    #         body=True,
    #         color="primary",
    #         inverse=True,
    #     ),
    # ]

    labelselectors = [
            LabeledSelect(
                id="select-country",
                options=[{"label": v, "value": k} for k,v in country_map.items()],
                #value=list(xPlot.keys())[0],
                value=list(country_map.keys())[0],
                label="Filter by Country",
            ),
            LabeledSelect(
                id="select-type",
                options=[{"label": v, "value": k} for k, v in list(col_map.items())[0:4]],
                #value=list(xPlot.keys())[0],
                value='Confirmed',
                label="Filter by data type",
            ), 
        ]


    otherselectors = [
            dcc.RangeSlider(
            id='date-slider',
            # label="Filter time range",
            # marks={i: '{}'.format(df['Date'][i]) for i in range(0,df.shape[0]-1,(df.shape[0]-1)//5)},
            min=0,
            max=df.shape[0]-1,
            value=[0, df.shape[0]-1]
            ),
            dcc.Checklist(
            id='inc-type',
            options=[
            {'label': 'brut incidence   ', 'value': 'brut'},
            {'label': 'moving average (7days)   ', 'value': 'MA'},
            {'label': 'exponential moving average', 'value': 'EMA'}
            ],
            value=['MA', 'EMA'],
            labelStyle={'display': 'inline-block'}
    ) 
    ]


    # Graph components
    graphs = [
        [
            # LabeledSelect(
            #     id="select-type",
            #     options=[{"label": v, "value": k} for k, v in col_map.items()],
            #     #value=list(xPlot.keys())[0],
            #     value='Confirmed',
            #     label="Filter type",
            # ),
            dcc.Graph(id="graph-cumul"),
            dcc.Graph(id="graph-incidence"),
        ],
        # [
        #     LabeledSelect(
        #         id="select-type",
        #         options=[{"label": v, "value": k} for k, v in col_map.items()],
        #         value=list(xPlot.keys())[0],
        #         label="Filter Features",
        #     ),
        #     dcc.Graph(id="graph-cumul"),
        # ],
        # [
        #     LabeledSelect(
        #         id="select-gam",
        #         options=[{"label": col_map[k], "value": k} for k in xPlot.keys()],
        #         value=list(xPlot.keys())[0],
        #         label="Visualize GAM",
        #     ),
        #     dcc.Graph("graph-gam"),
        # ],
    ]

    app.layout = dbc.Container(
        [
            Header("Dash Covid Visualization", app),
            html.Hr(), # Separation line
            dbc.Row([dbc.Col(card) for card in cards]),
            html.Br(),
            #selectors[1],
            dbc.Row([dbc.Col(selector) for selector in labelselectors]),
            dbc.Col([dbc.Col(selector) for selector in otherselectors]),

            dbc.Row([dbc.Col(graph) for graph in graphs]),
            html.P(id='placeholder')
        ],
        fluid=False,
    )


    @app.callback(
        [Output("graph-cumul", "figure"),
        Output("graph-incidence", "figure"),
        Output('date-slider', 'marks'),
        Output('date-slider', 'max'),
        ],
        [Input("select-country", "value"),
        Input("select-type", "value"),
        Input("date-slider", "value"),
        Input("inc-type", "value")]
    )
    def update_figures(country_val, datatype_val, daterange, inctype_val):
        # 1 - load country file
        filepath = "workdata/incidence_"+country_val+"_Table.csv"
        #df = pd.read_csv(filepath)
        df = verify_priordata(country_val)

        print('range BEFORE refresh {}  {}'.format(0,df.shape[0]-1))
        # 2 - verification if up to date
        datetime_object = datetime.date.today()
        lastdfdate = df['Date'][df.shape[0]-1]
        lastdfdate = datetime.datetime.strptime(lastdfdate, '%Y-%m-%d').date()
        diffdate= datetime_object-lastdfdate
        if lastdfdate != datetime_object :
            print('lastdate in data : {} ({} days from today)'.format(lastdfdate,diffdate.days))
            #2-1 check if selected slide value include max before update
            print('selectedrange : {}/{};df size {}'.format(daterange[0],daterange[1],df.shape[0]-1))
            if daterange[1] == df.shape[0]-1 : updateslidemaxval_flag = True
            else : updateslidemaxval_flag = False
            #2.2 update incidence
            updateIncidenceTable(country_val)
            df = pd.read_csv(filepath)
            #2.3 replace slider max val if needed
            if updateslidemaxval_flag and daterange[1] != df.shape[0]-1 :
                daterange[1] = df.shape[0]-1

        # 3 - renew slide range to DF size
        print('range AFTER refresh {}  {}'.format(0,df.shape[0]-1))
        slidemax = df.shape[0]-1
        slidemarksdict = {i: '{}'.format(df['Date'][i]) for i in range(0,slidemax,slidemax//5)}
        
        # 4 - Filter dosplay based on chosen values
        # DATE RANGE
        xdf_filt = df.iloc[daterange[0]:daterange[1]]
        # DATA TYPES
        if 'brut' not in inctype_val :
            xdf_filt.drop([colname for colname in xdf_filt.columns if 'brut' in colname],
                axis=1,inplace=True)
        if 'MA' not in inctype_val :
            xdf_filt.drop([colname for colname in xdf_filt.columns if '_MM' in colname],
                axis=1,inplace=True)
        if 'EMA' not in inctype_val :
            xdf_filt.drop([colname for colname in xdf_filt.columns if '_eMM' in colname],
                axis=1,inplace=True)
        
        # 5 - draw graphe
        # cumulative graphe
        coef_fig = go.Figure(
            data=[go.Scatter(
                x=xdf_filt['Date'],
                y=xdf_filt[datatype_val],
                #color="condition",
                mode='lines')],
            layout=dict(
                title="Cumulative Graph"
                )
        )

        #incidence graphe
        incidencelist = [colname for colname in xdf_filt.columns if datatype_val in colname]
        incidencelist.pop(0) # first one is the cumul count
        coef_fig2 = go.Figure(
            data=[go.Scatter(x=xdf_filt['Date'],y=xdf_filt[col],name=col_map[col],mode='lines') 
                 for col in incidencelist],
            layout=dict(
                title="Incidence Graph",
                legend={
                "x": -0.0277108433735,
                "y": -0.142606516291,
                "orientation": "h",
                },   
            )
        )

        return coef_fig,coef_fig2,slidemarksdict,slidemax

    # @app.callback(
    #     Output("placeholder", "children"),
    #     Input('update_button', 'n_clicks'),
    #     #[dash.dependencies.State('input-box', 'value')]
    #     )
    # def update_output(n_clicks):
    #     if n_clicks > 0 :
    #         print("updatingdata from click callback : nclik = {}".format(n_clicks))
    #         update_alldata()
    #     return ''

    @app.callback(
        [Output("infected-rate", "children"),
        Output("mortality-rate", "children")],
        Input("select-country", "value"),
        #[dash.dependencies.State('input-box', 'value')]
        )
    def update_cards(country_val):
        #filepath = "workdata/incidence_"+country_val+"_Table.csv"
        #df = pd.read_csv(filepath)
        df = verify_priordata(country_val)
        # compute few data
        print('update cards')

        lastline = df.shape[0]-1
        mortalityrate = df['Deaths'][lastline]/df['Confirmed'][lastline]

        dfpop = pd.read_csv("workdata/population_2019.csv",index_col=0)
        contaminationrate = df['Confirmed'][lastline]/(float(dfpop['population'][country_val])*1000000)

        return f"{contaminationrate*100:.2f}%",f"{mortalityrate*100:.2f}%"
    # @app.callback(
    #     Output('date-slider', 'marks'),
    #     Input("select-country", "value"))
    # def set_daterange(selected_country):
    #     print('slide updated via callback')
    #     return {i: '{}'.format(df['Date'][i]) for i in range(0,df.shape[0]-1,(df.shape[0]-1)//5)}

# =========================================
# STARTING THE APP
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
appcontent(app)

if __name__ == "__main__":
    app.run_server(debug=True,host='0.0.0.0')