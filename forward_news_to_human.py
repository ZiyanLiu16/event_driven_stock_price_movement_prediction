# this module can send news (or only news predicted to rise in price on next day) via email
from retrieve_news_from_news_api import retrieve_news
from model import Model


def find_positive_news(news):
    model = Model()
    return [elem for elem in news if model.predict(elem) == 'positive']


def forward_information(only_predicted_positive=False):
    """
    this function forward useful news via email
    :param only_predicted_positive: if True, only includes news predicted to suggest rise in price by model
    """
    news = retrieve_news()

    if only_predicted_positive:
        news = find_positive_news(news)

    message = create_message("ziyan@canvs.tv", "zl488@cornell.edu", news)
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


def form_content(news):
    """
    form content of email
    :param news: list of (publish_date, symbol, company_name, news, url) (list of tuple)
    :return: (str)
    """
    content_list = []
    for elem in news:
        company_name = elem[2]
        title = elem[3]
        url = elem[4]
        content_list.append("company_name: {}\ntitle:{}\nurl:{}".format(company_name, title, url))
    return '\n\n'.join(content_list)


def create_message(sender, to, news):
    """ 
    :param sender: Email address of the sender.
    :param to: Email address of the receiver.
    :param subject: The subject of the email message.
    :param news: list of (publish_date, symbol, company_name, news, url) (list of tuple)
    :return: An object containing a base64url encoded email object.
    """
    subject = get_email_subject()
    message_text = form_content(news)

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

