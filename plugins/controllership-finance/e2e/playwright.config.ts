import { defineConfig, devices } from "@playwright/test";

/** E2E T12 — Auditoria de Entradas em HML (ou DEV com as mesmas envs). */
export default defineConfig({
  testDir: "./specs",
  timeout: 120_000,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"]],
  outputDir: "./artifacts/test-results",
  use: {
    baseURL:
      process.env.CF_E2E_BASE_URL ??
      process.env.ENGINEERING_E2E_BASE_URL ??
      "https://192.168.1.237:18443",
    ignoreHTTPSErrors: process.env.PLAYWRIGHT_INSECURE !== "0",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "off",
    launchOptions: process.env.PLAYWRIGHT_CHROME_PATH
      ? { executablePath: process.env.PLAYWRIGHT_CHROME_PATH }
      : {},
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile", use: { ...devices["Pixel 7"] } },
  ],
});
