import re


def standard_cleaner(txt):
    # required
    txt = txt.lower()
    txt = re.sub('ё', 'е', txt)
    # optional
    txt = re.sub('"', '', txt)
    return txt


def russian_restore_punc_cleaner(txt):
    txt = re.sub(' - ', '-', txt)
    txt = re.sub(' ! ', '! ', txt)
    txt = re.sub(r' \? ', '? ', txt)
    # bug fix:
    #   after punctuation restoration some words with "-" splits to two words
    #       1. [что-нибудь] -> [что - нибудь] -> [что ? - нибудь ?] -> [что ?-нибудь?]
    #       2. [почему-то] -> [почему - то] -> [почему ? - то] -> [почему ?-то]
    txt = re.sub(r' [?!,.]-', '', txt)
    return txt
