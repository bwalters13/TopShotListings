# -*- coding: utf-8 -*-
"""
Created on Sun Feb 28 11:56:53 2021

@author: blake
"""

import pandas as pd
import numpy as np
import plotly.express as px
import json
import requests
import plotly.graph_objects as go


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
    