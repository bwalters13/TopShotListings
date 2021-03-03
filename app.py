# -*- coding: utf-8 -*-
"""
Created on Sun Feb 28 11:56:21 2021

@author: blake
"""
from plotting_func import plot_listings, get_listings, filter_listings
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from getSet import base_set



base = base_set()

app = dash.Dash()
app.layout = html.Div([
    dcc.Graph(id='player-graph'),
    dcc.Checklist(
        id='filter',
        options=[
            {'label': 'Filter Listings', 'value': 'filter'},
            {'label': 'Log Scale', 'value': 'log'}
        ],
        value=[]
    ),
    html.Label('Moment Selection'),
    html.Div(),
    dcc.Dropdown(
        id='moment-drop',
        options=[
            {'label': y['play'], 'value': y['id']}
            for _, y in base.iterrows()
        ],
        value="03acc4a7-9301-46a2-8fb9-75affab7ee59"
        
    ),
    html.Label('Lowest Ask w/ Lowest Serial'),
    html.Div(id='lowest ask'),
    
    html.Label('Serial Range'),
    dcc.RangeSlider(
        id='serial-slider',
        min=0,
        max=15000,
        step=50,
        marks={x:str(x)
               for x in range(1000, 15000, 1000)},
        value=[0,15000],
        
    ),
    html.Div(id='serial-output'),
    html.Label('Price Range'),
    dcc.RangeSlider(
        id='price-slider',
        min=0,
        max=250000,
        step=50,
        marks={x:str(x)
               for x in range(0, 250000, 10000)},
        value=[0, 10000],
        
    ),
    
    html.Div(id='price-output')
    
])



@app.callback(
    Output('player-graph', 'figure'),
    Output('lowest ask', 'children'),
    Output('serial-output', 'children'),
    Output('price-output', 'children'),
    Input('moment-drop', 'value'),
    Input('serial-slider', 'value'),
    Input('price-slider', 'value'),
    Input('filter', 'value')
    
)

def update_figure(selected_player, serial_range, price_range, filter_deals):
    df = get_listings(selected_player)
    if 'filter' in filter_deals:
        df = filter_listings(df)
    if 'log' in filter_deals:
         fig = plot_listings(df, *price_range, *serial_range, True)
    else:
        fig = plot_listings(df, *price_range, *serial_range)
    low = df.loc[df.price == df.price.min(), ['price', 'serial']]
    low_ask = "Price: {}, Serial: {}".format(low.price.min(), low.serial.min())
    prange = 'You have selected {}-{}'.format(*price_range)
    srange = 'You have selected {}-{}'.format(*serial_range)
    return fig, low_ask, srange, prange
app.run_server(debug=False, use_reloader=False)  # Turn off reloader if inside Jupyter
