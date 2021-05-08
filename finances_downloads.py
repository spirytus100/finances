from bs4 import BeautifulSoup, SoupStrainer
import requests


def get_stooq_quote(url, htmlid):
    content = requests.get(url)
    parse_only = SoupStrainer(id=[htmlid])
    soup = BeautifulSoup(content.text, "lxml", parse_only=parse_only)
    return soup.text

def get_quotes():
    webcontent = {
        "Medicalgorythmics": ("https://stooq.pl/q/?s=mdg", "aq_mdg_c2"),
        "Enea": ("https://stooq.pl/q/?s=ena", "aq_ena_c3"),
        "BETAW20TR": ("https://stooq.pl/q/?s=betaw20tr.pl", "aq_betaw20tr.pl_c3"),
        "PKO BP": ("https://stooq.pl/q/?s=pko", "aq_pko_c2"),
        "PKN Orlen": ("https://stooq.pl/q/?s=pkn", "aq_pkn_c2"),
        "Pszenica": ("https://stooq.pl/q/?s=zw.f", "aq_zw.f_c2"),
        "Srebro": ("https://stooq.pl/q/?s=xagusd", "aq_xagusd_c4"),
        "STOXX 600 Banks ETF": ("https://stooq.pl/q/?s=fa.f", "aq_fa.f_cl"),
        "E-car LN ETF": ("https://stooq.pl/q/?s=ecar.uk", "aq_ecar.uk_c4"),
    }

    for key, val in webcontent.items():
        print(key, get_stooq_quote(val[0], val[1]))