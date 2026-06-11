import { defineConfig } from "@playwright/test";

// The E2E suite runs against the PRODUCTION build served at the REAL
// deployment base path — not the dev server at /. Unit tests cannot see
// deployment-path bugs (TDD_CONTRACT.md, Bug #8); this configuration is
// the deploy gate that can.
const BASE_PATH = "/geo-fluid-dynamics-engine/";

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  retries: process.env.CI ? 1 : 0,
  use: {
    baseURL: `http://localhost:4173${BASE_PATH}`,
    // Locally this box has no Playwright browsers; system Edge is Chromium.
    ...(process.env.CI ? {} : { channel: "msedge" }),
  },
  webServer: {
    command: "npm run build && npm run preview",
    url: `http://localhost:4173${BASE_PATH}`,
    env: { GFDE_BASE: BASE_PATH },
    reuseExistingServer: false,
    timeout: 180_000,
  },
});
