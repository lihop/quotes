// SPDX-FileCopyrightText: 2022 Leroy Hopson <copyright@leroy.geek.nz>
//
// SPDX-License-Identifier: CC0-1.0
const PORT = 2022;

const express = require("express");
const app = express();
const sqlite = require("better-sqlite3");
const path = require("path");
const db = new sqlite(path.resolve("quotes.db"), { fileMustExist: true });

app.get("/quotes/:symbol", (req, res, next) => {
  try {
    const data = db
      .prepare(`SELECT * FROM quotes WHERE symbol=?`)
      .all(req.params.symbol);
    res.json(data);
  } catch (err) {
    console.error(err.message);
    next(err);
  }
});

app.listen(PORT, () =>
  console.log(`App listening on http://localhost:${PORT}...`)
);
