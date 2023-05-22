// SPDX-FileCopyrightText: 2022 Leroy Hopson <copyright@leroy.geek.nz>
//
// SPDX-License-Identifier: CC0-1.0
const FUNDS = {
  "NZ 20": "FND37626.NZ",
  "Global 100": "FND37632.NZ",
  "S&P 500": "FND37633.NZ"
};

const concat = require("lodash/concat");
const get = require("lodash/get");
const keys = require("lodash/keys");
const moment = require("moment");

describe("", () => {
  it("", () => {
    cy.visit("https://my.kernelwealth.co.nz/auth/login");
    cy.get('input[name="username"]').type(Cypress.env("KERNEL_USERNAME"), {
      delay: 0
    });
    cy.get('input[name="password"]').type(Cypress.env("KERNEL_PASSWORD"), {
      delay: 0
    });
    cy.get('button[type="submit"]').click();
    cy.intercept("/api/*").as("api");
    cy.wait("@api", { timeout: 60000 });
    cy.get('a[href="/invest/"]', { timeout: 60000 }).click({ force: true });
    cy.visit("https://my.kernelwealth.co.nz/invest/marketplace");
    cy.intercept("https://chelly.kernelwealth.co.nz/api/Marketplace").as(
      "Marketplace"
    );
    cy.wait("@Marketplace", { timeout: 60000 }).then(interception => {
      let allQuotes = [];
      get(interception, "response.body.funds").forEach(fund => {
        if (keys(FUNDS).includes(fund.name)) {
          const quotes = get(fund, "fundPriceHistory", []).map(quote => ({
            symbol: FUNDS[fund.name],
            date: moment(quote.date, "MM/DD/YYYY HH:mm:ss").format(
              "YYYY-MM-DD"
            ),
            price: parseFloat((quote.price * 0.01).toFixed(2))
          }));
          allQuotes = concat(allQuotes, quotes);
        }
      });
      cy.writeFile("kernel_quotes.json", allQuotes);
    });
  });
});
