#! python3
# basketPriceRecommendations.py - Suggest the amount of a stock to buy or sell,
# based on preset units within a basket.

import numpy as np
import os
import pandas as pd
import yfinance as yf

file_path = '.\\Reference\\%s'
file_name = 'stocks.csv'

# Dollar amount of single unit.
ira_unit = 40
invest_unit = ira_unit * 0.5

ira_sell_unit = ira_unit * 0.5
invest_sell_unit = invest_unit * 0.5

df = pd.read_csv(os.path.abspath(file_path %
                                 file_name)).sort_values(by = 'TICKER')

def print_recommendations(df, recommendation, account,
                          account_action, shares_recommendation):
    
    print('\n%s the following for the %s account:\n' % (recommendation,
                                                        account))
    
    for n in range(len(df)):
        row = df.loc[n, :]
        
        if not np.isnan(row[account_action]):
            print('%s:' % (row['TICKER']),
                  '{:.3f}'.format(row[shares_recommendation]), 'shares at',
                  '${:.2f}.'.format(row['PRICE']))

    return

def recommend_amount(row):

    # Get the closing price.
    price = yf.Ticker(row['TICKER']).history().iloc[-1]['Close']
    
    invest_buy_share = shares_amount(invest_unit, row['INVEST_BUY'], price)
    ira_buy_share = shares_amount(ira_unit, row['IRA_BUY'], price)
    
    invest_sell_share = shares_amount(invest_sell_unit, row['INVEST_SELL'], price)
    ira_sell_share = shares_amount(ira_sell_unit, row['IRA_SELL'], price)
        
    return {'TICKER' : row['TICKER'],
            'PRICE' : price,
            'INVEST_BUY_SHARES' : invest_buy_share,
            'IRA_BUY_SHARES' : ira_buy_share,
            'INVEST_SELL_SHARES' : invest_sell_share,
            'IRA_SELL_SHARES' : ira_sell_share}

# Returns the amount of shares to buy or sell.
def shares_amount(units, basket_size, price):
    return units / basket_size / price if basket_size is not np.nan else basket_size

df = pd.merge(df, pd.DataFrame(list(df.apply(recommend_amount, axis = 1))),
              on = 'TICKER')

print_recommendations(df, 'BUY', 'INVESTMENT',
                      'INVEST_BUY', 'INVEST_BUY_SHARES')

print_recommendations(df, 'BUY', 'IRA',
                      'IRA_BUY', 'IRA_BUY_SHARES')

print_recommendations(df, 'SELL', 'INVESTMENT',
                      'INVEST_SELL', 'INVEST_SELL_SHARES')

print_recommendations(df, 'SELL', 'IRA',
                      'IRA_SELL', 'IRA_SELL_SHARES')

