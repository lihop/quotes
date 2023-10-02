#!/bin/python
# SPDX-FileCopyrightText: 2022 Leroy Hopson <copyright@leroy.geek.nz>
#
# SPDX-License-Identifier: CC0-1.0

import requests
import json
import sqlite3
import dateutil.parser
import pandas as pd
import math
import warnings
from bs4 import BeautifulSoup as bs
from datetime import datetime
from requests.adapters import HTTPAdapter, Retry
from tabula import read_pdf
from urllib.error import HTTPError

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
HEADERS = { 'User-Agent': USER_AGENT }

con = sqlite3.connect("quotes.db")
cur = con.cursor()

# Use a requests Session in order to enable retries.
session = requests.Session()
retries = Retry(total=5, backoff_factor=1)
session.mount("https://", HTTPAdapter(max_retries=retries))

cur.execute('''CREATE TABLE IF NOT EXISTS quotes
               (symbol text, date text, price real)''')
cur.execute(
    "CREATE UNIQUE INDEX IF NOT EXISTS symbol_date_idx ON quotes (symbol, date)")
con.commit()

# FND40819.NZ Foundation Series Total World Fund
res = session.get(
    "https://www.fundrock.com/fundrock-new-zealand/frnz-documents-and-reporting/", headers=HEADERS)
table = pd.read_html(res.content)[2]
for fund in table.iterrows():
    if fund[1][0] != "Foundation Series Total World Fund":
        continue
    price = fund[1][2]
    date = datetime.strptime(fund[1][1], '%m/%d/%Y').strftime('%Y-%m-%d')
    assert date and price, "Could not determine date and/or price."
    con.execute("REPLACE INTO quotes VALUES('FND40819.NZ', ?, ?)",
                [date, price])
    con.commit()

# VAN1579.AU Vanguard International Shares Select Exclusions Index Fund
res = session.get(
    "https://www.vanguard.com.au/adviser/api/products/adviser/fund/8122/prices?limit=-1")
json = json.loads(res.content)
buy = json["data"][0]["buyPrices"][0]
price = buy["price"] / 1.0007
date = dateutil.parser.isoparse(buy["asOfDate"]).strftime('%Y-%m-%d')
assert date and price, "Could not determine date and/or price."
con.execute("REPLACE INTO quotes VALUES('VAN1579.AU', ?, ?)", [date, price])
con.commit()

# FND1423.NZ Harbour NZ Index Shares Fund
res = session.get("https://www.harbourasset.co.nz/our-funds/index-shares/", headers=HEADERS, timeout=120)
table = pd.read_html(res.text)[2]
date = table["Date"][0]
price = table["Unit Price NZD"][0]
assert date and price, "Could not determine date and/or price."
con.execute("REPLACE INTO quotes VALUES('FND1423.NZ', ?, ?)", [date, price])
con.commit()

# FUEMAV30.VN MAFM VN30 ETF
res = session.get("https://finance.vietstock.vn/FUEMAV30-quy-etf-mafm-vn30.htm", headers=HEADERS)
table_html = bs(res.text, 'html.parser').find('table', {'id': 'stock-transactions'})
table = pd.read_html(str(table_html))[0]
for row in table.iterrows():
    date_str = row[1]["Ngày"]
    date = datetime.strptime(date_str, '%d/%m/%Y').strftime('%Y-%m-%d')
    price = row[1]["Giá đóng cửa"]
    assert date and price, "Could not determine date and/or price."
    con.execute("REPLACE INTO quotes VALUES('FUEMAV30.VN', ?, ?)",
                [date, price])
    con.commit()

con.close()
