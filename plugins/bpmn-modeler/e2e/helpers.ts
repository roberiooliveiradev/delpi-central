import { test as base, expect, type Page } from "@playwright/test";

/**
 * Actor matrix (P7 §24). Identidades de teste provisionadas no Keycloak/RBAC
 * de homologação — tokens obtidos via helper de ambiente, nunca hardcoded.
 */

export type Actor = "viewer" | "editor" | "manager" | "none";

async function tokenFor(page: Page, actor: Actor): Promise<void> {
  const envName = `BPMN_E2E_TOKEN_${actor.toUpperCase()}`;
  const token = process.env[envName];
  if (actor !== "none" && !token) {
    throw new Error(`Missing ${envName} — provisione identidade de teste.`);
  }
  if (token) {
    await page.addInitScript((t) => {
      // Convenção do portal: token de sessão injetado para o host MFE.
      (window as unknown as { __E2E_TOKEN__?: string }).__E2E_TOKEN__ = t;
    }, token);
  }
}

export const test = base.extend<{ actor: Actor }>({
  actor: ["editor", { option: true }],
  page: async ({ page, actor }, use) => {
    await tokenFor(page, actor);
    await use(page);
  },
});

export { expect };

export const LIBRARY_URL = "/apps/bpmn-modeler";
export const modelUrl = (id: string) => `${LIBRARY_URL}/models/${id}`;
export const revisionUrl = (id: string, n: number) =>
  `${LIBRARY_URL}/models/${id}/revisions/${n}`;
