// SPDX-FileCopyrightText: 2022 Leroy Hopson <copyright@leroy.geek.nz>
//
// SPDX-License-Identifier: CC0-1.0
const FUNDS = {
  "Kernel Cash Plus Fund": "FND40600.NZ"
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
    cy.get('[data-cy="HoldingName-25445"]').click();
    cy.intercept("https://*/charts/instrument_price_data.json?*").as("charts");
    cy.wait("@charts", { timeout: 120000 }).then(interception => {
      cy.get('span[class^="DulledTextstyled"]').then(el => {
        const lastUpdated = moment(
          el.text().replace(" Updated at ", ""),
          "DD MMMM YYYY, h:mm A Z"
        );

        const dates = get(interception, "response.body.graph.xAxis.categories");

        let allQuotes = [];
        get(interception, "response.body.graph.series").forEach(fund => {
          if (keys(FUNDS).includes(fund.name)) {
            const quotes = get(fund, "data", [])
              .map((quote, i) => ({
                symbol: FUNDS[fund.name],
                date: moment(dates[i], "DD MMM YY"), //.format("YYYY-MM-DD"),
                price: parseFloat(quote.y2)
              }))
              .filter(quote => quote.date.isSameOrBefore(lastUpdated))
              .map(quote => ({
                ...quote,
                date: quote.date.format("YYYY-MM-DD")
              }));
            allQuotes = concat(allQuotes, quotes);
          }
        });
        cy.writeFile("kernel_quotes.json", allQuotes);
      });
    });
  });
});
