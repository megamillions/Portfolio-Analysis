import datetime
import matplotlib.pyplot as plt
import pandas as pd
import yahoo_fin.stock_info as si

# Measured in years.
timespan = 5

today = datetime.date.today()
past = today - datetime.timedelta(days = timespan * 365)

stocks = ['FB', 'AAPL', 'AMZN', 'NFLX', 'GOOGL']

for stock in stocks:
    
    stock_data = si.get_data(stock, start_date = past, end_date = today)
    
    stock_df = pd.Series(stock_data.adjclose)
    
    initial = stock_df.iloc[0]

    stock_indexed = stock_df.transform(lambda x: (x / initial) * 100)

    plt.plot(stock_indexed, label=stock)

plt.legend(loc='upper left')

plt.show()