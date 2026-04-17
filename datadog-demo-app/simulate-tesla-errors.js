const { chromium } = require('playwright');

const APP_URL = 'https://d124xnxyrpsehi.cloudfront.net';
const ROUNDS = 8; // click TSLA 8 times to blast error events

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  });
  const page = await context.newPage();

  // Capture console errors to confirm forwarding
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log(`[BROWSER ERROR] ${msg.text()}`);
    }
  });

  console.log(`Navigating to ${APP_URL} ...`);
  await page.goto(APP_URL, { waitUntil: 'networkidle', timeout: 45000 });
  await page.waitForTimeout(3000); // let RUM SDK init

  // Check RUM is loaded
  const rumLoaded = await page.evaluate(() => !!window.DD_RUM);
  console.log(`RUM SDK loaded: ${rumLoaded}`);

  for (let i = 1; i <= ROUNDS; i++) {
    console.log(`\n--- Round ${i}/${ROUNDS} ---`);

    // Try to find and click TSLA in the watchlist or search
    try {
      // First try clicking a TSLA watchlist item
      const tslaEl = await page.$('[data-symbol="TSLA"], [data-ticker="TSLA"]');
      if (tslaEl) {
        await tslaEl.click();
        console.log('Clicked TSLA watchlist item');
      } else {
        // Fall back: call fetchStockDetail directly via JS
        const result = await page.evaluate(() => {
          return new Promise((resolve) => {
            if (typeof fetchStockDetail === 'function') {
              fetchStockDetail('TSLA', (data) => resolve({ method: 'fetchStockDetail', data: !!data }));
            } else if (typeof loadStock === 'function') {
              loadStock('TSLA');
              resolve({ method: 'loadStock' });
            } else {
              // Directly inject the error via RUM
              if (window.DD_RUM) {
                const tslaError = new Error('Tesla data pipeline failure: real-time feed disconnected (HTTP 503)');
                tslaError.name = 'TeslaDataError';
                window.DD_RUM.addError(tslaError, {
                  stock_symbol: 'TSLA', error_type: 'api_failure', http_status: 503,
                  source: 'simulate-script', round: arguments[0],
                });
                window.DD_RUM.addAction('tesla_error_triggered', { stock_symbol: 'TSLA', error_code: 503, demo: true });
                console.error('[StockLens] TSLA feed disconnected — HTTP 503: real-time data pipeline failure', {
                  symbol: 'TSLA', http_code: 503, source: 'simulate-script',
                });
                resolve({ method: 'direct_rum', rumLoaded: true });
              } else {
                resolve({ method: 'no_rum' });
              }
            }
          });
        }, i);
        console.log(`Result: ${JSON.stringify(result)}`);
      }
    } catch (err) {
      // Direct injection as fallback
      const injected = await page.evaluate((round) => {
        if (window.DD_RUM) {
          const tslaError = new Error('Tesla data pipeline failure: real-time feed disconnected (HTTP 503)');
          tslaError.name = 'TeslaDataError';
          window.DD_RUM.addError(tslaError, {
            stock_symbol: 'TSLA', error_type: 'api_failure', http_status: 503,
            source: 'simulate-script', round: round,
          });
          window.DD_RUM.addAction('tesla_error_triggered', { stock_symbol: 'TSLA', error_code: 503, demo: true, round: round });
          console.error('[StockLens] TSLA feed disconnected — HTTP 503: real-time data pipeline failure', {
            symbol: 'TSLA', http_code: 503, source: 'simulate-script', round: round,
          });
          return { injected: true, round: round };
        }
        return { injected: false };
      }, i);
      console.log(`Direct injection: ${JSON.stringify(injected)}`);
    }

    await page.waitForTimeout(2000); // give RUM time to flush
  }

  // Final flush — navigate away and back
  console.log('\nFlushing RUM events...');
  await page.waitForTimeout(5000);

  const finalStats = await page.evaluate(() => ({
    rumLoaded: !!window.DD_RUM,
    sessionId: window.DD_RUM ? window.DD_RUM.getInternalContext?.()?.session_id : null,
  }));
  console.log(`Final RUM state: ${JSON.stringify(finalStats)}`);

  await browser.close();
  console.log('\nSimulation complete. Tesla errors fired and sent to Datadog RUM.');
})();
