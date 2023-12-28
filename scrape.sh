#!/bin/bash
#
# SPDX-FileCopyrightText: 2022 Leroy Hopson <copyright@leroy.nix.nz>
# SPDX-License-Identifier: CC0-1.0
set -e
cd "$(dirname "$0")"

SYMBOLS=("FND40819.NZ" "VAN1579.AU" "FND1423.NZ" "FUEMAV30.VN")

# Activate python virtual environment if available.
VENV_FILE=.venv/bin/activate
if test -f "$VENV_FILE"; then 
	. $VENV_FILE
fi

# Scrape quotes.
python ./scrape.py

# Export latest quotes.
sqlite3 -header -json quotes.db "SELECT * FROM quotes;" > quotes/latest.json

# Import historical quotes.
for symbol in ${SYMBOLS[@]}; do
	(wget -O - https://lihop.github.io/quotes/${symbol}.json || echo "[]") | cat | sqlite-utils insert quotes.db quotes - --pk symbol --pk date --replace
done

# Re-import latest quotes.
cat quotes/latest.json | sqlite-utils insert quotes.db quotes - --pk symbol --pk date --replace

# Re-export all quotes in JSON and CSV format.
for format in "json" "csv"; do
	for symbol in ${SYMBOLS[@]}; do
		sqlite3 -header -${format} quotes.db "SELECT * FROM quotes WHERE symbol='${symbol}';" > quotes/${symbol}.${format}
	done
done

# Format JSON files.
npx prettier --write quotes/*.json
