import requests
from alpha_api import alpha_api
from datetime import datetime
from tickers_to_track import tickers
time_format = "%Y-%m-%d"
today_string = datetime.strftime(datetime.today(), time_format)


def query_daily_series():
    for ticker in tickers:
        # query data
        print('ticker: ', ticker)
        daily_url = (
            "https://www.alphavantage.co/query?function={query_function}&symbol={stock_code}&outputsize={outputsize}&apikey={apikey}".format(
            query_function="TIME_SERIES_DAILY",
            stock_code=ticker,
            outputsize="full",
            apikey=alpha_api)
        )
        response = requests.get(url=daily_url).json()
        print("daily_url: ", daily_url)
        try:
            daily_series = {"series": response["Time Series (Daily)"]}
        except:
            print("response: ", response)

        # store data
        import json
        output_filename = "daily_prices_series/daily_series_{}_lastDay_{}.json".format(ticker, today_string)
        with open(output_filename, 'w') as f:
            json.dump(daily_series, f)
        f.close()


if __name__ == "__main__":
    query_daily_series()

