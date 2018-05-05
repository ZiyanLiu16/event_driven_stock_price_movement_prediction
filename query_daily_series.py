from datetime import datetime
time_format = "%Y-%m-%d"
today_string = datetime.strftime(datetime.today(), time_format)


def query_daily_series():
	for symbol in symbols:
	    # query data
	    print('symbol: ', symbol)
	    daily_url = (
	    "https://www.alphavantage.co/query?function={query_function}&symbol={stock_code}&outputsize={outputsize}&apikey={apikey}".format(
	        query_function="TIME_SERIES_DAILY",
	        stock_code=symbol,
	        outputsize="full",
	        apikey=alpha_api))
	    response = requests.get(url=daily_url).json()
	    daily_series = {"series": response["Time Series (Daily)"]}

	    # store data
	    import json
	    output_filename = "daily_prices_series/daily_series_{}_lastDay_{}.json".format(symbol, today_string)
	    with open(output_filename, 'w') as f:
	        json.dump(daily_series, f)
	    f.close()

if __name__ == "__main__":
	query_daily_series()