#!/bin/bash
# SPDX-FileCopyrightText: 2022 Leroy Hopson <copyright@leroy.geek.nz>
#
# SPDX-License-Identifier: CC0-1.0
set -e
cd "$(dirname "$0")"

SYMBOLS=("FND20410.NZ" "FND1423.NZ" "FND2387.NZ" "FND40819.NZ" "FND79.NZ" "FND8205.NZ" "FND8207.NZ" "FUEMAV30.VN" "VAN1579.AU" "FND37626.NZ" "FND37632.NZ" "FND37633.NZ")

# Activate python virtual environment if available.
VENV_FILE=.venv/bin/activate
if test -f "$VENV_FILE"; then 
	. $VENV_FILE
fi

# Scrape quotes.
$(npm bin)/cypress run
python ./scrape.py

# Export latest quotes.
sqlite3 -header -json quotes.db "SELECT * FROM quotes;" > quotes/latest.json

# Import historical quotes.
for symbol in ${SYMBOLS[@]}; do
	(wget -O - https://lihop.github.io/quotes/${symbol}.json || echo "[]") | cat | sqlite-utils insert quotes.db quotes - --pk symbol --pk date --replace
done

# Re-import latest quotes.
cat quotes/latest.json | sqlite-utils insert quotes.db quotes - --pk symbol --pk date --replace

# Import Kernel quotes.
cat kernel_quotes.json | sqlite-utils insert quotes.db quotes - --pk symbol --pk date --replace
rm kernel_quotes.json

# Import more precise Kernel quotes.
cat kernel_quotes_precise.json | sqlite-utils insert quotes.db quotes - --pk symbol --pk date --replace
rm kernel_quotes_precise.json

# Re-export all quotes in JSON and CSV format.
for format in "json" "csv"; do
	for symbol in ${SYMBOLS[@]}; do
		sqlite3 -header -${format} quotes.db "SELECT * FROM quotes WHERE symbol='${symbol}';" > quotes/${symbol}.${format}
	done
done

# Format JSON files.
npx prettier --write quotes/*.json
