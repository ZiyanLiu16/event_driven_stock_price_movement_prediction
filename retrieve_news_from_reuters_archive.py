import pickle
import requests
from bs4 import BeautifulSoup
from collections import defaultdict, Counter

all_name = set()
all_name_tokens = []
with open("news_reuters.csv", "r") as f:
    for i, line in enumerate(f):
        ticket, name, date, title, body, newsType = line.split(",")
        if name not in all_name:
            all_name_tokens.extend(name.split())
        all_name.add(name)

all_name_tokens_summary = Counter(all_name_tokens)


results = defaultdict(list)
with open("news_reuters.csv", "r") as f:
    for i, line in enumerate(f):
        ticket, name, date, title, body, newsType = line.split(",")
        name_tokens = set(name.split())
        title_tokens = set(title.split())

        shared_token = name_tokens & title_tokens
        if shared_token:
            if (len(list(shared_token)) == 1 and
                all_name_tokens_summary[list(shared_token)[0]] == 1 and
                        (name, name_tokens & title_tokens) not in results[ticket]):
                results[ticket].append((name, name_tokens & title_tokens))


merged_results = {}
for ticket, name_parts in results.items():
    if len(name_parts) == 1:
        output_name = list(name_parts[0][1])[0]
    else:
        merge_name = ' '.join([list(elem[1])[0] for elem in name_parts])
        if merge_name in name_parts[0][0]:
            output_name = merge_name

    formal_name_tokens = name_parts[0][0].split()
    output_name_tokens = output_name.split()

    if (len(output_name_tokens) == len(formal_name_tokens) or
        (
            len(output_name_tokens) + 1 == len(formal_name_tokens) and
            set(formal_name_tokens) & {"Corp", "Inc", "Ltd", "Corporation", "plc", "Incorporated"}
        )
       ):
        merged_results[ticket] = (name_parts[0][0], output_name)


# create common name -> ticket mapping
ticket_common_name = {}
for ticket, name in merged_results.items():
    if not name[1] in ticket_common_name:
        ticket_common_name[name[1]] = ticket

ticket_common_name["Google"] = "GOOGL"
for ambiguous_name in {"Shire", "Target", "BP", "News", "Nasdaq", "Harris", "Hess", "NICE"}:
    del ticket_common_name[ambiguous_name]

ticket_common_name["Amazon"] = "AMZN"
ticket_common_name["Alibaba"] = "BABA"
ticket_common_name["Blizzard"] = "ATVI"

# create tickers that corresponds to the stock want to track
ticker_to_track = {ticker for name, ticker in ticket_common_name.items()}
with open("stock_to_track_tickers.pickle", "bw+") as f:
    pickle.dump(ticker_to_track, f)


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


def download_news(dates_to_check=1):
    from datetime import datetime, timedelta
    today = datetime.today()
    for d in range(dates_to_check):
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
            ariticle_url = item.a['href']
            raw_text = item.get_text().split("\xa0")
            title = raw_text[0]
            try:
                news_time = datetime.strptime(date_string+' '+raw_text[-1], "%Y%m%d %I:%M%p %Z")
                news_time_string = datetime.strftime(news_time, "%Y%m%d %H:%M")
            except Exception as e:
                print(e)
                print(item.get_text())
                print(raw_text)

            matching = seek_company(title, ticket_common_name)
            if matching is False:
                continue
            company_ticket, company_common_name = matching
            title = title.replace('"', "'")
            with open("news_examples_with_stocks.csv", "a+") as f:
                print('"{}","{}","{}","{}","{}"'.format(
                    news_time_string, company_ticket, company_common_name, title, ariticle_url), file=f
                )