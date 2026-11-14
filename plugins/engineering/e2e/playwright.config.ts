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
    /* TLS self-signed do ambiente HML — opt-in explícito, nunca
     * para apontar a PRD sem certificado válido. */
    ignoreHTTPSErrors: process.env.PLAYWRIGHT_INSECURE === "1",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "off",
    /* Permite apontar para um chrome já instalado quando o headless
     * shell do playwright não está baixado (dev local). */
    launchOptions: process.env.PLAYWRIGHT_CHROME_PATH
      ? { executablePath: process.env.PLAYWRIGHT_CHROME_PATH }
      : {},
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile", use: { ...devices["Pixel 7"] } },
    { name: "tablet", use: { ...devices["Galaxy Tab S4"] } },
    {
      name: "mobile-320",
      use: { ...devices["Pixel 7"], viewport: { width: 320, height: 720 } },
    },
  ],
});
