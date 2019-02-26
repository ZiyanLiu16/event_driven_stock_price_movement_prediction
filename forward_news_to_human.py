# this module can send news (or only news predicted to rise in price on next day) via email
from retrieve_news_from_news_api import retrieve_news
from model import Model


def get_predictions(news):
    """
    :param news: (list of str) 
    :return: list of probability whether a piece of news suggest rise in stock price (list of float) 
    """
    model = Model()
    model.load_model("model_2019-02-24_16-11.pickle")
    titles = [elem[3] for elem in news]
    return model.predict(titles)


def forward_information(start_date=None):
    """
    this function forward useful news via email
    :param start_date: xxxx-xx-xx
    :return: 
    """
    news = retrieve_news(start_date=start_date)
    prob = get_predictions(news)

    message = create_message("ziyan@canvs.tv", "zl488@cornell.edu", news, prob)
    service = build_service()
    send_message(service, "ziyan@canvs.tv", message)


def build_service():
    """
    build gmail api service
    :return: service object 
    """
    import pickle
    from googleapiclient.discovery import build
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
    service = build("gmail", "v1", credentials=creds)
    return service


def get_email_subject():
    return "news that mights suggest chances"


def form_content(news, prob):
    """
    form content of email
    :param news: list of (publish_date, symbol, company_name, news, url) (list of tuple)
    :param prob: list of probability whether the piece of news suggest rise in stock price (list of float)
    :return: (str)
    """
    news_prob = [(round(prob[i], 4), elem[2], elem[3], elem[4]) for i, elem in enumerate(news)]
    news_prob_sorted = sorted(news_prob, key=lambda x: x[0], reverse=True)
    content_list = ["company_name: {}\nscore:{}\ntitle:{}\nurl:{}".format(company_name, prob, title, url)
                    for prob, company_name, title, url in news_prob_sorted]
    return '\n\n'.join(content_list)


def create_message(sender, to, news, prob):
    """ 
    :param sender: Email address of the sender.
    :param to: Email address of the receiver.
    :param news: list of (publish_date, symbol, company_name, news, url) (list of tuple)
    :param prob: list of probability whether the piece of news suggest rise in stock price
    :return: An object containing a base64url encoded email object.
    """
    subject = get_email_subject()
    message_text = form_content(news, prob)

    from email.mime.text import MIMEText
    import base64
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes())
    raw = raw.decode()
    body = {'raw': raw}
    return body


def send_message(service, user_id, message):
    """
    Send an email message.
    :param service: Authorized gmail API service instance.
    :param user_id: User's email address. The special value "me"
                    can be used to indicate the authenticated user.
    :param message: Message to be sent.
    :return: Sent Message.
    """
    try:
        message = (service.users().messages().send(userId=user_id, body=message)
                   .execute())
        print('Message Id: %s' % message['id'])
        return message
    except Exception as e:
        print('An error occurred: %s' % e)

