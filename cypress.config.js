// SPDX-FileCopyrightText: none
// SPDX-License-Identifier: CC0-1.0
const { defineConfig } = require('cypress')

module.exports = defineConfig({
  e2e: {
    setupNodeEvents(on, config) {},
    supportFile: false,
  },
})
