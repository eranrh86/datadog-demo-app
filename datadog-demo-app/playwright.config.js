// @ts-check
const { defineConfig, devices } = require('@playwright/test');

const APP_URL = process.env.APP_URL || 'https://d124xnxyrpsehi.cloudfront.net';

module.exports = defineConfig({
  testDir: './tests/mobile',
  timeout: 45_000,
  retries: 1,
  workers: 2,

  reporter: [
    ['list'],
    ['html', { outputFolder: 'mobile-test-report', open: 'never' }],
  ],

  use: {
    baseURL: APP_URL,
    // Wait for network to be idle before assertions
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
    // Capture screenshot on failure
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
  },

  projects: [
    // ── iPhone 15 Pro — Safari (WebKit) ───────────────────────────────
    {
      name: 'iPhone 15 Pro',
      use: {
        ...devices['iPhone 15 Pro'],
        // Override UA to real Safari on iOS 17
        userAgent:
          'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) ' +
          'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
      },
    },

    // ── iPhone SE (small screen) — Safari (WebKit) ────────────────────
    {
      name: 'iPhone SE',
      use: {
        ...devices['iPhone SE'],
        userAgent:
          'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) ' +
          'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
      },
    },

    // ── Pixel 7 — Chrome (Chromium) ───────────────────────────────────
    {
      name: 'Pixel 7 (Android)',
      use: {
        ...devices['Pixel 7'],
        userAgent:
          'Mozilla/5.0 (Linux; Android 13; Pixel 7) ' +
          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
      },
    },

    // ── Samsung Galaxy S23 — Chrome (Chromium) ────────────────────────
    {
      name: 'Galaxy S23 (Android)',
      use: {
        ...devices['Galaxy S8'],  // closest built-in profile
        viewport: { width: 390, height: 844 },
        deviceScaleFactor: 3,
        isMobile: true,
        hasTouch: true,
        userAgent:
          'Mozilla/5.0 (Linux; Android 13; SM-S911B) ' +
          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
      },
    },
  ],
});
