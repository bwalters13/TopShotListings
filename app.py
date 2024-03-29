# -*- coding: utf-8 -*-
"""
Created on Sun Feb 28 11:56:21 2021

@author: blake
"""

import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
import numpy as np
import json
import requests
import datetime
import plotly.express as px
import math
from dash.exceptions import PreventUpdate

#from scipy import interpolate

def round_up(n, decimals=0):
    multiplier = 10 ** decimals
    return int(math.ceil(n * multiplier) / multiplier)







def execute(query, url='https://api.nba.dapperlabs.com/marketplace/graphql'):    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0',
        'From': 'blakewalterss@gmail.com'  # This is another valid field
    }
    print(headers)
    r = requests.post(url, json={'query':query}, headers=headers)
    js = json.loads(r.text)
    return js

def get_listings(pid, sid):
    query = """{
      getUserMomentListings(input:{playID: "%s", setID: "%s"}){
        data{
          play{
              stats{playerName, jerseyNumber}
          }
          momentListings{
            price
            moment{
              flowSerialNumber
            }
          }
        }
      }
    }""" % (pid, sid)
    js = execute(query)
    k = pd.json_normalize(js, record_path=['data', 'getUserMomentListings', 'data', 'momentListings'])
    k.columns = ['price', 'serial']
    k['serial'] = k['serial'].astype(int)
    k['name'] = js['data']['getUserMomentListings']['data']['play']['stats']['playerName']
    k['price'] = k['price'].apply(lambda x: int(x.split('.')[0]))
    k['jersey'] = js['data']['getUserMomentListings']['data']['play']['stats']['jerseyNumber'] 
    k['jersey_serial'] = 0
    if k['jersey'].values[0] in k.serial:
        k.loc[k.serial == k['jersey'].values[0], 'jersey_serial'] = 1
    return k


def plot_listings(df, pid, sid, log_x=False):
    
    play_name = base.loc[(base['id'] == pid) & (base['set id'] == sid)]['play'].values[0]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
    x=df['price'], y=df['serial'],
    mode='markers',
    marker_color='#E03A3E',
    hovertemplate = 
    '<b>Price</b>: $%{x}' +
    '<br><b>Serial</b> %{y}<br>'
    ))
    # filtered_df = filter_listings(df)
    # f = interpolate.interp1d(filtered_df['price'], filtered_df['serial'])
    # fig.add_trace(go.Scatter(x=filtered_df['price'], 
    #                          y=f(filtered_df['price']), 
    #                          mode='lines',
    #                          line=dict(color='lightsalmon')
                             
    #                          ),
                             
    #               )
    fig.update_layout(
        plot_bgcolor='#323130',
        paper_bgcolor='#323130'
    )
    if not df[df.jersey_serial == 1].empty:
        fig.add_trace(go.Scatter(
        x=df[df.jersey_serial == 1].price,
        y=df[df.jersey_serial == 1].serial,
        mode='markers',
        marker_symbol='star',
        marker_size=10,
        marker_color='#00ff00',
        name='Jersey Number Serial'
        ))
    if not df.empty:
        fig.update_layout(
        font=dict(color='Orange'),
        title='Listings for {}'.format(play_name)
        )
    else:
        fig = go.Figure()
        fig.update_layout(
            title='No Listings for {}'.format(play_name)
        )
        return fig
    fig.update_xaxes(showgrid=True, gridcolor='#E9F0DB', color='#E03A3E', title={'text': '<b>Price</b>'})
    fig.update_yaxes(showgrid=False, gridcolor='#E9F0DB', color='#E03A3E', title={'text': '<b>Serial</b>'})
    fig.update_xaxes(showline=True, linewidth=2, linecolor='#000000', mirror=True, nticks=10)
    fig.update_yaxes(showline=True, linewidth=2, linecolor='#000000', mirror=True)
    if log_x:
        fig.update_xaxes(type='log', showgrid=False)
    
    return fig

def filter_listings(df):
    drop = []
    jersey_df = df[df.jersey_serial == 1]
    df = df.sort_values('price')
    df = df.groupby('price').min().reset_index()
    for x in df.index:
        for y in df.index[x:]:
            if df.loc[y, 'serial'] > df.loc[x, 'serial']:
                drop.append(y)
    df = df.append(jersey_df)
    return df[~df.index.isin(drop)]

def jersey_num(pid):
    query = """{
      searchMintedMoments(input: {filters: {byForSale: FOR_SALE, byPlays: "%s"}, sortBy: PRICE_USD_ASC, searchInput: {pagination: {cursor: "", direction: RIGHT, limit: 1000}}}) {
        data {
          searchSummary {
            data {
              size
              ... on MintedMoments {
                data {
                  
                  play {
                    stats {
                      jerseyNumber
                    }
                  }
                  
                }
              }
            }
          }
        }
      }
    }
    """ % pid
    js = execute(query)
    return js['data']['searchMintedMoments']['data']['searchSummary']['data']['data'][0]['play']['stats']['jerseyNumber']


