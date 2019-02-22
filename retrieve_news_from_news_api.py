# this file enable querying news from news api (https://newsapi.org/docs/get-started)
def process_date(start_date):
    """
    provide a date_string (xxxx-xx-xx) suggesting search for news published since the date (str)
    if input is None, the date is today
    :param start_date: 
    :return: (str)
    """
    if start_date is None:
        from datetime import datetime
        start_date = datetime.now()
    return start_date.strftime("%Y-%m-%d")


def make_query(company_name, sort_criterion, start_date):
    """
    :param company_name: (str)
    :param sort_criterion: either search by "popularity" or "relevance" (str)
    :param start_date: since which date the news are published in results (str, format "XXXX-XX-XX")
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
           'sortBy={}&'
           'apiKey={}'.format(company_name, start_date, sort_criterion, news_api_key))
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
        sort_criterion="popularity"
    return sort_criterion


def make_single_search(company_name, start_date=None):
    """
    :param company_name (str)
    :param start_date: since which date the news are published in results (str, format "XXXX-XX-XX")
    :return: 
    """
    start_date = process_date(start_date)
    sort_criterion = decide_news_sort_criterion(company_name)
    response = make_query(company_name, sort_criterion, start_date)
    return response


def reformat_news(elem, company_name):
    """
    extract title, date, company information
    :param elem: {'source': , 'author':, 'title':, 'description':, 'url':, 'content': , 'publishedAt':,} (dict)
    :param company_name: (str)
    :return: (date_str, stock_symbol, company_name, titile, url)(tuple) # TODO: stock symbol
    """
    from utils import clean_text_for_store_in_csv, reformat_datestr
    return (reformat_datestr(elem['publishedAt']),
            "", company_name,
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


def clean_and_summarize_result(news, company_name):
    relevant_news = filter_irrelevant_news(news, company_name)
    relevant_news_reformatted = [reformat_news(elem, company_name) for elem in relevant_news]
    return relevant_news_reformatted


def retrieve_news(start_date=None, save_news=True):
    news = []
    from companies_of_concern import companies_of_concern as company_name_list
    for company_name in company_name_list:
        response = make_single_search(company_name, start_date)
        news.extend(clean_and_summarize_result(response, company_name))

    if save_news:
        save_news_to_csv(news)

    return news
