import { defineConfig } from "@playwright/test";

/**
 * BPMN Modeler browser E2E — stack mínima real (P7 §23):
 * gateway + portal/MFE + bpmn-modeler-api + bpmn_modeler DB + Keycloak + Core RBAC.
 *
 * Requer BPMN_E2E_BASE_URL (ex.: http://localhost) e identidades de teste
 * provisionadas (actor matrix §24): viewer / editor / manager.
 */
export default defineConfig({
  testDir: "./specs",
  timeout: 60_000,
  retries: 0,
  use: {
    baseURL: process.env.BPMN_E2E_BASE_URL ?? "http://localhost",
    trace: "retain-on-failure",
  },
});
