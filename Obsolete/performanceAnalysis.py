#! python3
# performanceAnalysis.py - Analyze a stock's performance in a portfolio using
# up-to-date information from Yahoo Finance. Before running script, populate
# directory with csv with the following columns:
# 'Stock', 'Shares', 'Cost basis per share'

# TO DO investigate whether can use gridspect for plotting
#from matplotlib import gridspec

# TO DO calculate weighted average dividend return

import datetime
import matplotlib.pyplot as plt
import pandas as pd
import yahoo_fin.stock_info as si

# Will save dataframe as csv or plot as png - adjust as needed.
write_output = False

# Measurements for individual stocks.
buffer = 0.005
target_gain = 0.1

# Formats number as dollar, percentage, etc, ready to print.
def as_dollar(n):
    return '${:,.2f}'.format(n)

def as_percentage(n):
    return '{:.2%}'.format(n)

def get_weighted_average(dataframe, series):
    return (series * dataframe['Shares']).sum() / dataframe['Shares'].sum()

def generate_df(filename):
    
    portfolio = pd.read_csv(filename)
    
    df = pd.DataFrame(portfolio)
    df.set_index('Stock', inplace = True)
    
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

    # Calculate a few metrics to read.
    prev_cost_basis = df['Prev position'].sum()
    
    today_d_gain = portfolio_value - prev_cost_basis
    today_p_gain = today_d_gain / prev_cost_basis
    
    total_d_gain = portfolio_value - cost_basis
    total_p_gain = total_d_gain / cost_basis

    # Create a few summary rows.
    df.loc['Weighted averages'] = {'Shares' : df['Shares'].mean(),
                     'Cost basis per share' :
                         get_weighted_average(df, df['Cost basis per share']),
                     'Cost basis total' :
                         get_weighted_average(df, df['Cost basis total']),
                     'Latest price' :
                         get_weighted_average(df, df['Latest price']),
                     'Position' :
                         get_weighted_average(df, df['Position']),
                     'Prev close' :
                         get_weighted_average(df, df['Prev close']),
                     'Prev position' :
                         get_weighted_average(df, df['Prev position']),
                     'Today $ gain/loss' :
                         get_weighted_average(df, df['Today $ gain/loss']),
                     'Today % gain/loss' :
                         get_weighted_average(df, df['Today $ gain/loss']),
                     'Today % range' : None,
                     'Total $ gain/loss' :
                         get_weighted_average(df, df['Total $ gain/loss']),
                     'Total % gain/loss' :
                         get_weighted_average(df, df['Total % gain/loss']),
                     'Portfolio %' :
                         get_weighted_average(df, df['Portfolio %'])}
    
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
                     'Portfolio %' : df['Portfolio %'][:-1].sum()}
    
    return df

invest_df = generate_df('investPortfolio.csv')
ira_df = generate_df('iraPortfolio.csv')

right_now = datetime.datetime.now()

# TO DO performance from cost-basis to present day
# TO DO performance as time series 3-month w/ 7-day average

# Data to plot.
plt.style.use('ggplot')

fig, axs = plt.subplots(2, 2, figsize=(12, 8))

