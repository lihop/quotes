#!/bin/python
# SPDX-FileCopyrightText: 2022 Leroy Hopson <copyright@leroy.nix.nz>
#
# SPDX-License-Identifier: CC0-1.0

import requests
import json
import csv
import sqlite3
import dateutil.parser
import pandas as pd
import math
import warnings
from bs4 import BeautifulSoup as bs
from collections import deque
from datetime import datetime, timedelta
from io import StringIO
from requests.adapters import HTTPAdapter, Retry
from tabula import read_pdf
from urllib.error import HTTPError

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36'
HEADERS = {'User-Agent': USER_AGENT, 'Accept-Langage': 'en-NZ'}

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
    "https://www.fundrock.com/fundrock-new-zealand/frnz-documents-and-reporting/",
    headers=HEADERS)
table = pd.read_html(res.content)[2]
for fund in table.iterrows():
    if fund[1][0] != "Foundation Series Total World Fund":
        continue
    price = fund[1][2]
    # Date formatting is inconsistent, so parse in multiple formats and pick
    # whichever is closest to today.
    raw_date = fund[1][1].replace('-', '/')
    try:
        us_date = datetime.strptime(raw_date, '%m/%d/%Y')
    except ValueError:
        us_date = None
    try:
        non_us_date = datetime.strptime(raw_date, '%d/%m/%Y')
    except ValueError:
        non_us_date = None
    today = datetime.today()
    if us_date and non_us_date:
        date = us_date if abs(
            (us_date -
             today).days) < abs(
            (non_us_date -
             today).days) else non_us_date
    else:
        date = (us_date if us_date else non_us_date)
    assert date and price, "Could not determine date and/or price."
    con.execute("REPLACE INTO quotes VALUES('FND40819.NZ', ?, ?)",
                [date.strftime('%Y-%m-%d'), price])
    con.commit()

# FND1423.NZ Harbour NZ Index Shares Fund
res = session.get("https://www.harbourasset.co.nz/our-funds/index-shares/",
                  headers=HEADERS, timeout=120)
table = pd.read_html(StringIO(res.text))[2]
date = table["Date"][0]
price = table["Unit Price NZD"][0]
assert date and price, "Could not determine date and/or price."
con.execute("REPLACE INTO quotes VALUES('FND1423.NZ', ?, ?)", [date, price])
con.commit()

# FUEMAV30.VN MAFM VN30 ETF
res = session.get(
    "https://finance.vietstock.vn/FUEMAV30-quy-etf-mafm-vn30.htm",
    headers=HEADERS)
table_html = bs(res.text, 'html.parser').find(
    'table', {'id': 'stock-transactions'})
table = pd.read_html(StringIO(str(table_html)))[0]
for row in table.iterrows():
    date_str = row[1]["Ngày"]
    date = datetime.strptime(date_str, '%d/%m/%Y').strftime('%Y-%m-%d')
    price = row[1]["Giá đóng cửa"]
    assert date and price, "Could not determine date and/or price."
    con.execute("REPLACE INTO quotes VALUES('FUEMAV30.VN', ?, ?)",
                [date, price])
    con.commit()

# FUEVN100.VN VinaCapital VN100 EETF
res = session.get(
    "https://finance.vietstock.vn/FUEVN100-vn100-etf.htm",
    headers=HEADERS)
table_html = bs(res.text, 'html.parser').find(
    'table', {'id': 'stock-transactions'})
table = pd.read_html(StringIO(str(table_html)))[0]
for row in table.iterrows():
    date_str = row[1]["Ngày"]
    date = datetime.strptime(date_str, '%d/%m/%Y').strftime('%Y-%m-%d')
    price = row[1]["Giá đóng cửa"]
    assert date and price, "Could not determine date and/or price."
    con.execute("REPLACE INTO quotes VALUES('FUEVN100.VN', ?, ?)",
                [date, price])
    con.commit()

# FND78.NZ Mercer Macquarie NZ Cash Fund
res = session.get(
    "https://digital.feprecisionplus.com/mercer-nz/en-au/MercerNZ/DownloadTool/GetPriceHistory?jsonString=%7B%22GrsProjectId%22%3A%2217200147%22%2C%22ProjectName%22%3A%22mercer-nz%22%2C%22ToolId%22%3A16%2C%22LanguageId%22%3A%227%22%2C%22LanguageCode%22%3A%22en-au%22%2C%22UnitHistoryFilters%22%3A%7B%22CitiCode%22%3A%22XOCV%22%2C%22Universe%22%3A%22GL%22%2C%22TypeCode%22%3A%22FGL%3AXOCV%22%2C%22BaseCurrency%22%3A%22NZD%22%2C%22PriceType%22%3A2%2C%22TimePeriod%22%3A%221%22%7D%7D", headers=HEADERS)
