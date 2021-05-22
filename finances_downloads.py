import datetime
from bs4 import BeautifulSoup, SoupStrainer
import requests
import sqlite3
import csv
import os


def get_stooq_quote(url, htmlid):
    content = requests.get(url)
    parse_only = SoupStrainer(id=[htmlid])
    soup = BeautifulSoup(content.text, "lxml", parse_only=parse_only)
    try:
        quote = float(soup.text)
    except ValueError:
        return False
    else:
        return quote

def get_quotes():
    webcontent = {
        "Medicalgorythmics": ("https://stooq.pl/q/?s=mdg", "aq_mdg_c2"),
        "Enea": ("https://stooq.pl/q/?s=ena", "aq_ena_c3"),
        "BETAW20TR": ("https://stooq.pl/q/?s=betaw20tr.pl", "aq_betaw20tr.pl_c3"),
        "PKO BP": ("https://stooq.pl/q/?s=pko", "aq_pko_c2"),
        "Orlen": ("https://stooq.pl/q/?s=pkn", "aq_pkn_c2"),
        "Pszenica": ("https://stooq.pl/q/?s=zw.f", "aq_zw.f_c2"),
        "Srebro": ("https://stooq.pl/q/?s=xagusd", "aq_xagusd_c4"),
        "iShares EURO STOXX Banks 30-15 UCITS": ("https://stooq.pl/q/?s=fa.f", "aq_fa.f_cl"),
        "E-car LN ETF": ("https://stooq.pl/q/?s=ecar.uk", "aq_ecar.uk_c4"),
    }
    connection = sqlite3.connect("finances.db", detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    sql_select = "SELECT amount, buy_price, buy_comission FROM investments WHERE name = ?"

    start_price = None
    for key, val in webcontent.items():
        if key == "Pszenica":
            name = "ETFS Euro Daily Hedged Wheat"
            start_price = 456.25
        elif key == "Srebro":
            name = "VZLC GR ETF"
            start_price = 29.04*4.49
        else:
            name = key
        cursor = connection.execute(sql_select, (name,))
        if cursor:
            record = cursor.fetchone()
            quote = get_stooq_quote(val[0], val[1])
            if quote:
                perc_profit = ((quote * record[0] - record[2]) - (record[0] * record[1] + record[2])) / (
                            record[0] * record[1] + record[2]) * 100
                if start_price is not None:
                    quote_diff = round(quote - start_price, 2)
                else:
                    quote_diff = round(quote - record[1], 2)
                print(key, record[1], quote, quote_diff, str(round(perc_profit, 2)) + "%")

            else:
                print("Nie można pobrać danych dla instrumentu", key)

def get_inflation_stats():
    year = datetime.datetime.now().year
    month = datetime.datetime.now().month
    if month == 1:
        year = year - 1
        file_month = 12
    else:
        file_month = month - 1

    str_date = datetime.datetime.strftime(datetime.datetime(year, file_month, 1), "%d%m%Y")[2:]
    if os.path.exists("inflacja_org_" + str_date + ".csv"):
        return
    else:
        url = "https://stat.gov.pl/download/gfx/portalinformacyjny/pl/defaultstronaopisowa/4741/1/1/miesieczne_wskazniki_cen_towarow_i_uslug_konsumpcyjnych_od_1982_roku_" + str_date[:2] + "-" + str_date[2:] + ".csv"
        #url = "https://stat.gov.pl/download/gfx/portalinformacyjny/pl/defaultstronaopisowa/4741/1/1/miesieczne_wskazniki_cen_towarow_i_uslug_konsumpcyjnych_od_1982_roku_03-2021.csv"
        r = requests.get(url)

        if r.status_code != 200:
            return

    with open("inflacja_org_" + str_date + ".csv", "wb") as fo:
        fo.write(r.content)

    with open("inflacja_org_" + str_date + ".csv", "r", encoding="cp850") as fo:
        csv_reader = csv.reader(fo, delimiter=";")
        inflation_list = []
        for row in csv_reader:
            if row[2].startswith("Analogiczny m"):
                inflation_list.append([row[3], row[4], row[5]])

    with open("inflacja_gus.csv", "w", newline="") as fo:
        csv_writer = csv.writer(fo, delimiter=";")
        csv_writer.writerow(("Rok", "Miesiąc", "Wartość"))
        csv_writer.writerows(inflation_list)

    print("Dane dotyczące inflacji zostały zaktualizowane.")

