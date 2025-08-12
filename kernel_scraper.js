// SPDX-FileCopyrightText: 2025 Leroy Hopson <copyright@leroy.geek.nz>
//
// SPDX-License-Identifier: CC0-1.0

const { chromium } = require('playwright');
const fs = require('fs').promises;
const moment = require('moment');
const path = require('path');

const FUNDS = {
  "Cash Plus": "FND40600.NZ",
  "March 2027 NZ Bond Fund": "FND46943.NZ", 
  "March 2029 NZ Bond Fund": "FND46944.NZ"
};

const FUND_SLUGS = {
  "Cash Plus": "kernel-cash-plus-fund",
  "March 2027 NZ Bond Fund": "kernel-march-2027-nz-bond-fund",
  "March 2029 NZ Bond Fund": "kernel-march-2029-nz-bond-fund"
};

const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

async function getKernelQuotes() {
  console.log('🚀 Starting automated Kernel quotes collection...');
  
  // Try to use system chromium if Playwright browsers aren't installed
  let launchOptions = { 
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-web-security',
      '--disable-features=VizDisplayCompositor',
      '--disable-crash-reporter'
    ]
  };
  
  // In nix environment or when playwright browsers not installed, use system chromium
  const fs = require('fs');
  if (fs.existsSync('/run/current-system/sw/bin/chromium')) {
    launchOptions.executablePath = '/run/current-system/sw/bin/chromium';
    console.log('🔧 Using system chromium from nix');
  }
  
  const browser = await chromium.launch(launchOptions);

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    locale: 'en-NZ',
    timezoneId: 'Pacific/Auckland',
    extraHTTPHeaders: {
      'Accept-Language': 'en-NZ,en-US;q=0.9,en;q=0.8'
    }
  });

  const page = await context.newPage();

  try {
    const username = process.env.KERNEL_USERNAME;
    const password = process.env.KERNEL_PASSWORD;
    
    if (!username || !password) {
      throw new Error('Please set KERNEL_USERNAME and KERNEL_PASSWORD environment variables');
    }

    console.log('🔐 Navigating to login page...');
    
    // Navigate with realistic behavior
    await page.goto('https://www.kernelwealth.co.nz/', { waitUntil: 'networkidle' });
    await delay(2000);
    
    // Go to login page
    await page.goto('https://my.kernelwealth.co.nz/auth/login', { waitUntil: 'networkidle' });
    await delay(3000);
    
    // Check for security checkpoint
    const bodyText = await page.textContent('body');
    console.log('Page loaded, checking for security blocks...');
    
    if (bodyText.includes('Failed to verify') || bodyText.includes('Security Checkpoint') || bodyText.includes('Vercel')) {
      console.log('🚨 Security checkpoint detected');
      
      // Try to wait it out or handle it
      await delay(10000);
      await page.reload({ waitUntil: 'networkidle' });
      await delay(5000);
      
      const retryBodyText = await page.textContent('body');
      if (retryBodyText.includes('Failed to verify') || retryBodyText.includes('Security Checkpoint')) {
        throw new Error('Security checkpoint blocking access - manual intervention may be required');
      }
    }
    
    console.log('✅ No security blocks detected, proceeding with login...');
    
    // Wait for and fill login form
    await page.waitForSelector('input[type="email"], input[name="username"], input:first-of-type', { timeout: 10000 });
    
    const emailInput = page.locator('input').first();
    await emailInput.click();
    await delay(1000);
    await emailInput.fill(username);
    await delay(1500);
    
    const passwordInput = page.locator('input[type="password"], input:nth-of-type(2)');
    await passwordInput.click();
    await delay(500);
    await passwordInput.fill(password);
    await delay(1000);
    
    // Submit login
    const submitButton = page.getByRole('button', { name: /log in/i });
    await submitButton.click();
    console.log('📤 Login form submitted');
    
    // Wait for login to complete
    await page.waitForURL(url => !url.includes('/auth/login'), { timeout: 20000 });
    await delay(3000);
    
    console.log('✅ Login successful!');
    
    // Capture authentication token
    let authToken = null;
    
    page.on('request', request => {
      const authHeader = request.headers()['authorization'];
      if (authHeader && authHeader.startsWith('Bearer ')) {
        authToken = authHeader;
        console.log('🔑 Captured auth token');
      }
    });
    
    // Navigate to trigger API call
    await page.goto('https://my.kernelwealth.co.nz/invest/kernel-cash-plus-fund', { 
      waitUntil: 'networkidle' 
    });
    await delay(5000);
    
    if (!authToken) {
      throw new Error('Failed to capture authentication token');
    }
    
    console.log('🔑 Authentication token captured, fetching fund data...');
    
    // Fetch all fund data using the API
    const allQuotes = [];
    
    for (const [fundName, fundSlug] of Object.entries(FUND_SLUGS)) {
      try {
        console.log(`📊 Fetching ${fundName}...`);
        
        const response = await page.evaluate(async ({ authToken, fundSlug }) => {
          const res = await fetch(`https://chelly.kernelwealth.co.nz/api/Marketplace/fund/${fundSlug}`, {
            headers: {
              'Authorization': authToken,
              'Accept': 'application/json, text/plain, */*',
              'Referer': 'https://my.kernelwealth.co.nz/',
              'Origin': 'https://my.kernelwealth.co.nz'
            }
          });
          
          if (!res.ok) {
            throw new Error(`HTTP ${res.status}`);
          }
          
          return await res.json();
        }, { authToken, fundSlug });
        
        if (response && response.fundPosition && response.fundPosition.fundPriceHistory) {
          const priceHistory = response.fundPosition.fundPriceHistory;
          console.log(`📈 Found ${priceHistory.length} price records for ${fundName}`);
          
          const quotes = priceHistory.map(quote => ({
            symbol: FUNDS[fundName],
            date: moment(quote.date, "MM/DD/YYYY HH:mm:ss").format("YYYY-MM-DD"),
            price: parseFloat((quote.price * 0.01).toFixed(2))
          }));
          
          allQuotes.push(...quotes);
        } else {
          console.log(`⚠️ No price history found for ${fundName}`);
        }
        
        await delay(2000); // Be polite to the API
        
      } catch (error) {
        console.error(`❌ Error fetching ${fundName}:`, error.message);
      }
    }
    
    // Save results
    await fs.writeFile('kernel_quotes.json', JSON.stringify(allQuotes, null, 2));
    console.log(`🎉 Success! Collected ${allQuotes.length} total quotes`);
    console.log('📄 Results saved to kernel_quotes.json');
    
    return allQuotes;
    
  } catch (error) {
    console.error('💥 Error:', error.message);
    
    // Take screenshot for debugging
    try {
      await page.screenshot({ path: 'error-screenshot.png', fullPage: true });
      console.log('📸 Error screenshot saved');
    } catch (screenshotError) {
      console.log('Could not take screenshot:', screenshotError.message);
    }
    
    throw error;
  } finally {
    await browser.close();
  }
}

if (require.main === module) {
  getKernelQuotes().catch(error => {
    console.error('Script failed:', error);
    process.exit(1);
  });
}

module.exports = { getKernelQuotes };