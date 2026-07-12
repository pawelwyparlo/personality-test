import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright config for the happy-path e2e.
 *
 * The spec runs on the HOST against the already-running Compose stack (it does
 * NOT start its own server). Point it at a different frontend with FRONTEND_URL;
 * the default matches the local Compose port (see the root .env / README).
 */
const baseURL = process.env.FRONTEND_URL ?? 'http://localhost:15173'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: 0,
  reporter: 'list',
  use: {
    baseURL,
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})