data = res.json()
for item in data['DataList']:
    price = item['Price']['Price']['Amount']
    date = dateutil.parser.parse(
        item['Price']['PriceDate']).strftime('%Y-%m-%d')
    assert date and price, "Could not determine date and/or price."
    con.execute("REPLACE INTO quotes VALUES('FND78.NZ', ?, ?)",
                [date, price])
    con.commit()

# FND452.NZ UniSaver Growth
res = session.get(
    "https://www.unisaver.co.nz/investments/latest-returns/#compare",
    headers=HEADERS)
table = pd.read_html(StringIO(res.text))[0]
date = datetime.strptime(
    table.columns[1], 'Current price %d/%m/%Y').strftime('%Y-%m-%d')
price = float(table[table.columns[1]][1].replace('$', ''))
assert date and price, "Could not determine date and/or price."
con.execute("REPLACE INTO quotes VALUES('FND452.NZ', ?, ?)", [date, price])
con.commit()
headers = {'Origin': 'https://www.youraccountonline.com'}
data = {
    "Request": {
        "Resource": "Superfacts",
        "Action": "GetPubUnitPriceHistory",
        "ParamData": {
            "UPHistStartDate": (
                datetime.now() -
                timedelta(
                    days=7)).strftime("%d/%m/%Y"),
            "FullHistory": True,
            "ClientCode": "NZUSS",
            "DatabaseCode": "UNINZ"}}}
res = session.post(
    "https://secure.superfacts.com/sfsvc/v5/jsonutilsvc/JSONUtilityService.svc/ProcessPubRequest",
    headers=(
        HEADERS | headers),
    data=json.dumps(data))
res.encoding = 'utf-8-sig'
unit_prices = res.json()['ResultData']['UnitPriceData']['UnitPrices']
for unit_price in unit_prices:
    if unit_price['Code'] == 'USGROW_DEF':
        date = datetime.strptime(
            unit_price['EffectiveStartDate'],
            '%d/%m/%Y').strftime('%Y-%m-%d')
        price = float(unit_price['ExitPrice'])
        assert date and price, "Could not determine date and/or price."
        con.execute(
            "REPLACE INTO quotes VALUES('FND452.NZ', ?, ?)", [
                date, price])
        con.commit()

# FND8205.NZ Mercer NZ Shares Passive Fund
res = session.get(
    "https://digital.feprecisionplus.com/mercer-nz/en-au/MercerNZ/DownloadTool/GetPriceHistory?jsonString=%7B%22GrsProjectId%22%3A%2217200147%22%2C%22ProjectName%22%3A%22mercer-nz%22%2C%22ToolId%22%3A16%2C%22LanguageId%22%3A%227%22%2C%22LanguageCode%22%3A%22en-au%22%2C%22UnitHistoryFilters%22%3A%7B%22CitiCode%22%3A%22WTCZ%22%2C%22Universe%22%3A%22GL%22%2C%22TypeCode%22%3A%22FGL%3AWTCZ%22%2C%22BaseCurrency%22%3A%22NZD%22%2C%22PriceType%22%3A2%2C%22TimePeriod%22%3A%221%22%7D%7D", headers=HEADERS)
data = res.json()
for item in data['DataList']:
    price = item['Price']['Price']['Amount']
    date = dateutil.parser.parse(
        item['Price']['PriceDate']).strftime('%Y-%m-%d')
    assert date and price, "Could not determine date and/or price."
    con.execute("REPLACE INTO quotes VALUES('FND8205.NZ', ?, ?)",
                [date, price])
    con.commit()

# FND43092.NZ Hedeged Global Bond Fund
res = session.get(
    "https://simplicity.kiwi/api/download_prices?fund_name=INVHedged%20Global%20Bond",
    headers=HEADERS)
data = csv.reader(res.text.splitlines())
header = next(data)
for row in deque(data, 7):
    date = datetime.strptime(row[0], '%d-%m-%Y').strftime('%Y-%m-%d')
    price = row[1]
    assert date and price, "Could not determine date and/or price."
    con.execute("REPLACE INTO quotes VALUES('FND43092.NZ', ?, ?)",
                [date, price])
    con.commit()

# FND9381.NZ NZ Bond Fund
res = session.get(
    "https://simplicity.kiwi/api/download_prices?fund_name=INVNZ%20Bond",
    headers=HEADERS)
data = csv.reader(res.text.splitlines())
header = next(data)
for row in deque(data, 7):
    date = datetime.strptime(row[0], '%d-%m-%Y').strftime('%Y-%m-%d')
    price = row[1]
    assert date and price, "Could not determine date and/or price."
    con.execute("REPLACE INTO quotes VALUES('FND9381.NZ', ?, ?)",
                [date, price])
    con.commit()

con.close()
