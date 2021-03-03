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



ids = ['708a6f60-5c93-406e-854f-50dd6734c0dd',
 '0a528e81-5bb0-4bf8-a7f9-6dbd183528ce',
 '737f9997-8817-4a74-9c13-88b99c37d118',
 '28eddc41-6a11-4ff8-8ec6-15041aa01e80',
 'c561f66b-5bd8-451c-8686-156073c3fb69',
 'a3a4f935-4d05-4166-b8c4-ce8e52eb3ca3',
 '7b797690-5b53-45a7-b972-bd2d5152654a',
 '12a8288a-addc-4e5c-8af7-b3ba6e5161d4',
 'a494c64e-9e93-418c-8934-f331ee47a39b',
 'feead270-621c-4cde-baac-2f6834e9e594',
 'd2378dc1-1168-410b-893d-e084170a402e',
 'a156f083-e902-49d3-a113-bd61702c336a',
 'd4712d31-9030-40de-b1a6-1fb9964348f3',
 '5f85e04f-798f-434c-89d4-2b0a575bd652',
 '252e83ac-b3a4-407e-82d2-138beb60b5b9',
 '9c8202c7-698b-4f44-b029-b70ddc49e9dc',
 'dd7c595c-5a1b-4f43-8493-db0a2bbcc5aa',
 '3a0ae6ce-f22e-4d98-b1fe-906f859df983',
 '4e166b27-3099-44c3-9de3-cac2b9751692',
 '18b2d80e-d38d-4678-9b7f-c2bfb223259e',
 '2dbc545a-25a5-4208-8e89-bbb6c3e3a364',
 '2ab08547-9f62-4ff4-aff9-1bdc0de8fa3e',
 '320cae53-d585-4e74-8a66-404fa3543c19',
 '814c5183-596f-41d7-9135-c6b29faa9c6d',
 'b73fe6f1-ae28-468b-a4b3-4adb68e7d6bc',
 '827f9328-03aa-4cb5-97cd-7b5f2c2386fd',
 '208ae30a-a4fe-42d4-9e51-e6fd1ad2a7a9',
 '33a4a3a3-a32c-4925-a4e8-7d24e56b105e',
 '54bc2e0d-91e9-4f4c-9361-a8d7eeefe91e',
 'ad8e85a4-2240-4604-95f6-be826966d988']


def base_set():
    moments = pd.DataFrame()
    for x in ids:
        query = """{
        getSet(input:{
        setID:"%s",
        
          }){
            set{
             
              flowName
              flowSeriesNumber
              plays{
                id
               
                
                stats{
                  playerName
                  playerID
                  jerseyNumber,
                  playCategory,
                  dateOfMoment
                  
                  
                }
              }
            }
          }
        }""" % x
        js = execute(query)
        base = pd.json_normalize(js['data']['getSet']['set']['plays'])
        base['date'] = pd.to_datetime(base['stats.dateOfMoment'])
        base['date'] = base['date'].apply(lambda x: pd.Timestamp(x - datetime.timedelta(hours=6)))
        base['date'] = [np.datetime_as_string(x, unit='D') for x in base.date.values]
        base['set name'] = js['data']['getSet']['set']['flowName']
        base['play'] = base['stats.playerName'] + " " + base['stats.playCategory'] + " " + base['date'] + " " + base['set name'] + ' (Series {})'.format(js['data']['getSet']['set']['flowSeriesNumber'])
        moments = moments.append(base)
    return moments






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
if __name__ == '__main__':
    app.run_server(debug=True)
