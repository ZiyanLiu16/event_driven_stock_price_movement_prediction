import pickle
import requests
from bs4 import BeautifulSoup


with open("tracking_company.pickle", "br") as f:
    tracking_company = pickle.load(f)
    tickers = {ticker for name, ticker in tracking_company.items()}


def seek_company(title, ticket_common_name):
    # search for company name in the news title,
    # return (ticket of company, name of name) if there is one
    # return False if there isn't a company identified
    for company_common_name, company_ticket in ticket_common_name.items():
        import re
        company_common_name_clean = company_common_name.lower()
        title_clean = re.sub(r"[.,\)\(\-]+", " ", title).lower()
        title_clean = ' '.join(title_clean.split()).strip()
        company_common_name_clean_tokens = company_common_name_clean.split()

        # search for single-word name company
        if len(company_common_name_clean_tokens) == 1:
            title_clean_tokens = title_clean.split()
            if company_common_name_clean_tokens[0] in title_clean_tokens:
                return company_ticket, company_common_name
        # search for multi-word name company
        elif company_common_name_clean in title_clean:
            return company_ticket, company_common_name
    return False


with open("tracking_company.pickle", "br") as f:
    tracking_company = pickle.load(f)


def download_news(dates_to_check=2):
    from datetime import datetime, timedelta
    import time
    today = datetime.today()
    for d in range(dates_to_check):
        s_t = time.time()
        # get page contents
        date_to_check = today + timedelta(days=-d)
        date_string = datetime.strftime(date_to_check, "%Y%m%d")
        print(date_string)
        url = "https://www.reuters.com/resources/archive/us/{}.html".format(date_string)
        content = requests.get(url).content

        # parsing web page
        soup = BeautifulSoup(content, "lxml")
        items = soup.find_all("div", {"class": ["headlineMed"]})
        for item in items:
            # save events
            article_url = item.a['href']
            raw_text = item.get_text().split("\xa0")
            title = raw_text[0]
            try:
                news_time = datetime.strptime(date_string+' '+raw_text[-1], "%Y%m%d %I:%M%p %Z")
                news_time_string = datetime.strftime(news_time, "%Y%m%d %H:%M")
            except Exception as e:
                print(e)
                print(item.get_text())
                print(raw_text)

            matching = seek_company(title, tracking_company)
            if matching is False:
                continue
            company_ticket, company_common_name = matching
            title = title.replace('"', "'")

            
            with open("company_news.csv", "a+") as f:
                print('"{}","{}","{}","{}","{}"'.format(
                    news_time_string, company_ticket, company_common_name, title, article_url), file=f
                )

        print("used {} sec to query news".format(time.time() - s_t))