base = pd.read_csv('https://raw.githubusercontent.com/bwalters13/TopShotListings/main/moment_data.csv')

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}]
)
app.title = 'Top Shot Listings'
server = app.server
app.layout = html.Div(children=[
    html.Div(
            className="row",
            style={'fontColor':'white'},
            children=[
                # Column for user controls
                html.Div(
                    className="four columns div-user-controls",
                    children=[
                        html.Img(
                            className="logo", src=app.get_asset_url("dash-logo-new.png")
                        ),
                        html.H2("TOPSHOT LISTINGS APP"),
                        html.P(
                            """Select a moment or type in a query below"""
                        ),
                        html.Div(
                                className="div-for-dropdown",
                                style={'fontColor':'white'},
                                children=[
                                    dcc.Store(id='player-df'),
                                    dcc.Dropdown(
                                        id='moment-drop',
                                        style={'color':'white'},
                                        options=[
                                            {'label': y['play'], 'value': y['id']+ ',' + y['set id']}
                                            for _, y in base.iterrows()
                                        ],
                                        value="03acc4a7-9301-46a2-8fb9-75affab7ee59" +  ",ad8e85a4-2240-4604-95f6-be826966d988",
                                        optionHeight=80
                                        
                                    )
                                ],
                        ),
                    html.Div(
                       className='row',
                       children=[
                           html.Div(
                               className="div-for-dropdown",
                               children=[
                                   html.Label('Select a Serial Range',
                                              style={'font-weight': 'bold', 'padding': '2px', 'font-size': '20px'}),
                                   html.Div(
                                       style={'width': '175%', 'float': 'left', 'marginRight': 2, 'marginLeft': 2, "display": "grid", "grid-template-columns": "10% 40% 10%"},
                                       children=[
                                           
                                           dcc.Input(id='serial-min-value', size='10',type='number', placeholder='Min'), 
                                           dcc.RangeSlider(
                                                id='serial-slider',
                                                min=0,
                                                step=50,
                                                value=[0,35000],
                                            
                                            ),
                                           dcc.Input(id='serial-max-value', size='10', type='number', placeholder='Max')
                                       ]
                                   ),
                                   # html.Div(
                                   #     style={'width': '10%', 'float': 'right', 'marginRight': 2, 'marginLeft': 2, 'display': 'inline-block'},
                                   #     children=[
                                   #         dcc.Input(id='slider-max-value', size='1')
                                   #     ]
                                   # ),
                                   html.Div([
                                       # dcc.RangeSlider(
                                       #      id='serial-slider',
                                       #      min=0,
                                       #      max=15000,
                                       #      step=50,
                                       #      marks={x:str(x)
                                       #             for x in range(0, 15000, 3000)},
                                       #      value=[0,15000],
                                            
                                       #  ),
                                ]
                                ),
                                   
                            ]
                            ),
                           html.Div(id='serial-output'),
                           html.Div(
                               className="div-for-dropdown",
                               children=[
                                   html.Label('Select a Price Range',
                                              style={'font-weight': 'bold', 'padding': '2px', 'font-size': '20px'}),
                                   html.Div(
                                       style={'width': '175%', 'float': 'left', 'marginRight': 2, 'marginLeft': 2, "display": "grid", "grid-template-columns": "10% 40% 10%"},
                                       children=[
                                           dcc.Input(id='price-min-value', size='10',type='number', placeholder='Min'), 
                                           dcc.RangeSlider(
                                                id='price-slider',
                                                min=0,
                                                max=50000,
                                                step=50,
                                                marks={x:str(x)
                                                       for x in range(0, 50001, 10000)},
                                                value=[0,1000000]
                                            
                                            ),
                                           dcc.Input(id='price-max-value', size='10', type='number', placeholder='Max')
                                       ]
                                   ),
                               ]
                            ),
                           html.Div(id='price-output'),
                           html.P(id='total-listings'),
                         ]
                    )
                ]
            ),
                
    html.Div(
        className="eight columns div-for-charts bg-grey",
        children=[
            dcc.Graph(id='player-graph'),
            dcc.Checklist(
                id='filter',
                options=[
                    {'label': 'Filter Listings', 'value': 'filter'},
                    {'label': 'Log Scale', 'value': 'log'}
                ],
                value=[]
            ),
    # html.Label('Moment Selection'),
    # html.Div(),
    # dcc.Dropdown(
    #     id='moment-drop',
    #     options=[
    #         {'label': y['play'], 'value': y['id']}
    #         for _, y in base.iterrows()
    #     ],
    #     value="03acc4a7-9301-46a2-8fb9-75affab7ee59"
        
    # ),
            html.Label('Lowest Ask w/ Lowest Serial'),
            html.Div(id='lowest ask',
                     style={'font_color':'red'}),
            dcc.Graph(id='histogram')

        ]
    # html.Label('Serial Range'),
    # dcc.RangeSlider(
    #     id='serial-slider',
    #     min=0,
    #     max=15000,
    #     step=50,
    #     marks={x:str(x)
    #            for x in range(1000, 15000, 1000)},
    #     value=[0,15000],
        
    # ),
    # html.Div(id='serial-output'),
    # html.Label('Price Range'),
    # dcc.RangeSlider(
    #     id='price-slider',
    #     min=0,
    #     max=250000,
    #     step=50,
    #     marks={x:str(x)
    #            for x in range(0, 250000, 10000)},
    #     value=[0, 10000],
        
    # ),
    
    # html.Div(id='price-output')
     )  
     ]
    )
    ]
)

