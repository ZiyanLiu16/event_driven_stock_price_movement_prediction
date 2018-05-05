import requests
from alpha_api import alpha_api
from target_stock_symbols import symbols

# query interday data
# interday data only available for last 10-15 trading days.
# 1min, 5min, 15min, 30min, 60min

def query_intraday_series(interval = "30min"):
	for symbol in symbols:
	    print('symbol: ', symbol)
	    intraday_url = (
	        "https://www.alphavantage.co/query?function={query_function}&symbol={stock_code}&interval={interval}&apikey={apikey}".format(
	            query_function="TIME_SERIES_INTRADAY",
	            stock_code=symbol,
	            interval=interval,
	            apikey="alpha_api")
	    )
	    response = requests.get(url=intraday_url).json()
	    time_series = response["Time Series ({})".format(interval)]

	    # # read existing time series data
	    import json
	    exist_series_filename = "intraday_price_series/intraday_{}_{}.json".format(interval, symbol)
	    try:
	        exist_series = json.load(open(exist_series_filename))["series"]
	    except:
	        exist_series = {"series": {}}

	    # add new data to series
	    for time in time_series:
	        if time not in exist_series:
	            exist_series["series"][time] = time_series[time]

	    # save updated existed series
	    with open(exist_series_filename, 'w') as f:
	        json.dump(exist_series, f)
	        
	        
	    # use:
	    # df = pd.DataFrame({})
	    # df = df_msft.from_dict(exist_series["series"], orient = 'index')
	    # to form tabular data


if __name__ == "__main__":
	query_intraday_series()
