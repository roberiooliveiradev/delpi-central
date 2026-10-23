import { defineConfig } from "@playwright/test";

/**
 * TV Dashboard editor E2E — Task VISTA-TV-EDITOR-E2E-VALIDATION-026.
 * Stack local real: gateway + portal/MFE + tv-dashboard-api + Keycloak + RBAC.
 * Nunca rodar contra produção.
 *
 * Env:
 *   TV_E2E_BASE_URL (default http://localhost)
 *   TV_E2E_PASS_EDITOR / TV_E2E_PASS_MANAGER / TV_E2E_PASS_VIEWER
 *   TV_E2E_PLAYLIST / TV_E2E_SLIDE_A / TV_E2E_SLIDE_B (fixtures provisionadas)
 */
export default defineConfig({
  testDir: "./specs",
  timeout: 90_000,
  retries: 0,
  workers: 1, // mesma playlist mutável — serial por contrato
  use: {
    baseURL: process.env.TV_E2E_BASE_URL ?? "http://localhost",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "off",
    viewport: { width: 1920, height: 1080 },
  },
});
