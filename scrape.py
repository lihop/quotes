#!/bin/python
# SPDX-FileCopyrightText: 2022 Leroy Hopson <copyright@leroy.geek.nz>
#
# SPDX-License-Identifier: CC0-1.0

import requests
import json
import sqlite3
import dateutil.parser
import pandas as pd
import batdata
import math
from bs4 import BeautifulSoup as bs
from datetime import datetime

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

con = sqlite3.connect("quotes.db")
cur = con.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS quotes
               (symbol text, date text, price real)''')
cur.execute(
    "CREATE UNIQUE INDEX IF NOT EXISTS symbol_date_idx ON quotes (symbol, date)")
con.commit()

# FND20410.NZ Foundation Series Growth Fund
#res = requests.get(
#    "https://iisolutions.co.nz/fund-hosting/documents-and-reporting-2/", headers=HEADERS)
#table = pd.read_html(res.content)[1]
#for fund in table.iterrows():
#    if fund[1]['Funds'] != "Foundation Series Growth Fund":
#        continue
#    price = fund[1]['Unit Price']
#    date = datetime.strptime(fund[1]['Date'], '%d-%b-%y').strftime('%Y-%m-%d')
#    assert date and price, "Could not determine date and/or price."
#    con.execute("REPLACE INTO quotes VALUES('FND20410.NZ', ?, ?)",
#                [date, price])
#    con.commit()

# VAN1579.AU Vanguard International Shares Select Exclusions Index Fund
res = requests.get(
    "https://www.vanguard.com.au/institutional/products/api/data/detail/au/inst/en/8122/wholesale/equity")
json = json.loads(res.content)
nav = json["fundDetail"]["fundData"]["dailyPrice"]["NAV"]
price = nav["price"]
date = dateutil.parser.isoparse(nav["effectiveDate"]).strftime('%Y-%m-%d')
assert date and price, "Could not determine date and/or price."
con.execute("REPLACE INTO quotes VALUES('VAN1579.AU', ?, ?)", [date, price])
con.commit()

# FND1423.NZ Harbour NZ Index Shares Fund
res = requests.get("https://www.harbourasset.co.nz/our-funds/index-shares/")
table = pd.read_html(res.text)[2]
date = table["Date"][0]
price = table["Unit Price NZD"][0]
assert date and price, "Could not determine date and/or price."
con.execute("REPLACE INTO quotes VALUES('FND1423.NZ', ?, ?)", [date, price])
con.commit()

# FND79.NZ AMP Capital NZ Fixed Interest Fund
# FND8205.NZ AMP NZ Shares Index Fund
# FND8207.NZ AMP All Country Global Shares Index Fund
funds = [
    # Funds acquired by Macquarie Asset Management, so skip for now.
    # {'symbol': 'FND79.NZ', 'url': 'https://www.ampcapital.com/nz/en/investments/funds/fixed-interest/amp-capital-nz-fixed-interest-fund', 'spread': 0.000992},
    # {'symbol': 'FND8205.NZ', 'url': 'https://www.ampcapital.com/nz/en/investments/funds/index-funds/nz-shares-index-fund', 'spread': 0.0027},
    # {'symbol': 'FND8207.NZ', 'url': 'https://www.ampcapital.com/nz/en/investments/funds/index-funds/all-country-global-shares-index-fund', 'spread': 0.0007},
]
for fund in funds:
    res = requests.get(fund['url'])
    soup = bs(res.text, 'html.parser')
    buy = float(soup.find_all('div', {'class': 'ht-highlight_color'})[1].text)
    sell = float(soup.find_all('div', {'class': 'ht-highlight_color'})[2].text)
    price = round(buy - (buy * fund['spread']), 4)
    sell_adjusted = round(sell + (sell * fund['spread']), 4)
    assert math.isclose(
        price, sell_adjusted, rel_tol=0.0001), "buy/sell prices not equal after adjusting for buy/sell spread."
    date_str = soup.find_all("div", {"class": "ht-meta"})[2].text
    date = datetime.strptime(date_str, 'As at %d %b %Y').strftime('%Y-%m-%d')
    assert date and price, "Could not determine date and/or price."
    con.execute("REPLACE INTO quotes VALUES(?, ?, ?)",
                [fund['symbol'], date, price])
    con.commit()

# FND2387.NZ Hunter Global Fixed Interest Fund
#res = requests.get(
#    'https://www.morningstar.com.au/Funds/FundReport/24267', headers=HEADERS)
#table = pd.read_html(res.content)[5]
#buy = float(table[1][4])
#sell = float(table[1][5])
#assert sell == round(buy - (buy * 0.001),
#                     4), "buy/sell prices not equal after adjusting for buy/sell spread."
#price = buy
#soup = bs(res.text, 'html.parser')
#date_str = soup.find_all("p", {'class': 'fundreportsubheading'})[3].text
#date = datetime.strptime(date_str, 'as at %d %b %Y').strftime('%Y-%m-%d')
#con.execute("REPLACE INTO quotes VALUES(?, ?, ?)", ['FND2387.NZ', date, price])
#con.commit()

# FUEMAV30.VN MAFM VN30 ETF
vnd = batdata.Vnd()
now = datetime.now()
date = now.strftime('%Y%m%d')
hist = vnd.hist("FUEMAV30", "close", date, date).json
for quote in hist:
    date = quote['tradingDate']
    price = quote['close'] * 1000
    con.execute("REPLACE INTO quotes VALUES('FUEMAV30.VN', ?, ?)",
                [date, price])
    con.commit()

con.close()
