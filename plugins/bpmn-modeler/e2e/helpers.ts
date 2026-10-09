import { existsSync, mkdirSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  test as base,
  expect,
  request,
  type Browser,
  type Page,
} from "@playwright/test";

/**
 * Actor matrix (P7 §24). Identidades de teste provisionadas no Keycloak/RBAC
 * de dev via `e2e/provision-test-identities.sh` — credenciais via env,
 * nunca hardcoded:
 *
 *   BPMN_E2E_USER_VIEWER / BPMN_E2E_PASS_VIEWER
 *   BPMN_E2E_USER_EDITOR / BPMN_E2E_PASS_EDITOR
 *   BPMN_E2E_USER_MANAGER / BPMN_E2E_PASS_MANAGER
 *
 * Login é o fluxo real: portal → Keycloak authorize → form → redirect de
 * volta. Nenhum mock de boundary.
 */

export type Actor = "viewer" | "editor" | "manager" | "none";

function credentials(actor: Actor): { user: string; pass: string } | null {
  if (actor === "none") return null;
  const user = process.env[`BPMN_E2E_USER_${actor.toUpperCase()}`];
  const pass = process.env[`BPMN_E2E_PASS_${actor.toUpperCase()}`];
  if (!user || !pass) {
    throw new Error(
      `Missing BPMN_E2E_USER_${actor.toUpperCase()}/BPMN_E2E_PASS_${actor.toUpperCase()} ` +
        `— provisione via e2e/provision-test-identities.sh.`,
    );
  }
  return { user, pass };
}

/** Login real: portal /login → "Entrar com DELPI SSO" → Keycloak form →
 *  redirect de volta ao portal autenticado. */
export async function loginAs(page: Page, actor: Actor): Promise<void> {
  const creds = credentials(actor);
  if (!creds) return;
  await page.goto("/");
  if (!page.url().includes("/login")) {
    await page.waitForURL(/\/login/, { timeout: 30_000 });
  }
  await page.getByRole("button", { name: /Entrar com DELPI SSO/ }).click();
  // Com sessão KC viva o IdP pode redirecionar direto (silent SSO) sem exibir
  // o formulário — só preencher credenciais quando o campo aparecer.
  const userField = page
    .getByRole("textbox", { name: /usuário|username|email/i })
    .first();
  const formShown = await userField
    .waitFor({ state: "visible", timeout: 10_000 })
    .then(() => true)
    .catch(() => false);
  if (formShown) {
    // tema keycloak delpi-energy: labels acessíveis, ids variam por tema
    await userField.fill(creds.user);
    await page
      .getByRole("textbox", { name: /senha|password/i })
      .first()
      .fill(creds.pass);
    await page.getByRole("button", { name: /entrar|sign in|log in/i }).click();
  }
  await page.waitForURL(
    (url) => !url.pathname.startsWith("/auth/") && !url.pathname.endsWith("/login"),
    { timeout: 30_000 },
  );
}

/** Access token por password-grant — somente para SETUP via API
 *  (criação de fixtures); nunca para validar o fluxo de auth da UI. */
export async function apiToken(actor: Actor): Promise<string> {
  const creds = credentials(actor);
  if (!creds) throw new Error(`actor ${actor} has no credentials`);
  const base = process.env.BPMN_E2E_BASE_URL ?? "http://localhost";
  const ctx = await request.newContext({ baseURL: base });
  const resp = await ctx.post(
    "/auth/realms/delpi/protocol/openid-connect/token",
    {
      form: {
        client_id: "delpi-central",
        grant_type: "password",
        username: creds.user,
        password: creds.pass,
      },
    },
  );
  if (!resp.ok()) throw new Error(`token grant failed: ${resp.status()}`);
  return (await resp.json()).access_token as string;
}

/**
 * Session cache (R2 §13–§14): um login real por (worker, actor) gravado
 * como storageState imutável em `.auth/worker-{idx}-{actor}.json`.
 * Cada teste recebe contexto novo a partir do snapshot — isolamento de
 * cookies/storage entre testes, sem login storm no Keycloak.
 *
 * Retry: apenas na fronteira externa (login SSO). MAX 2 tentativas com
 * backoff curto; falha não é cacheada — o próximo teste pode re-tentar.
 */
const AUTH_DIR = join(dirname(fileURLToPath(import.meta.url)), ".auth");
const AUTH_MAX_ATTEMPTS = 2;
const AUTH_BACKOFF_MS = 1_500;
const authStates = new Map<Actor, Promise<string>>();

