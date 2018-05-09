import requests
import time
import datetime
import numpy as np
from bs4 import BeautifulSoup


class ReutersNews:

    def __init__(self):
        with open("stocks_names.txt") as f:
            self.stocks = f.readlines()
        f.close()

        try:
            with open("recorded_stock_date.txt", "r+") as f:
                self.recorded_stock_date = {line.strip() for line in f}
            f.close()
        except:
            self.recorded_stock_date = set()

        print(self.recorded_stock_date)

    def generate_date(self, num_days):
        today_date = datetime.datetime.today()
        dates_list = [today_date - datetime.timedelta(days=x) for x in range(0, num_days)]
        dates_string_list = [date.strftime("%Y%m%d") for date in dates_list]
        return dates_string_list

    def get_news_reuters(self, n=3):
        dates_string_list = self.generate_date(n)  # look back on the past n days
        for stock in self.stocks:
            for i, date_string in enumerate(dates_string_list):
                company, symbol, exchange = stock.split(", ")
                print('this combination: ', date_string+'_'+symbol)
                if date_string+'_'+symbol in self.recorded_stock_date:
                    print("captured!")
                    continue  # news of stock on this date has been obtained
                if i == 0:
                    self.get_news_of_today(symbol, company, exchange.strip(), date_string)
                else:
                    self.get_historical_news(symbol, company, exchange.strip(), date_string)
                with open("recorded_stock_date.txt", "a+") as f:
                    print(date_string+'_'+symbol, file=f)
                f.close()

    @staticmethod
    def parser(content, soup, symbol, company, date_string):
        with open('news/news_reuters.csv', 'a+') as f:
            # r+ for reading and writing.The stream is positioned at the beginning of the file.
            # a+ for reading and appending(writing at end of file).The file is created if it does not

            for i in range(len(content)):
                title = content[i].h2.get_text().replace(",", " ").replace("\n", " ")
                body = content[i].p.get_text().replace(",", " ").replace("\n", " ")

                if i == 0 and len(soup.find_all("div", class_="topStory")) > 0:
                    news_type = 'topStory'
                else:
                    news_type = 'normal'

                # get time
                article_url = "https://www.reuters.com"+content[i].h2.a['href']
                article_page_html = requests.get(article_url).content
                article_soup = BeautifulSoup(article_page_html, "lxml")
                publish_time_string = article_soup.find_all("div", {"class":"date_V9eGk"})
                publish_time_string = ' '.join(publish_time_string[0].text.split()[:6])
                publish_time = datetime.datetime.strptime(publish_time_string, '%b %d, %Y / %I:%M %p')
                publish_time_string = publish_time.strftime('%Y-%m-%d-%H-%M-%S')


                print(
                    "symbol: {}\ndate: {}\ndatetime: {}\ntitle: {}\nnews_type: {}\n".format(
                        symbol, date_string, publish_time_string, title, news_type))
                date_string_with_dash = date_string[:4]+'-'+date_string[4:6]+"-"+date_string[7:]
                print(','.join([symbol, company, publish_time_string, date_string_with_dash, title, body, news_type]), file=f)

        f.close()

    @staticmethod
    def get_content(url):
        has_content = 0
        repeat_times = 4
        for _ in range(repeat_times):  # repeat in case of http failure
            time.sleep(np.random.poisson(3))
            response = requests.get(url)
            html = response.content
            soup = BeautifulSoup(html, "lxml")
            content = soup.find_all("div", {'class': ['topStory', 'feature']})
            has_content = len(content)
            if has_content:
                break
        return has_content, content, soup

    def get_news_of_today(self, symbol, company, exchange, date_string):
        suffix = {"NYSE": ".N", "NASDAQ": ".O", "AMEX": ".A"}
        url = "http://www.reuters.com/finance/stocks/companyNews/{}{}".format(symbol, suffix[exchange])
        print("url:", url)
        has_content, content, soup = self.get_content(url)
        if has_content:
            self.parser(content, soup, symbol, company, date_string)

    def get_historical_news(self, symbol, company, exchange, date_string):
        new_time = date_string[4:] + date_string[:4]  # change 20180506 to 05062018 to match reuters format
        suffix = {"NYSE": ".N", "NASDAQ": ".O", "AMEX": ".A"}
        url = "http://www.reuters.com/finance/stocks/companyNews/{}{}".format(symbol, suffix[exchange])
        url_with_date = url + "?date=" + new_time
        print('historical url: ', url_with_date)
        has_content, content, soup = self.get_content(url_with_date)
        if has_content:
            self.parser(content, soup, symbol, company, date_string)

if __name__ == "__main__":
    pass