# @app.callback(
#     Output("price-slider", "value"),
#     [Input("price-min-value", "value"), Input("price-max-value", "value")]
# )
# def custom_slider(minimum, maximum, vals):
#     print(vals)
#     if minimum >= 0 and maximum:
#         return [int(minimum), int(maximum)]
#     else:
#         return [0,15000]


# @app.callback(
#     Output("serial-slider", "value"),
#     [Input("slider-min-value", "value"), Input("slider-max-value", "value")]
# )
# def custom_prange(minimum, maximum):
#     if minimum >= 0 and maximum:
#         return [int(minimum), int(maximum)]
#     else:
#         return [0,15000]

@app.callback(Output("player-df", "data"),
              Input("moment-drop", "value")
)
def get_df(moment):
    if not moment:
        raise PreventUpdate
    df = get_listings(*moment.split(','))
    return df.to_dict('records')


@app.callback(
    Output("serial-slider", "max"),
    Output("serial-slider", "marks"),
    Input("moment-drop", "value")
)
def get_serial_max(moment):
    moment = moment.split(',')
    cc = base[(base['id'] == moment[0]) & (base['set id'] == moment[1])]['circ_count'].values[0]
    if cc == 0:
        raise PreventUpdate
    marks = {x: str(x) for x in range(0,cc, cc//5)}
    return cc, marks

@app.callback(
    Output("price-min-value", "value"),
    Output("price-max-value", "value"),
    Output("price-slider", "value"),
    Input("price-min-value", "value"),
    Input("price-max-value", "value"),
    Input("price-slider", "value"),
)
def callback_price(input_value_min, input_value_max, slider_values):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "price-max-value":
        value = input_value_max
        return slider_values[0], value, [slider_values[0], value]
    elif trigger_id == "price-min-value":
        value = input_value_min
        return value, slider_values[1], [value, slider_values[1]]
    else:
        value = slider_values
        return slider_values[0], slider_values[1], slider_values
    
@app.callback(
    Output("serial-min-value", "value"),
    Output("serial-max-value", "value"),
    Output("serial-slider", "value"),
    Input("serial-min-value", "value"),
    Input("serial-max-value", "value"),
    Input("serial-slider", "value"),
    Input("moment-drop", "value")
)
def callback_serial(input_value_min, input_value_max, slider_values, moment):
    ctx = dash.callback_context
    moment = moment.split(',')
    cc = base[(base['id'] == moment[0]) & (base['set id'] == moment[1])]['circ_count'].values[0]
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "serial-max-value":
        value = input_value_max
        return slider_values[0], value, [slider_values[0], value]
    elif trigger_id == "serial-min-value":
        value = input_value_min
        return value, slider_values[1], [value, slider_values[1]]
    elif trigger_id == 'moment-drop':
        return slider_values[0], cc, [slider_values[0], cc]
    else:
        value = slider_values
        return slider_values[0], slider_values[1], slider_values
    


    

@app.callback(
    Output("histogram", "figure"),
    Input("player-df", "data")
)

def get_histogram(selected_moment):
    if not selected_moment:
        raise PreventUpdate
    df = pd.DataFrame(selected_moment)
    fig = px.violin(df, x='price')
    fig.update_layout(plot_bgcolor="black", paper_bgcolor='black',
                      font=dict(color='white'))
    return fig

@app.callback(
    Output('total-listings','children'),
    Output('player-graph', 'figure'),
    Output('lowest ask', 'children'),
    Output('serial-output', 'children'),
    Output('price-output', 'children'),
    Input('player-df', 'data'),
    Input('moment-drop', 'value'),
    Input('serial-slider', 'value'),
    Input('price-slider', 'value'),
    Input('filter', 'value')
    
)

def update_figure(listings, selected_player, serial_range, price_range, filter_deals):
    if not len(listings):
        raise PreventUpdate
    df = pd.DataFrame(listings) 
    selected_player = selected_player.split(',')
    df = df.loc[(df.serial.between(*serial_range, inclusive='both')) & (df.price.between(*price_range, inclusive='both'))]
    if 'filter' in filter_deals:
        df = filter_listings(df)
    if 'log' in filter_deals:
         fig = plot_listings(df, *selected_player, True)
    elif listings:
        fig = plot_listings(df, *selected_player)
    low = df.loc[df.price == df.price.min(), ['price', 'serial']]
    low_ask = "Price: {}, Serial: {}".format(low.price.min(), low.serial.min())
    prange = 'You have selected ${}-${}'.format(*price_range)
    srange = 'You have selected {}-{}'.format(*serial_range)
    len_list = "Total Listings Shown: {}".format(len(df))
    return len_list, fig, low_ask, srange, prange
if __name__ == '__main__':
    app.run_server(debug=True)
