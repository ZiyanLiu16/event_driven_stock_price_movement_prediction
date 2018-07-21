import pickle
import requests
from alpha_api import alpha_api
from datetime import datetime
import json
import time

time_format = "%Y-%m-%d"
today_string = datetime.strftime(datetime.today(), time_format)

with open("tracking_company.pickle", "br") as f:
    tracking_company = pickle.load(f)
    tickers = {ticker for name, ticker in tracking_company.items()}


def query_daily_series():
    import time
    for ticker in tickers:
        s_t = time.time()
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
            continue

        # store data
        output_filename = "daily_prices_series/daily_series_{}_lastDay_{}.json".format(ticker, today_string)
        with open(output_filename, 'w') as f:
            json.dump(daily_series, f)
        f.close()

        #time.sleep(3)
        print("use {} sec to get historical prices of {}".format(time.time() - s_t, ticker))


if __name__ == "__main__":
    query_daily_series()