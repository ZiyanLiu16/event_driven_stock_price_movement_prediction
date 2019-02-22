# necessary to clean stuff before feed it to function for forign language judgment
import re
mentions_regex = re.compile(r'@\w*')
hashtags_regex = re.compile(r'#\w*')
retweet_regex = re.compile(r'^RT @\w+\s?:')
hyperlink_regex = re.compile(r'https?://\S+')
first_word_of_sentence_regex = re.compile(r'[!?.]\s*\w+')
words_regex = re.compile(r'\w+')
punctuation_regex = re.compile(r"[.!,…;:?\'\"\’£}{)(*“”|]")
emojis_regex = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U0001F1F2-\U0001F1F4"  # Macau flag
        u"\U0001F1E6-\U0001F1FF"  # flags
        u"\U0001F600-\U0001F64F"
        u"\U00002702-\U000027B0"
        #u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U0001F1F2"
        u"\U0001F1F4"
        u"\U0001F620"
        u"\u200d"
        u"\u2640-\u2642"
        u"🤢"
        u"🤣"
        u"🤔"
        u"🤗"
        u"🤓"
        u"🤐"
        "]+", flags=re.UNICODE)


def clean_text(text):
    text_to_consider = text
    text_to_consider = emojis_regex.sub('', text_to_consider)
    text_to_consider = hashtags_regex.sub('', text_to_consider)
    text_to_consider = retweet_regex.sub('', text_to_consider)
    text_to_consider = mentions_regex.sub('', text_to_consider)
    text_to_consider = hyperlink_regex.sub('', text_to_consider)
    text_to_consider = punctuation_regex.sub('', text_to_consider)
    text_to_consider = text_to_consider.lower().strip()
    return text_to_consider


def clean_text_for_store_in_csv(text):
    return '"'+text.replace(',', '').replace('"', "'")+'"'


def reformat_datestr(date_str):
    import datetime
    datetime_obj = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    return datetime_obj.strftime("%Y%m%d %H%:%M")
