#!/bin/python
# SPDX-FileCopyrightText: 2022 Leroy Hopson <copyright@leroy.nix.nz>
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
    "https://www.fundrock.com/fundrock-new-zealand/frnz-documents-and-reporting/", headers=HEADERS)
table = pd.read_html(res.content)[2]
for fund in table.iterrows():
    if fund[1][0] != "Foundation Series Total World Fund":
        continue
    price = fund[1][2]
    date = fund[1][1]
    assert date and price, "Could not determine date and/or price."
    con.execute("REPLACE INTO quotes VALUES('FND40819.NZ', ?, ?)",
                [date, price])
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
    "https://finance.vietstock.vn/FUEMAV30-quy-etf-mafm-vn30.htm", headers=HEADERS)
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

# FND78.NZ Mercer Macquarie NZ Cash Fund
res = session.get(
    "https://digital.feprecisionplus.com/mercer-nz/en-au/MercerNZ/DownloadTool/GetPriceHistory?jsonString=%7B%22GrsProjectId%22%3A%2217200147%22%2C%22ProjectName%22%3A%22mercer-nz%22%2C%22ToolId%22%3A16%2C%22LanguageId%22%3A%227%22%2C%22LanguageCode%22%3A%22en-au%22%2C%22UnitHistoryFilters%22%3A%7B%22CitiCode%22%3A%22XOCV%22%2C%22Universe%22%3A%22GL%22%2C%22TypeCode%22%3A%22FGL%3AXOCV%22%2C%22BaseCurrency%22%3A%22NZD%22%2C%22PriceType%22%3A2%2C%22TimePeriod%22%3A%221%22%7D%7D", headers=HEADERS)
data = res.json()
for item in data['DataList']:
    price = item['Price']['Price']['Amount']
    date = dateutil.parser.parse(item['Price']['PriceDate']).strftime('%Y-%m-%d')
    assert date and price, "Could not determine date and/or price."
    con.execute("REPLACE INTO quotes VALUES('FND78.NZ', ?, ?)",
                [date, price])
    con.commit()

# FND452.NZ UniSaver Growth
custom_fund_headers = {
    'User-Agent': USER_AGENT,
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Origin': 'https://www.youraccountonline.com',
}

custom_fund_data = json.dumps({
    "Request": {
        "SvcToken": "null",
        "Resource": "Superfacts",
        "Action": "GetPubUnitPriceHistory",
        "ParamData": {
            "UPHistStartDate": "",
            "FullHistory": False,
            "ClientCode": "NZUSS",
            "DatabaseCode": "UNINZ"
        }
    }
})

res = session.post(
    "https://secure.superfacts.com/sfsvc/v5/jsonutilsvc/JSONUtilityService.svc/ProcessPubRequest",
    headers=custom_fund_headers, data=custom_fund_data)

# Remove the UTF-8 BOM if it's present
res_text = res.content.decode('utf-8-sig')

data = json.loads(res_text)
unit_prices = data['ResultData']['UnitPriceData']['UnitPrices']
for unit_price in unit_prices:
    if unit_price['Code'] == "USGROW_DEF":
        price = unit_price['CurExitPrice']
        break

date = data['ResultData']['UnitPriceData']['UPHistEndDate']
date_formatted = datetime.strptime(date, '%d/%m/%Y').strftime('%Y-%m-%d')

assert date_formatted and price, "Could not determine date and/or price for FND452.NZ."
cur.execute("REPLACE INTO quotes VALUES('FND452.NZ', ?, ?)", [date_formatted, price])
con.commit()

con.close()
