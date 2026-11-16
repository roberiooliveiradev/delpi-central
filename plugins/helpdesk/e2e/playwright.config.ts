import { defineConfig, devices } from "@playwright/test";

/** E2E UX V2 — homologação real do MFE Meus Chamados de TI:
 *  login SSO → /apps/helpdesk → Minhas, Fila, Nova, Administração.
 *  Credenciais via env (infra/.env):
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
    baseURL: process.env.HELPDESK_E2E_BASE_URL ?? "http://localhost",
    /* TLS self-signed do ambiente HML — opt-in explícito, nunca
     * para apontar a PRD sem certificado válido. */
    ignoreHTTPSErrors: process.env.PLAYWRIGHT_INSECURE === "1",
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
    { name: "tablet", use: { ...devices["Galaxy Tab S4"] } },
    {
      name: "mobile-320",
      use: { ...devices["Pixel 7"], viewport: { width: 320, height: 720 } },
    },
  ],
});
