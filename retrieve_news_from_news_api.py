# this file enable querying news from news api (https://newsapi.org/docs/get-started)
def process_date(date):
    """
    provide a date_ (like 2019-03-05 or like 2019-03-05T20:10:23) 
                    suggesting search for news published since/until the date/time (str)
                    if input is None, the date is today at 00:00:00
    :param date (str or None)
    :return: (str)
    """
    if date is None:
        from datetime import datetime
        date = datetime.now()
        return date.strftime("%Y-%m-%d")
    return date


def make_query(company_name, sort_criterion, start_date, end_date):
    """
    :param company_name: (str)
    :param sort_criterion: either search by "popularity" or "relevance" (str)
    :param start_date: since which date the news are published in results (str, format "XXXX-XX-XX" or "2019-03-05T20:10:23"))
    :param end_date:   until which date the news are published in results (str, format "XXXX-XX-XX" or "2019-03-05T20:10:23"))
    :return: dict of :
            {'totalResults':
             'articles':
             {'source': , 'author':, 'title':, 'description':, 'url':, 'content': , 'publishedAt':,}
    """
    from credentials import news_api_key
    import requests
    url = ('https://newsapi.org/v2/everything?'
           'q={}&'
           'from={}&'
           'to={}&'
           'sortBy={}&'
           'apiKey={}'.format(company_name, start_date, end_date, sort_criterion, news_api_key))
    return requests.get(url).json()


def language_detection(text):
    from utils import clean_text
    from langdetect import detect
    try:
        pred = detect(clean_text(text))
    except:
        pred = "und"
    return 'en' if pred in {'en', 'und', 'xx-Qaai', 'sco'} else "foreign"


def filter_irrelevant_news(news, company_name):
    """
    filter out news that
        1) is foreign, or 
        2) doesn't include the company name in title
    :param news: raw dict from query (dict)
    :param company_name: (str) 
    :return: relevant_news: list of relevant news, each element stays the same format as element
                            in response['articles']
    """
    relevant_news = []
    for article in news['articles']:
        title = article['title']
        if company_name.lower() not in title.lower():
            continue

        lang_detected = language_detection(title)
        if lang_detected == 'foreign':
            continue

        relevant_news.append(article)

    return relevant_news


def decide_news_sort_criterion(company_name):
    if company_name in {"YY", "HUYA", "Bilibili"}:
        sort_criterion = "relevance"
    else:
        sort_criterion = "popularity"
    return sort_criterion


def make_single_search(company_name, start_date=None, end_date=None):
    """
    :param company_name (str)
    :param start_date: since which date the news are published in results (
                       str, format "XXXX-XX-XX" or "2019-03-05T20:10:23")
    :param end_date: util which date the news are published in results (
                       str, format "XXXX-XX-XX" or "2019-03-05T20:10:23")
    :return:
    """
    start_date = process_date(start_date)
    end_date = process_date(end_date)
    sort_criterion = decide_news_sort_criterion(company_name)
    response = make_query(company_name, sort_criterion, start_date, end_date)
    return response


def reformat_news(elem, company_name, company_ticker):
    """
    extract title, date, company information
    :param elem: {'source': , 'author':, 'title':, 'description':, 'url':, 'content': , 'publishedAt':,} (dict)
    :param company_name: (str)
    :param company_ticker: (str)
    :return: (date_str, ticker, company_name, title, url)(tuple) 
    """
    # TODO: stock symbol
    from utils import clean_text_for_store_in_csv, reformat_datestr
    return (reformat_datestr(elem['publishedAt']),
            company_ticker,
            company_name,
            clean_text_for_store_in_csv(elem['title']),
            elem['url'])


def save_news_to_csv(news):
    """
    store news in .csv file
    :param news: (list of tuple)
    """
    with open("company_news.csv", "a") as f:
        for elem in news:
            print(','.join(elem), file=f)


def clean_and_summarize_result(news, company_name, company_ticker):
    relevant_news = filter_irrelevant_news(news, company_name)
    relevant_news_reformatted = [reformat_news(elem, company_name, company_ticker) for elem in relevant_news]
    return relevant_news_reformatted


def retrieve_news(start_date, end_date, company_source, save_news=True):

    news = []
    company_name_list, tickers_list = decide_companies_to_check(company_source)
    for i, company_name in enumerate(company_name_list):
        response = make_single_search(company_name, start_date, end_date)
        news.extend(clean_and_summarize_result(response, company_name, tickers_list[i]))

    if save_news:
        save_news_to_csv(news)

    return news


def decide_companies_to_check(company_source):
    """
    decide news from which companies to search
    :param company_source: flag, if == "my_favorite", only check companies from "companies_of_concern.py",
           otherwise track all companies from "tracking_compnay.pickle.
    :return: company_names: (list of str)
    :return: tickers: (list of str)
    """
    from companies_of_concern import companies_of_concern as company_names_my_favorite
    from companies_of_concern import companies_of_concern_ticker as tickers_my_favorite
    if company_source != "my_favorite":
        import pickle
        with open("tracking_company.pickle", "br") as f:
            tracking_company = pickle.load(f)
        for i, name in enumerate(company_names_my_favorite):  # add those not in pickle, like Bilibili, BILI
            tracking_company[name] = tickers_my_favorite[i]
        company_names, tickers = list(tracking_company.keys()), list(tracking_company.values())
    else:
        company_names, tickers = company_names_my_favorite, tickers_my_favorite

    return company_names, tickers