async function captureAuthState(
  browser: Browser,
  actor: Actor,
  file: string,
): Promise<string> {
  let lastError: unknown;
  for (let attempt = 1; attempt <= AUTH_MAX_ATTEMPTS; attempt++) {
    const context = await browser.newContext();
    try {
      const page = await context.newPage();
      await loginAs(page, actor);
      mkdirSync(AUTH_DIR, { recursive: true });
      await context.storageState({ path: file });
      return file;
    } catch (error) {
      lastError = error;
      if (attempt < AUTH_MAX_ATTEMPTS) {
        await new Promise((r) => setTimeout(r, AUTH_BACKOFF_MS));
      }
    } finally {
      await context.close();
    }
  }
  throw lastError;
}

function ensureAuthState(
  browser: Browser,
  actor: Actor,
  workerIndex: number,
): Promise<string> {
  const file = join(AUTH_DIR, `worker-${workerIndex}-${actor}.json`);
  if (existsSync(file)) return Promise.resolve(file);
  let pending = authStates.get(actor);
  if (!pending) {
    pending = captureAuthState(browser, actor, file);
    authStates.set(actor, pending);
    // falha transitória não é permanentemente cacheada
    pending.catch(() => authStates.delete(actor));
  }
  return pending;
}

export const test = base.extend<{ actor: Actor }>({
  actor: ["editor", { option: true }],
  page: async ({ browser, actor }, use, testInfo) => {
    if (actor === "none") {
      const context = await browser.newContext();
      const page = await context.newPage();
      await use(page);
      await context.close();
      return;
    }
    let state = await ensureAuthState(browser, actor, testInfo.workerIndex);
    let context = await browser.newContext({ storageState: state });
    let page = await context.newPage();
    // warm-up: snapshot começa em about:blank onde localStorage é negado;
    // navegar ao portal garante origem válida antes do teste
    await page.goto("/");
    // self-healing: sessão persistida pode estar stale (IdP restart,
    // refresh expirado) — o portal redireciona a /login via JS logo após
    // o boot. Settle curto cobre o redirect; recaptura 1x se cair em login.
    await page.waitForTimeout(1_200);
    const landedLogin = page.url().includes("/login");
    if (landedLogin) {
      const stale = join(
        AUTH_DIR,
        `worker-${testInfo.workerIndex}-${actor}.json`,
      );
      authStates.delete(actor);
      rmSync(stale, { force: true });
      await context.close();
      state = await ensureAuthState(browser, actor, testInfo.workerIndex);
      context = await browser.newContext({ storageState: state });
      page = await context.newPage();
      await page.goto("/");
    }
    await use(page);
    await context.close();
  },
});

export { expect };

export const LIBRARY_URL = "/apps/bpmn-modeler";
export const modelUrl = (id: string) => `${LIBRARY_URL}/models/${id}`;
export const revisionUrl = (id: string, n: number) =>
  `${LIBRARY_URL}/models/${id}/revisions/${n}`;

/** Fixture factory via API — cria model real para uso nas jornadas. */
export async function createModelViaApi(
  actor: Actor,
  displayName: string,
): Promise<string> {
  const base = process.env.BPMN_E2E_BASE_URL ?? "http://localhost";
  const token = await apiToken(actor);
  const ctx = await request.newContext({ baseURL: base });
  const resp = await ctx.post("/apps/bpmn-modeler-api/models", {
    headers: { Authorization: `Bearer ${token}` },
    data: { display_name: displayName },
  });
  if (!resp.ok())
    throw new Error(`create model failed: ${resp.status()} ${await resp.text()}`);
  return (await resp.json()).data.model_id as string;
}

/** Import via API — sobe um .bpmn real como fixture do teste. */
export async function importModelViaApi(
  actor: Actor,
  displayName: string,
  xml: string,
): Promise<string> {
  const base = process.env.BPMN_E2E_BASE_URL ?? "http://localhost";
  const token = await apiToken(actor);
  const ctx = await request.newContext({ baseURL: base });
  const resp = await ctx.post("/apps/bpmn-modeler-api/models/import", {
    headers: { Authorization: `Bearer ${token}` },
    multipart: {
      file: { name: "fixture.bpmn", mimeType: "text/xml", buffer: Buffer.from(xml) },
      display_name: displayName,
    },
  });
  if (!resp.ok())
    throw new Error(`import failed: ${resp.status()} ${await resp.text()}`);
  return (await resp.json()).data.model_id as string;
}

/** Autosave: aguarda o estado autoritativo verificado (write→read-back). */
export async function waitSaved(page: Page, timeout = 20_000): Promise<void> {
  await expect(page.locator(".bpmnm-save-status")).toHaveText("Salvo", {
    timeout,
  });
}

/** Estado "não persistido ainda" visível (queued, in-flight ou falha). */
export const PENDING_SAVE_RE =
  /Alterações aguardando salvamento|Salvando…|Falha ao salvar|Sem conexão/;

/** Força ciclo de refresh de token no portal (AppHost → refreshToken real). */
export async function requestTokenRefresh(page: Page): Promise<void> {
  await page.evaluate(() =>
    window.postMessage({ type: "DELPI_REFRESH_REQUEST" }, location.origin),
  );
}