def plot_charts(df, description, column):
    
    # Cash, summary average, and summary total assumed to be
    # the ultimate values in index.
    bar_data = df[:-3].copy()

    # Sort by order of % to align with pie chart later.
    bar_data.sort_values(by=['Portfolio %'], ascending=False, inplace=True)

    # Day over day percentage change.
    low_errors = []
    high_errors = []
    
    for stock in bar_data.index:
        
        # Get the stock's day range data.
        stock_table = si.get_quote_table(stock)
        day_range = stock_table["Day's Range"].split(' - ')
        prev_close = stock_table['Previous Close']
    
        # Low range.
        low = float(day_range[0])
        low_delta = (low - prev_close) / prev_close
        low_error = df['Today % gain/loss'][stock] - low_delta
    
        low_errors.append(low_error)
        
        # High range.
        high = float(day_range[1])
        high_delta = (high - prev_close) / prev_close
        high_error = high_delta - df['Today % gain/loss'][stock]
    
        high_errors.append(high_error)
    
    deltas = [low_errors, high_errors]

    # Create list of colors to map to chart whether bar is positive.
    color_map = []
    
    for stock in bar_data.index:
        
        if bar_data['Today % gain/loss'][stock] > 0:
            color_map.append('xkcd:kelly green')
            
        else:
            color_map.append('xkcd:coral')

    axs[0][column].bar(bar_data.index, bar_data['Today % gain/loss'],
                       color=color_map, yerr=deltas)
    axs[0][column].set_title('%s portfolio performance as of %s.' %
                             (description,
                              right_now.strftime('%Y/%m/%d %H:%M:%S')))
    axs[0][column].set_xticklabels(bar_data.index, rotation=90)
    axs[0][column].set_ylabel("Today's gain/loss")
    
    # Clean up the axis labels.
    vals = axs[0][column].get_yticks()
    axs[0][column].set_yticklabels(['{:.1%}'.format(x) for x in vals])
    
    # Show portfolio weighted average.
    benchmark_spy = df.loc['SPY', 'Today % gain/loss']
    today_p_gain = df.loc['Totals', 'Today % gain/loss']
    
    axs[0][column].plot([0, bar_data.index.shape[0]],
                        [today_p_gain, today_p_gain], 'r--',
                        label='Your daily gain ' + str(
                            as_percentage(today_p_gain)))
    
    # Align SPY benchmark.
    axs[0][column].plot([0, bar_data.index.shape[0]],
                        [benchmark_spy, benchmark_spy], 'k--',
                        label='SPY daily gain ' + str(
                            as_percentage(benchmark_spy)))
    
    axs[0][column].legend()
    
    # Sort by order of %.
    pie_data = df[:-2].copy()
    pie_data.sort_values(by=['Portfolio %'], inplace=True)
    
    # Explode the positions that satisfy the benchmark holdings.
    explosions = []
    
    # Less 1 for cash.
    target_percentage = (1 / (pie_data.shape[0] - 1)) + buffer
    
    for stock in pie_data.index:
        if (pie_data['Total % gain/loss'][stock] > target_gain and
            pie_data['Portfolio %'][stock] > target_percentage):
            explosions.append(0.2)
            
        else:
            explosions.append(0)
    
    # Plot pie chart.
    axs[1][column].pie(pie_data['Portfolio %'], labels=pie_data.index,
                       autopct='%1.1f%%', explode=explosions,
                       pctdistance=0.8, shadow=True, startangle=90)
    
    axs[1][column].set_title('Position as present share of %s portfolio.' %
                             description)

plot_charts(invest_df, 'Invest', 0)
plot_charts(ira_df, 'IRA', 1)

plt.tight_layout()

'''
# Annotate with some delicious factoids.
def add_annotation(annotation, y_placement):
   plt.annotate(annotation, (0.725, y_placement), xycoords='figure fraction')

today_d_gain = ira_df.loc['Totals', 'Today $ gain/loss']
today_p_gain = ira_df.loc['Totals', 'Today % gain/loss']
total_d_gain = ira_df.loc['Totals', 'Total $ gain/loss']
total_p_gain = ira_df.loc['Totals', 'Total % gain/loss']

add_annotation('Portfolio value: %s' %
               as_dollar(ira_df.loc['Totals', 'Position']), 0.95)
add_annotation("Today's gain/loss value:\n%s    %s" %
               (as_dollar(today_d_gain), as_percentage(today_p_gain)), 0.9)

benchmark_spy = ira_df.loc['SPY', "Today % gain/loss"]

# Show portfolio daily weighted gain against benchmark daily gain, e.g. SPY.
add_annotation('Benchmark:\n%s %s' % ('SPY', as_percentage(benchmark_spy)), 0.85)
add_annotation('Spread over benchmark:\n%s' %
               as_percentage(today_p_gain - benchmark_spy), 0.8)

# Print total gain/loss.
add_annotation('Total gain/loss:\n%s    %s' %
               (as_dollar(total_d_gain), as_percentage(total_p_gain)), 0.75)

# Print top 5 gainers.
top_gainers = ira_df[:-3].copy()

# Format database before running through function.
top_gainers.sort_values(by=['Today % gain/loss'], ascending=False, inplace=True)

top_count = 0.7

add_annotation('Today\'s top 5 gainers:', top_count)

for stock in top_gainers.index[:5]:
    
    top_count -= 0.02
    
    add_annotation('%s %s' %
                   (stock, as_percentage(top_gainers['Today % gain/loss'][stock])),
                   top_count)

# Transform top gainers into bottom gainers.
top_gainers.sort_values(by=['Today % gain/loss'], inplace=True)

bot_count = 0.55

add_annotation('Today\'s bottom 5 gainers:', bot_count)

for stock in top_gainers.index[:5]:
    
    bot_count -= 0.02
    
    add_annotation('%s %s' %
                   (stock, as_percentage(top_gainers['Today % gain/loss'][stock])),
                   bot_count)
'''

print(invest_df[['Latest price', 'Total % gain/loss', 'Portfolio %']])
print(ira_df[['Latest price', 'Total % gain/loss', 'Portfolio %']])

# TO DO groupby facts, like industry

# Save today's portfolio and image as a csv and png.
if write_output:
    ira_df.to_csv('Performance %s.csv' % right_now.strftime('%d-%m-%Y'))
    plt.savefig('Performance %s.png' % right_now.strftime('%d-%m-%Y'))
    
else:
    plt.show()