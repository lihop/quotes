// SPDX-FileCopyrightText: 2022 Leroy Hopson <copyright@leroy.geek.nz>
//
// SPDX-License-Identifier: CC0-1.0
const HOLDINGS = [25445, 25870, 25871];
const FUNDS = {
  "Kernel Cash Plus Fund": "FND40600.NZ",
  "Kernel March 2027 NZ Bond Fund": "FND46943.NZ",
  "Kernel March 2029 NZ Bond Fund": "FND46944.NZ"
};

const concat = require("lodash/concat");
const get = require("lodash/get");
const keys = require("lodash/keys");
const moment = require("moment");

describe("", () => {
  it("", () => {
    cy.visit("https://portfolio.sharesight.com/users/sign_in");
    cy.get('input[id="user_email"]').type(Cypress.env("SHARESIGHT_USERNAME"), {
      delay: 0
    });
    cy.get('input[id="user_password"]').type(
      Cypress.env("SHARESIGHT_PASSWORD"),
      {
        delay: 0
      }
    );
    cy.get('input[type="submit"]').click();
    const allQuotes = [];
    HOLDINGS.forEach(holding => {
      cy.visit("https://portfolio.sharesight.com/");
      cy.get('[data-cy="HoldingName-' + holding + '"]').click();
      cy.intercept("https://*/charts/instrument_price_data.json?*").as(
        "charts-" + holding
      );
      cy.wait("@charts-" + holding, { timeout: 120000 }).then(interception => {
        cy.get('span[class^="DulledTextstyled"]').then(el => {
          const lastUpdated = moment(
            el.text().replace(" Updated at ", ""),
            "DD MMMM YYYY, h:mm A Z"
          );

          const dates = get(
            interception,
            "response.body.graph.xAxis.categories"
          );

          get(interception, "response.body.graph.series").forEach(fund => {
            if (keys(FUNDS).includes(fund.name)) {
              const quotes = get(fund, "data", [])
		.filter(quote => !!quote)
                .map((quote, i) => ({
                  symbol: FUNDS[fund.name],
                  date: moment(dates[i], "DD MMM YY"),
                  price: parseFloat(quote.y2)
                }))
                .filter(quote => quote.date.isSameOrBefore(lastUpdated))
                .map(quote => ({
                  ...quote,
                  date: quote.date.format("YYYY-MM-DD")
                }));
              quotes.forEach(quote => allQuotes.push(quote));
            }
          });
        });
      });
    });
    cy.writeFile("kernel_quotes.json", allQuotes);
  });
});
