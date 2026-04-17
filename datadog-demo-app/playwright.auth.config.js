// @ts-check
/**
 * Playwright config for Google OAuth + Earnings Whisper E2E tests.
 * Run with: npx playwright test --config=playwright.auth.config.js
 */
const { defineConfig, devices } = require('@playwright/test');

const APP_URL = process.env.APP_URL || 'http://localhost:3000';

module.exports = defineConfig({
  testDir: './tests/auth',
  timeout: 30_000,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : 2, // serial in CI to avoid port contention

  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-auth-report', open: 'never' }],
    ['junit', { outputFile: 'playwright-auth-junit.xml' }],
  ],

  use: {
    baseURL: APP_URL,
    actionTimeout: 10_000,
    navigationTimeout: 20_000,
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
    // Inject JWT_SECRET into browser context so frontend can verify tokens
    storageState: undefined, // each test starts with clean storage
  },

  projects: [
    // Desktop Chrome — primary for auth tests
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    // Firefox — secondary coverage
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
  ],

  // Start a local dev server if APP_URL is localhost
  webServer: APP_URL.includes('localhost') ? {
    command: 'NODE_ENV=test JWT_SECRET=test-jwt-secret-not-for-production node src/app.js',
    url: `${APP_URL}/api/health`,
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
    env: {
      NODE_ENV: 'test',
      PORT: '3000',
      JWT_SECRET: 'test-jwt-secret-not-for-production',
      LOG_LEVEL: 'silent',
    },
  } : undefined,
});
