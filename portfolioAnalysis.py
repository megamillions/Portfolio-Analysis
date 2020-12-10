#! python3
# portfolioAnalysis.py - Analyze a stock portfolio using
# up-to-date information from Yahoo Finance. Before running script, populate
# directory with csv with the following columns:
# 'Stock', 'Shares', 'Cost basis per share'

from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import yahoo_fin.stock_info as si

portfolio = pd.read_csv('portfolio.csv')

df = pd.DataFrame(portfolio)
df.set_index('Stock', inplace = True)

# Will save dataframe as csv or plot as png - adjust as needed.
write_csv = True
write_plot = True

# Measurements for individual stocks.
buffer = 0.005
target_gain = 0.1

# Subtract 1 for cash position.
target_percentage = (1 / (df.shape[0] - 1)) + buffer

df['Cost basis total'] = df['Shares'] * df['Cost basis per share']

cost_basis = df['Cost basis total'].sum()

df['Latest price'] = df.index.map(lambda x: si.get_live_price(x) if x != 'Cash' else 1)
df['Position'] = df['Shares'] * df['Latest price']

df['Prev close'] = df.index.map(lambda x: si.get_quote_table(x)['Previous Close'] if x != 'Cash' else 1)
df['Prev position'] = df['Shares'] * df['Prev close']

# Calculate each stock's daily and total changes.
df['Today $ gain/loss'] = df['Position'] - df['Prev position']
df['Today % gain/loss'] = df['Today $ gain/loss'] / df['Prev position']

df['Total $ gain/loss'] = df['Position'] - df['Cost basis total']
df['Total % gain/loss'] = df['Total $ gain/loss'] / df['Cost basis total']

# Calculate each stock's weight against the portfolio.
portfolio_value = df['Position'].sum()

df['Portfolio %'] = df['Position'].apply(lambda x: x / portfolio_value)

# Day over day percentage change.
low_deltas = []
high_deltas = []

for stock in df.index:
    
    if stock != 'Cash':
        
        # Get the stock's day range data.
        day_range = si.get_quote_table(stock)["Day's Range"].split(' - ')

        # Low range.
        low = float(day_range[0])
        low_delta = ((low * df['Shares'][stock]) - df['Prev position'][stock]) / df['Prev position'][stock]
        low_deltas.append(low_delta)
        
        # High range.
        high = float(day_range[1])
        high_delta = ((high * df['Shares'][stock]) - df['Prev position'][stock]) / df['Prev position'][stock]
        high_deltas.append(low_delta)
    
    # Cash will not be plotted.
    else:
        pass

deltas = [low_deltas, high_deltas]

# Gives indicator on whether to sell, to be alert, or to keep dreaming.
def get_status(dataframe):

    if dataframe['Portfolio %'] > target_percentage:
        
        if dataframe['Total % gain/loss'] > target_gain:
            return 'X'
        
        elif dataframe['Total % gain/loss'] > 0:
            return '/'
        
        else:
            return 'o'
        
    else:
        return ''

df['Status'] = df.apply(get_status, axis=1)

# Calculate a few metrics to read.
prev_cost_basis = df['Prev position'].sum()

today_d_gain = portfolio_value - prev_cost_basis
today_p_gain = today_d_gain / prev_cost_basis

total_d_gain = portfolio_value - cost_basis
total_p_gain = total_d_gain / cost_basis

def get_weighted_average(series):
    return (series * df['Shares']).sum() / df['Shares'].sum()

# Create a few summary rows.
df.loc['Weighted averages'] = {'Shares' : df['Shares'].mean(),
                 'Cost basis per share' : get_weighted_average(df['Cost basis per share']),
                 'Cost basis total' : get_weighted_average(df['Cost basis total']),
                 'Latest price' : get_weighted_average(df['Latest price']),
                 'Position' : get_weighted_average(df['Position']),
                 'Prev close' : get_weighted_average(df['Prev close']),
                 'Prev position' : get_weighted_average(df['Prev position']),
                 'Today $ gain/loss' : get_weighted_average(df['Today $ gain/loss']),
                 'Today % gain/loss' : get_weighted_average(df['Today $ gain/loss']),
                 'Today % range' : None,
                 'Total $ gain/loss' : get_weighted_average(df['Total $ gain/loss']),
                 'Total % gain/loss' : get_weighted_average(df['Total % gain/loss']),
                 'Portfolio %' : get_weighted_average(df['Portfolio %']),
                 'Status' : None}

# Remember to exclude the previous summary row.
df.loc['Totals'] = {'Shares' : df['Shares'][:-1].sum(),
                 'Cost basis per share' : None,
                 'Cost basis total' : df['Cost basis total'][:-1].sum(),
                 'Latest price' : None,
                 'Position' : portfolio_value,
                 'Prev close' : None,
                 'Prev position' : prev_cost_basis,
                 'Today $ gain/loss' : today_d_gain,
                 'Today % gain/loss' : today_p_gain,
                 'Today % range' : None,
                 'Total $ gain/loss' : total_d_gain,
                 'Total % gain/loss' : total_p_gain,
                 'Portfolio %' : df['Portfolio %'][:-1].sum(),
                 'Status' : None}

right_now = datetime.now()

# Save today's portfolio as a csv.
if write_csv:
    df.to_csv('Performance %s.csv' % right_now.strftime('%d-%m-%Y'))

# Formats number as dollar, percentage, etc, ready to print.
def as_dollar(n):
    return '${:,.2f}'.format(n)

def as_percentage(n):
    return '{:.2%}'.format(n)

print(df[['Latest price', 'Total % gain/loss', 'Portfolio %', 'Status']])
print('Portfolio value:\n\t%s' % as_dollar(portfolio_value))
print("Today's gain/loss value:\n\t%s\n\t\t%s" %
      (as_dollar(today_d_gain), as_percentage(today_p_gain)))

benchmark_spy = df.loc['SPY', "Today % gain/loss"]

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
plt.style.use('ggplot')

fig, axs = plt.subplots(2, 1, figsize=(5, 10))

# Cash, summary average, and summary total assumed to be ultimate values in index.
axs[0].bar(df.index[:-3], df["Today % gain/loss"][:-3], yerr=deltas)
axs[0].set_title('Portfolio performance as of %s.' % right_now.strftime('%H:%M:%S %d/%m/%Y'))
axs[0].set_xticklabels(df.index[:-3], rotation=90)
axs[0].set_ylabel("Today's gain/loss")

# Clean up the axis labels.
vals = axs[0].get_yticks()
axs[0].set_yticklabels(['{:.1%}'.format(x) for x in vals])

# Show portfolio weighted average.
benchmark_spy = df.loc['SPY', "Today % gain/loss"]
today_p_gain = df.loc['Totals', 'Today % gain/loss']

axs[0].plot([0, df.index[:-3].shape[0]], [today_p_gain, today_p_gain],
            'r--', label='Your daily gain ' + str(as_percentage(today_p_gain)))

# Align SPY benchmark.
axs[0].plot([0, df.index[:-3].shape[0]], [benchmark_spy, benchmark_spy],
            'k--', label='SPY daily gain ' + str(as_percentage(benchmark_spy)))

axs[0].legend()

# TO DO sort by order of %
axs[1].pie(df['Portfolio %'][:-2], labels=df.index[:-2], autopct='%1.1f%%', pctdistance=0.8)
axs[1].set_title('Position as present share of portfolio.')

fig.tight_layout()

# TO DO groupby facts, like industry

if write_plot:
    plt.savefig('Performance %s.png' % right_now.strftime('%d-%m-%Y'))
    
else:
    plt.show()