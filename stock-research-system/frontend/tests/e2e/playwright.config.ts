import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for E2E testing
 * Tests the Tavily Stock Research System
 */
export default defineConfig({
  testDir: './specs',
  timeout: 60000,
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { open: 'never' }],
    ['json', { outputFile: '../results/test-results.json' }],
    ['list']
  ],

  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 10000,
    navigationTimeout: 30000,
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],

  webServer: [
    {
      command: 'npm start',
      port: 3000,
      reuseExistingServer: true,
      timeout: 120000,
    },
    {
      command: 'cd ../../backend && python3 main.py',
      port: 8000,
      reuseExistingServer: true,
      timeout: 120000,
    }
  ],
});