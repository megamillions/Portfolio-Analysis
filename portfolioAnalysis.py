#! python3
# portfolioAnalysis.py - Analyze a stock portfolio using up-to-date information
# from Yahoo Finance. Before running script, populate directory with csv with
# the following columns: 'Stock', 'Shares', 'Cost basis per share'

import numpy as np
import pandas as pd
import yahoo_fin.stock_info as si

portfolio = pd.read_csv('portfolio.csv')

df = pd.DataFrame(portfolio)
df.set_index('Stock', inplace = True)

# Measurement for individual stocks.
buffer = 0.005
target_gain = 0.1

# Subtract 1 for cash position.
target_percentage = (1 / (df.shape[0] - 1)) + buffer

df['Cost basis total'] = df['Shares'] * df['Cost basis per share']

df['Latest price'] = df.index.map(lambda x: si.get_live_price(x) if x != 'Cash' else 1)
df['Position'] = df['Shares'] * df['Latest price']

df['Total $ gain/loss'] = df['Position'] - df['Cost basis total']
df['Total % gain/loss'] = df['Total $ gain/loss'] / df['Cost basis total']

portfolio_value = df['Position'].sum()

df['Portfolio %'] = df['Position'].apply(lambda x: x / portfolio_value)

def is_target_percentage(series):
	
	if series > target_percentage:
		return True
		
	else:
		return False

def get_status(dataframe):
	
	if is_target_percentage(dataframe['Portfolio %']) and dataframe['Total % gain/loss'] > target_gain:
		return 'X'
	
	elif is_target_percentage(dataframe['Portfolio %']):
		if dataframe['Total % gain/loss'] > 0:
			return '/'
		else:
			return 'o'
	
	else:
		return ''

df['Status'] = df.apply(get_status, axis=1)

print(df)
print('Portfolio value: %s\t\t\t\tIndividual stock target percentage of portfolio: %s' %
	(portfolio_value, target_percentage))