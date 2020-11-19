#! python3
# portfolioAnalysis.py - Analyze a stock portfolio using
# up-to-date information from Yahoo Finance. Before running script, populate
# directory with csv with the following columns:
# 'Stock', 'Shares', 'Cost basis per share'

import pandas as pd
import yahoo_fin.stock_info as si

portfolio = pd.read_csv('portfolio.csv')

df = pd.DataFrame(portfolio)
df.set_index('Stock', inplace = True)

# Measurement for individual stocks.
buffer = 0.005
target_gain = 0.1

# Subtract 1 for cash position, additional for spec plays.
target_percentage = (1 / (df.shape[0] - 2)) + buffer

df['Cost basis total'] = df['Shares'] * df['Cost basis per share']

cost_basis = df['Cost basis total'].sum()

df['Latest price'] = df.index.map(lambda x: si.get_live_price(x) if x != 'Cash' else 1)
df['Position'] = df['Shares'] * df['Latest price']

df['Prev close'] = df.index.map(lambda x: si.get_quote_table(x)['Previous Close'] if x != 'Cash' else 1)
df['Prev position'] = df['Shares'] * df['Prev close']

prev_cost_basis = df['Prev position'].sum()

df["Today's $ gain/loss"] = df['Position'] - df['Prev position']
df["Today's % gain/loss"] = df["Today's $ gain/loss"] / df['Prev position']

df['Total $ gain/loss'] = df['Position'] - df['Cost basis total']
df['Total % gain/loss'] = df['Total $ gain/loss'] / df['Cost basis total']

portfolio_value = df['Position'].sum()

df['Portfolio %'] = df['Position'].apply(lambda x: x / portfolio_value)

today_d_gain = portfolio_value - prev_cost_basis
today_p_gain = today_d_gain / prev_cost_basis

total_d_gain = portfolio_value - cost_basis
total_p_gain = total_d_gain / cost_basis

# Gives indicator on whether to sell, to be alert, or to keep dreaming.
def is_target_percentage(series):
	
	if series > target_percentage:
		return True
		
	else:
		return False

def get_status(dataframe):
	
    is_portfolio_share = is_target_percentage(dataframe['Portfolio %'])

    if is_portfolio_share and dataframe['Total % gain/loss'] > target_gain:
        return 'X'
	
    elif is_portfolio_share:
        if dataframe['Total % gain/loss'] > 0:
            return '/'
        else:
            return 'o'
	
    else:
        return ''

df['Status'] = df.apply(get_status, axis=1)

# Formats number as dollar, percentage, etc, ready to print.
def as_dollar(n):
    return '${:,.2f}'.format(n)

def as_percentage(n):
    return '{:.2%}'.format(n)

print(df)
print('Portfolio value:\n\t%s' % as_dollar(portfolio_value))
print("Today's gain/loss value:\n\t%s\n\t\t%s" %
      (as_dollar(today_d_gain), as_percentage(today_p_gain)))

benchmark_spy = df.loc['SPY', "Today's % gain/loss"]

# Show portfolio daily weighted gain against benchmark daily gain, e.g. SPY.
print('Benchmark:\n\t%s %s' % ('SPY', as_percentage(benchmark_spy)))
print('Spread over benchmark:\n\t%s %s' %
      ('SPY', as_percentage(today_p_gain - benchmark_spy)))

# Print total gain/loss.
print('Total gain/loss:\n\t%s\n\t\t%s' %
      (as_dollar(total_d_gain), as_percentage(total_p_gain)))

# TO DO print top 5 gainers

# TO DO print bottom 5 gainers

# TO DO performance as time series

# Data to plot.
from datetime import datetime
import matplotlib.pyplot as plt

plt.style.use('ggplot')

fig, axs = plt.subplots(2, 1, figsize=(5, 10))

right_now = datetime.now()

# Cash assumed to be ultimate value in index.
axs[0].bar(df.index[:-1], df["Today's % gain/loss"][:-1])
axs[0].set_title('Portfolio performance as of %s.' % right_now.strftime('%H:%M:%S %d/%m/%Y'))
axs[0].set_xticklabels(df.index[:-1], rotation=90)
axs[0].set_ylabel("Today's % gain/loss")

vals = axs[0].get_yticks()
axs[0].set_yticklabels(['{:.1%}'.format(x) for x in vals])

# Show portfolio weighted average.
axs[0].plot([0, df.index[:-1].shape[0]], [today_p_gain, today_p_gain],
            '--', label='Your daily gain ' + str(as_percentage(today_p_gain)))

# Align SPY benchmark.
axs[0].plot([0, df.index[:-1].shape[0]], [benchmark_spy, benchmark_spy],
            'k--', label='SPY daily gain ' + str(as_percentage(benchmark_spy)))

axs[0].legend()

axs[1].pie(df['Portfolio %'], labels=df.index, autopct='%1.1f%%', pctdistance=0.8)
axs[1].set_title('Position as present share of portfolio.')

fig.tight_layout()

plt.show()

# TO DO groupby facts