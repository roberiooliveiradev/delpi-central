import { defineConfig, devices } from "@playwright/test";

/** E2E NC (T6) — homologação real do Portal Engenharia:
 *  login SSO → /apps/engineering/nonconformities → list/detail/form +
 *  bridge legado. Credenciais via env (infra/.env.local):
 *  DEV_PORTAL_USERNAME / DEV_PORTAL_PASSWORD. */
export default defineConfig({
  testDir: "./specs",
  timeout: 60_000,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"]],
  outputDir: "./artifacts/test-results",
  use: {
    baseURL: process.env.ENGINEERING_E2E_BASE_URL ?? "http://localhost",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "off",
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile", use: { ...devices["Pixel 7"] } },
  ],
});
