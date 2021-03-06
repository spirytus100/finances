import datetime
from bs4 import BeautifulSoup, SoupStrainer
import requests
import sqlite3
import csv
import os
import texttable


def get_stooq_quote(url, htmlid):
    content = requests.get(url)
    parse_only = SoupStrainer(id=[htmlid])
    soup = BeautifulSoup(content.text, "lxml", parse_only=parse_only)
    try:
        quote = float(soup.text)
    except ValueError:
        try:
            quote = float(soup.text.replace(",", "."))
        except ValueError:
            return False
        else:
            return quote
    else:
        return quote

def get_quotes():
    webcontent = {
        "Medicalgorythmics": ("https://stooq.pl/q/?s=mdg", "aq_mdg_c2"),
        "Enea": ("https://stooq.pl/q/?s=ena", "aq_ena_c3"),
        "BETAW20TR": ("https://stooq.pl/q/?s=etfbw20tr.pl", "aq_etfbw20tr.pl_c2"),
        "PKO BP": ("https://stooq.pl/q/?s=pko", "aq_pko_c2"),
        "Orlen": ("https://stooq.pl/q/?s=pkn", "aq_pkn_c2"),
        "Pszenica": ("https://stooq.pl/q/?s=zw.f", "aq_zw.f_c2"),
        "Srebro": ("https://nl.investing.com/etfs/etfs-physical-silver-de", "last_last"),
        "iShares EURO STOXX Banks 30-15 UCITS": ("https://stooq.pl/q/?s=fa.f", "aq_fa.f_c1"),
        "E-car LN ETF": ("https://stooq.pl/q/?s=ecar.uk", "aq_ecar.uk_c4"),
    }
    connection = sqlite3.connect("finances.db", detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    sql_select = "SELECT amount, buy_price, buy_comission FROM investments WHERE name = ?"

    asset_list = [["aktywo", "kupno", "cena akt.", "zysk", "zysk %"]]

    start_price = None
    print("Trwa pobieranie danych...")
    for key, val in webcontent.items():
        if key == "Pszenica":
            name = "ETFS Euro Daily Hedged Wheat"
            start_price = 456.25
        elif key == "Srebro":
            name = "VZLC GR ETF"
            #start_price = 29.04
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
                    if key == "Srebro":
                        quote_diff = round(quote * 4.52 - record[1], 2)
                    else:
                        quote_diff = round(quote - start_price, 2)
                else:
                    quote_diff = round(quote - record[1], 2)
                #print(key, record[1], quote, quote_diff, str(round(perc_profit, 2)) + "%")
                asset_list.append([key, record[1], quote, quote_diff, str(round(perc_profit, 2))])

            else:
                #print("Nie mo??na pobra?? danych dla instrumentu", key)
                asset_list.append([key, None, None, None, None])

    asset_table = texttable.Texttable(max_width=0)
    asset_table.add_rows(asset_list)
    print(asset_table.draw())

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
        csv_writer.writerow(("Rok", "Miesi??c", "Warto????"))
        csv_writer.writerows(inflation_list)

    print("Dane dotycz??ce inflacji zosta??y zaktualizowane.")

