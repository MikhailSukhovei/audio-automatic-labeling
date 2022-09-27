import re


def russian_cleaner(txt):
    # required
    txt = txt.lower()
    txt = re.sub('ё', 'е', txt)
    # optional
    txt = re.sub('"', '', txt)
    return txt


def english_cleaner(txt):
    # required
    txt = txt.lower()
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


def english_restore_punc_cleaner(txt):
    txt = re.sub(" ' ", "'", txt)
    txt = re.sub(' - ', '-', txt)
    txt = re.sub(r' \? ', '? ', txt)
    txt = re.sub(' ! ', '! ', txt)
    txt = re.sub(r' [?!,.]-', '', txt)
    return txt
