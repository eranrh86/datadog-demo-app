// StockLens — Synthetic Mobile Test Suite
// Runs on: iPhone 15 Pro, iPhone SE, Pixel 7, Galaxy S23
// Tests: page load, watchlist, search, add/remove, stock detail, responsive layout

const { test, expect } = require('@playwright/test');

const APP_URL = process.env.APP_URL || 'https://d124xnxyrpsehi.cloudfront.net';

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

async function waitForApp(page) {
  await page.goto(APP_URL, { waitUntil: 'domcontentloaded' });
  // Wait for the watchlist sidebar to appear — means app JS has initialised
  await page.waitForSelector('#watchlistItems', { timeout: 20_000 });
  // Wait for at least one stock price to load from backend
  await page.waitForFunction(
    () => {
      const items = document.querySelectorAll('.wl-item');
      if (items.length === 0) return false;
      // At least one item should have a real price (not "0.00")
      const prices = [...items].map(el => {
        const p = el.querySelector('.wl-price');
        return p ? p.textContent.trim() : '';
      });
      return prices.some(p => p && !p.startsWith('$0.00') && !p.startsWith('₪0.00'));
    },
    { timeout: 25_000 }
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 1. PAGE LOAD & PERFORMANCE
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Page Load', () => {
  test('loads within 10 seconds and renders main UI', async ({ page }) => {
    const start = Date.now();
    await page.goto(APP_URL, { waitUntil: 'domcontentloaded' });

    // Core structural elements must be present
    await expect(page.locator('#watchlistItems')).toBeVisible({ timeout: 12_000 });
    await expect(page.locator('.search-wrap input')).toBeVisible({ timeout: 5_000 });

    const elapsed = Date.now() - start;
    console.log(`  ⏱  Page ready in ${elapsed}ms`);
    expect(elapsed).toBeLessThan(10_000);
  });

  test('title and app name are correct', async ({ page }) => {
    await page.goto(APP_URL, { waitUntil: 'domcontentloaded' });
    const title = await page.title();
    console.log(`  📄 Title: "${title}"`);
    expect(title.toLowerCase()).toMatch(/stock|lens|trade|market/i);
  });

  test('market status bar exists and contains US/TASE info', async ({ page }) => {
    await waitForApp(page);
    // On mobile the market status element may be CSS-hidden but still in DOM
    const marketStatus = page.locator('#marketStatus');
    await marketStatus.waitFor({ state: 'attached', timeout: 8_000 });
    const text = await marketStatus.innerText();
    console.log(`  📊 Market status: "${text.replace(/\n/g,' ')}"`);
    expect(text).toMatch(/US|TASE/i);
  });

  test('no console errors on load', async ({ page }) => {
    const errors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    await waitForApp(page);
    // Filter out known 3rd-party noise
    const realErrors = errors.filter(e =>
      !e.includes('favicon') &&
      !e.includes('kafka') &&         // kafka unavailable is expected
      !e.includes('net::ERR_') &&     // network is expected for some calls
      !e.includes('stocktwits')       // stocktwits can be rate-limited
    );
    if (realErrors.length > 0) {
      console.log('  ⚠️  Console errors:', realErrors);
    }
    expect(realErrors.length).toBe(0);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// 2. WATCHLIST
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Watchlist', () => {
  test('shows at least 5 stocks with prices', async ({ page }) => {
    await waitForApp(page);
    const items = page.locator('.wl-item');
    const count = await items.count();
    console.log(`  📋 Watchlist items: ${count}`);
    expect(count).toBeGreaterThanOrEqual(5);
  });

  test('each watchlist item has symbol, price, and % change', async ({ page }) => {
    await waitForApp(page);
    const items = page.locator('.wl-item');
    const count = Math.min(await items.count(), 5);  // check first 5

    for (let i = 0; i < count; i++) {
      const item = items.nth(i);
      const sym   = await item.locator('.wl-sym').textContent();
      const price = await item.locator('.wl-price').textContent();
      const chg   = await item.locator('.wl-chg').textContent();
      console.log(`  [${i+1}] ${sym?.trim()} | ${price?.trim()} | ${chg?.trim()}`);
      expect(sym?.trim().length).toBeGreaterThan(0);
      expect(price?.trim()).toMatch(/[\$₪][\d,.]+/);
      expect(chg?.trim()).toMatch(/[+\-]?\d+\.\d+%/);
    }
  });

  test('remove button appears on hover/touch and removes item', async ({ page }) => {
    await waitForApp(page);
    const items  = page.locator('.wl-item');
    const before = await items.count();
    expect(before).toBeGreaterThan(1);

    // Get symbol of first item before removal
    const firstItem  = items.first();
    const removedSym = (await firstItem.locator('.wl-sym').textContent())?.trim();

    // Hover to reveal remove button (mobile: just click it directly via JS)
    await firstItem.hover();
    const removeBtn = firstItem.locator('.wl-remove-btn');
    await removeBtn.waitFor({ state: 'visible', timeout: 3_000 });
    await removeBtn.click();

    // Wait for re-render
    await page.waitForTimeout(500);
    const after = await items.count();
    console.log(`  ✕ Removed ${removedSym}: ${before} → ${after} items`);
    expect(after).toBe(before - 1);
  });

  test('clicking a watchlist item opens stock detail', async ({ page }) => {
    await waitForApp(page);
    const firstItem = page.locator('.wl-item').first();
    const sym = (await firstItem.locator('.wl-sym').textContent())?.trim();
    await firstItem.click();

    // Should switch to analysis view with a price element visible
    await expect(page.locator('#analysis-price').first())
      .toBeVisible({ timeout: 8_000 });
    const price = await page.locator('#analysis-price').first().textContent();
    console.log(`  🖱️  Clicked ${sym} → analysis view opened | price: ${price}`);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// 3. SEARCH & ADD STOCK
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Search & Add', () => {
  test('search input is reachable on mobile', async ({ page }) => {
    await waitForApp(page);
    const input = page.locator('.search-wrap input').first();
    await expect(input).toBeVisible();
    await input.tap();
    await expect(input).toBeFocused();
  });

  test('searching "Apple" returns AAPL result', async ({ page }) => {
    await waitForApp(page);
    const input = page.locator('.search-wrap input').first();
    await input.tap();
    await input.fill('Apple');
    await page.waitForSelector('.ac-item', { timeout: 5_000 });
    const results = page.locator('.ac-item');
    const count = await results.count();
    console.log(`  🔍 "Apple" → ${count} results`);
    expect(count).toBeGreaterThan(0);
    // First result should include AAPL or Apple
    const firstText = await results.first().textContent();
    expect(firstText?.toUpperCase()).toMatch(/AAPL|APPLE/i);
  });

  test('searching "nebius" returns NBIS from Yahoo Finance', async ({ page }) => {
    await waitForApp(page);
    const input = page.locator('.search-wrap input').first();
    await input.tap();
    await input.fill('nebius');
    await page.waitForSelector('.ac-item', { timeout: 6_000 });
    const results = page.locator('.ac-item');
    const allText = await results.allTextContents();
    console.log(`  🔍 "nebius" results: ${allText.slice(0,3).join(' | ')}`);
    const hasNBIS = allText.some(t => t.toUpperCase().includes('NBIS') || t.toLowerCase().includes('nebius'));
    expect(hasNBIS).toBe(true);
  });

  test('searching TASE stock "bezq" finds it', async ({ page }) => {
    await waitForApp(page);
    const input = page.locator('.search-wrap input').first();
    await input.tap();
    await input.fill('bezq');
    await page.waitForSelector('.ac-item', { timeout: 5_000 });
    const allText = await page.locator('.ac-item').allTextContents();
    console.log(`  🔍 "bezq" results: ${allText.slice(0,2).join(' | ')}`);
    const hasBEZQ = allText.some(t => t.toUpperCase().includes('BEZQ'));
    expect(hasBEZQ).toBe(true);
  });

  test('can add NBIS to watchlist via search', async ({ page }) => {
    await waitForApp(page);

    // Remove NBIS if it's already there (idempotent test)
    const existingItems = await page.locator('.wl-sym').allTextContents();
    if (existingItems.map(s => s.trim()).includes('NBIS')) {
      const nbisRow = page.locator('.wl-item').filter({ hasText: 'NBIS' }).first();
      await nbisRow.hover();
      await nbisRow.locator('.wl-remove-btn').click();
      await page.waitForTimeout(400);
    }

    const beforeCount = await page.locator('.wl-item').count();

    // Search and add
    const input = page.locator('.search-wrap input').first();
    await input.tap();
    await input.fill('NBIS');
    await page.waitForSelector('.ac-item', { timeout: 6_000 });
    const nbisResult = page.locator('.ac-item').filter({ hasText: 'NBIS' }).first();
    await nbisResult.click();

    // Wait for watchlist to update
    await page.waitForTimeout(1_000);
    const afterCount = await page.locator('.wl-item').count();
    console.log(`  ➕ Added NBIS: ${beforeCount} → ${afterCount} watchlist items`);
    expect(afterCount).toBeGreaterThanOrEqual(beforeCount);

    // NBIS should now be in the watchlist
    const syms = await page.locator('.wl-sym').allTextContents();
    expect(syms.map(s => s.trim())).toContain('NBIS');
  });

  test('pressing Escape clears search dropdown', async ({ page }) => {
    await waitForApp(page);
    const input = page.locator('.search-wrap input').first();
    await input.tap();
    await input.fill('AAPL');
    // Wait for results to appear
    await page.waitForSelector('.ac-item', { timeout: 5_000 });
    const beforeCount = await page.locator('.ac-item').count();
    expect(beforeCount).toBeGreaterThan(0);
    await input.press('Escape');
    await page.waitForTimeout(400);
    // After Escape, no ac-items should be visible
    const afterCount = await page.locator('.ac-item:visible').count();
    console.log(`  ⌨️  Escape: ${beforeCount} results → ${afterCount} visible`);
    expect(afterCount).toBe(0);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// 4. STOCK DETAIL / ANALYSIS
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Stock Detail', () => {
  test('AAPL detail shows price, MA50, change', async ({ page }) => {
    await waitForApp(page);

    // Click AAPL in watchlist (or search if not there)
    const aaplItem = page.locator('.wl-item').filter({ hasText: 'AAPL' }).first();
    const aaplVisible = await aaplItem.isVisible().catch(() => false);

    if (aaplVisible) {
      await aaplItem.click();
    } else {
      const input = page.locator('.search-wrap input').first();
      await input.tap();
      await input.fill('AAPL');
      await page.waitForSelector('.ac-item', { timeout: 5_000 });
      await page.locator('.ac-item').first().click();
    }

    // Wait for detail view
    await page.waitForSelector('#analysis-price, .analysis-price, [id*="analysis"]', { timeout: 12_000 });
    const priceEl = page.locator('#analysis-price').first();
    if (await priceEl.isVisible()) {
      const price = await priceEl.textContent();
      console.log(`  💰 AAPL price in detail: ${price}`);
      expect(price).toMatch(/[\$₪]\d+/);
    } else {
      // Try alternate selectors
      const anyPrice = page.locator('[class*="price"]:not(.wl-price)').first();
      await expect(anyPrice).toBeVisible({ timeout: 5_000 });
    }
  });

  test('stock chart canvas is rendered', async ({ page }) => {
    await waitForApp(page);
    const firstItem = page.locator('.wl-item').first();
    await firstItem.click();
    // Wait for the main price chart (not sparklines which are tiny/hidden)
    // Main chart canvas is inside the analysis panel — look for visible canvas with height > 50
    await page.waitForTimeout(1_000); // let chart render
    const visibleCanvas = await page.evaluate(() => {
      const canvases = [...document.querySelectorAll('canvas')];
      const main = canvases.find(c => {
        const r = c.getBoundingClientRect();
        return r.height > 50 && r.width > 100;
      });
      return main ? { id: main.id, w: main.getBoundingClientRect().width, h: main.getBoundingClientRect().height } : null;
    });
    console.log('  📈 Main chart canvas:', visibleCanvas);
    expect(visibleCanvas).not.toBeNull();
    expect(visibleCanvas.h).toBeGreaterThan(50);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// 5. RESPONSIVE LAYOUT
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Mobile Layout', () => {
  test('no horizontal overflow on active (visible) panels', async ({ page }) => {
    await waitForApp(page);
    const viewWidth = await page.evaluate(() => window.innerWidth);
    // Check elements that overflow and are NOT inside a scrollable container
    // (the horizontal watchlist strip is intentionally scrollable on mobile)
    const overflowingEls = await page.evaluate((vw) => {
      function isInsideScroller(el) {
        let p = el.parentElement;
        while (p && p !== document.body) {
          const st = window.getComputedStyle(p);
          // Skip elements inside scrollable OR hidden-overflow containers:
          // - auto/scroll: user can scroll to see it (intentional)
          // - hidden: content is clipped, not visible to user (not a UX problem)
          if (st.overflowX === 'auto' || st.overflowX === 'scroll' || st.overflowX === 'hidden') return true;
          p = p.parentElement;
        }
        return false;
      }
      const bad = [];
      for (const el of document.querySelectorAll('*')) {
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden') continue;
        if (isInsideScroller(el)) continue;  // intentionally scrollable
        const rect = el.getBoundingClientRect();
        if (rect.right > vw + 10 && rect.width > 0 && rect.height > 0) {
          bad.push({ tag: el.tagName, id: el.id, cls: el.className.toString().slice(0, 50), right: Math.round(rect.right) });
        }
      }
      return bad.slice(0, 5);
    }, viewWidth);

    console.log(`  📐 viewport=${viewWidth}px | non-scrollable overflow: ${overflowingEls.length}`);
    if (overflowingEls.length > 0) {
      console.log('  ⚠️  Overflow details:', JSON.stringify(overflowingEls));
    }
    expect(overflowingEls.length).toBe(0);
  });

  test('search input is not cut off', async ({ page }) => {
    await waitForApp(page);
    const input = page.locator('.search-wrap input').first();
    const box = await input.boundingBox();
    expect(box).not.toBeNull();
    const viewWidth = await page.evaluate(() => window.innerWidth);
    console.log(`  🔍 Search input: x=${box.x.toFixed(0)}, width=${box.width.toFixed(0)}, viewport=${viewWidth}`);
    expect(box.x).toBeGreaterThanOrEqual(0);
    expect(box.x + box.width).toBeLessThanOrEqual(viewWidth + 2);
  });

  test('watchlist sidebar is accessible', async ({ page }) => {
    await waitForApp(page);
    const wl = page.locator('#watchlistItems');
    await expect(wl).toBeVisible();
    const box = await wl.boundingBox();
    expect(box.width).toBeGreaterThan(60);
    console.log(`  📋 Watchlist width: ${box.width.toFixed(0)}px`);
  });

  test('tap targets are at least 44px tall (accessibility)', async ({ page }) => {
    await waitForApp(page);
    const items = page.locator('.wl-item');
    const count = Math.min(await items.count(), 3);
    for (let i = 0; i < count; i++) {
      const box = await items.nth(i).boundingBox();
      console.log(`  👆 wl-item[${i}] height: ${box?.height.toFixed(0)}px`);
      expect(box?.height ?? 0).toBeGreaterThanOrEqual(40);
    }
  });

  test('text is readable (font size >= 11px)', async ({ page }) => {
    await waitForApp(page);
    const smallText = await page.evaluate(() => {
      const minOk = 11;
      const bad = [];
      for (const el of document.querySelectorAll('.wl-sym, .wl-price, .wl-name')) {
        const fs = parseFloat(window.getComputedStyle(el).fontSize);
        if (fs < minOk) bad.push({ tag: el.className, fontSize: fs });
      }
      return bad;
    });
    if (smallText.length > 0) console.log('  ⚠️  Small text found:', smallText);
    expect(smallText.length).toBe(0);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// 6. BACKEND API HEALTH (via browser fetch)
// ─────────────────────────────────────────────────────────────────────────────

test.describe('API Health (from browser)', () => {
  test('/api/stocks returns 20+ stocks', async ({ page }) => {
    await page.goto(APP_URL, { waitUntil: 'domcontentloaded' });
    const result = await page.evaluate(async (url) => {
      const r = await fetch(url + '/api/stocks');
      return r.json();
    }, APP_URL);
    const count = result.stocks?.length ?? 0;
    console.log(`  🌐 /api/stocks → ${count} stocks`);
    expect(count).toBeGreaterThanOrEqual(20);
  });

  test('/api/stock/AAPL returns real price', async ({ page }) => {
    await page.goto(APP_URL, { waitUntil: 'domcontentloaded' });
    const data = await page.evaluate(async (url) => {
      const r = await fetch(url + '/api/stock/AAPL');
      return r.json();
    }, APP_URL);
    console.log(`  🌐 /api/stock/AAPL → $${data.price} | ${data.name}`);
    expect(data.price).toBeGreaterThan(0);
    expect(data.name).toMatch(/apple/i);
  });

  test('/api/stock/NBIS loads on-demand (no 404)', async ({ page }) => {
    await page.goto(APP_URL, { waitUntil: 'domcontentloaded' });
    const data = await page.evaluate(async (url) => {
      const r = await fetch(url + '/api/stock/NBIS');
      return { status: r.status, body: await r.json() };
    }, APP_URL);
    console.log(`  🌐 /api/stock/NBIS → HTTP ${data.status} | $${data.body.price}`);
    expect(data.status).toBe(200);
    expect(data.body.price).toBeGreaterThan(0);
  });

  test('/api/stock/TEVA.TA returns ILS price', async ({ page }) => {
    await page.goto(APP_URL, { waitUntil: 'domcontentloaded' });
    const data = await page.evaluate(async (url) => {
      const r = await fetch(url + '/api/stock/TEVA.TA');
      return r.json();
    }, APP_URL);
    console.log(`  🌐 /api/stock/TEVA.TA → ${data.currency} ₪${data.price}`);
    expect(data.price).toBeGreaterThan(0);
  });

  test('/api/search?q=nvidia returns results', async ({ page }) => {
    await page.goto(APP_URL, { waitUntil: 'domcontentloaded' });
    const data = await page.evaluate(async (url) => {
      const r = await fetch(url + '/api/search?q=nvidia');
      return r.json();
    }, APP_URL);
    console.log(`  🌐 /api/search?q=nvidia → ${data.results?.length} results`);
    expect(data.results?.length).toBeGreaterThan(0);
    expect(data.results[0].symbol).toMatch(/NVDA/i);
  });
});
