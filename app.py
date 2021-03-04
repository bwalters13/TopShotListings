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







def execute(query, url='https://api.nba.dapperlabs.com/marketplace/graphql'):    
    r = requests.post(url, json={'query':query})
    js = json.loads(r.text)
    return js

def get_listings(pid):    
    query = """{
      searchMintedMoments(input: {filters: {byForSale: FOR_SALE, byPlays: "%s"}, sortBy: PRICE_USD_ASC, searchInput: {pagination: {cursor: "", direction: RIGHT, limit: 1000}}}) {
        data {
          searchSummary {
            data {
              size
              ... on MintedMoments {
                data {
                  id
                  price
                  flowId
                  flowSerialNumber
                  owner {
                    dapperID
                  }
                  play {
                    stats {
                      playerName
                      jerseyNumber
                    }
                  }
                  setPlay {
                    setID
                    playID
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
    moment = js['data']['searchMintedMoments']['data']['searchSummary']['data']['data']
    data = [[mo['play']['stats']['playerName'], mo['price'], mo['flowSerialNumber']] for mo in moment]
    df = pd.DataFrame(data, columns=['name', 'price', 'serial'])
    df['serial'] = df['serial'].astype(int) 
    df['price'] = df['price'].apply(lambda x: int(x.split('.')[0]))
    df['jersey'] = int(jersey_num(pid))
    df['jersey_serial'] = 0
    if df['jersey'].values[0] in df.serial:
        df.loc[df.serial == df['jersey'].values[0], 'jersey_serial'] = 1
    return df

def plot_listings(df, min_price, max_price, min_serial, max_serial, log_x=False):
    df = df.loc[(df.serial.between(min_serial, max_serial, inclusive=True)) & (df.price.between(min_price, max_price, inclusive=True))]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
    x=df['price'], y=df['serial'],
    mode='markers',
    marker_color='#E03A3E',
    hovertemplate = 
    '<b>Price</b>: $%{x}' +
    '<br><b>Serial</b> %{y}<br>'
    ))
    fig.update_layout(
        plot_bgcolor='#000000',
        paper_bgcolor='#C4ced4'
    )
    if not df[df.jersey_serial == 1].empty:
        fig.add_trace(go.Scatter(
        x=df[df.jersey_serial == 1].price,
        y=df[df.jersey_serial == 1].serial,
        mode='markers',
        marker_symbol='star',
        marker_size=10,
        marker_color='#00ff00'
        ))
    
    fig.update_xaxes(showgrid=True, gridcolor='#E9F0DB', color='#E03A3E', title={'text': '<b>Price</b>'})
    fig.update_yaxes(showgrid=False, gridcolor='#E9F0DB', color='#E03A3E', title={'text': '<b>Serial</b>'})
    fig.update_xaxes(showline=True, linewidth=2, linecolor='#0077c0', mirror=True, nticks=10)
    fig.update_yaxes(showline=True, linewidth=2, linecolor='#0077c0', mirror=True)
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

app = dash.Dash()
server = app.server
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
if __name__ == '__main__':
    app.run_server(debug=True)
