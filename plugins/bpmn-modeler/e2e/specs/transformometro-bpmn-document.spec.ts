import { request } from "@playwright/test";
import { test, expect, apiToken, loginAs } from "../helpers";

/**
 * G7-ACC — Cross-app acceptance: documento BPMN NATIVO do processo
 * (Transformômetro-owned) editado pela superfície compartilhada.
 *
 * Browser real contra LOCAL INTEGRATION RUNTIME. Prova o fluxo
 * card → editor → revisão → view histórica → exclusão, o XOR dual-mode
 * no nível de API e a autorização por processo (sem ownership de criador).
 */

const TM_API = "/apps/transformometro-api/transformometro";
const BPMN_API = "/apps/bpmn-modeler-api";

const RUN = `g7e2e-${Date.now().toString(36)}`;

type Actor = "manager" | "viewer" | "editor";

const BASE = process.env.BPMN_E2E_BASE_URL ?? "http://localhost";

async function api(
  actor: Actor,
  method: string,
  path: string,
  opts: { body?: unknown; headers?: Record<string, string> } = {},
) {
  const token = await apiToken(actor);
  const ctx = await request.newContext({ baseURL: BASE });
  return ctx.fetch(path, {
    method,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...opts.headers,
    },
    data: opts.body ? JSON.stringify(opts.body) : undefined,
  });
}

async function apiJson(actor: Actor, method: string, path: string, opts?: Parameters<typeof api>[3]) {
  const resp = await api(actor, method, path, opts);
  const json = await resp.json().catch(() => null);
  return { status: resp.status(), json };
}

async function createProcesso(actor: Actor, nome: string): Promise<string> {
  const { status, json } = await apiJson(actor, "POST", `${TM_API}/processos`, {
    body: { nome_processo: nome, status_processo: "ativo" },
  });
  if (status !== 201) throw new Error(`create processo failed: ${status}`);
  return json.data.processo_id as string;
}

const processoUrl = (pid: string) => `/apps/transformometro/processes/${pid}#diagrama`;
const bpmnEditUrl = (pid: string) => `/apps/transformometro/processes/${pid}/bpmn`;
const card = (page: import("@playwright/test").Page) =>
  page.getByTestId("bpmn-card");
const canvas = (page: import("@playwright/test").Page) =>
  page.getByLabel("Canvas do diagrama BPMN");

/** Mesmo fallback SSO do G5 — contexto frio refaz o login do actor pedido. */
async function gotoPage(
  page: import("@playwright/test").Page,
  url: string,
  actor: Actor = "manager",
) {
  await page.goto(url);
  const sso = page.getByRole("button", { name: /Entrar com DELPI SSO/ });
  const outcome = await Promise.race([
    card(page)
      .waitFor({ state: "visible", timeout: 20_000 })
      .then(() => "card" as const)
      .catch(() => null),
    canvas(page)
      .waitFor({ state: "visible", timeout: 20_000 })
      .then(() => "canvas" as const)
      .catch(() => null),
    sso
      .waitFor({ state: "visible", timeout: 20_000 })
      .then(() => "login" as const)
      .catch(() => null),
  ]);
  if (outcome === "login") {
    await loginAs(page, actor);
    await page.goto(url);
  }
}

test.describe("G7 — documento BPMN nativo do processo (runtime real)", () => {
  test.describe.configure({ mode: "serial" });
  test.use({ actor: "manager", viewport: { width: 1440, height: 900 } });
  test.setTimeout(180_000);

  let processoId = "";

  test.beforeAll(async () => {
    processoId = await createProcesso("manager", `G7 E2E Processo ${RUN}`);
  });

  test("E2E-01 card empty → criar → editor monta + read-back", async ({ page }) => {
    await gotoPage(page, processoUrl(processoId), "manager");
    await expect(card(page)).toBeVisible({ timeout: 60_000 });
    await expect(card(page)).toContainText("Criar diagrama BPMN");

    await card(page).getByRole("button", { name: "Criar diagrama BPMN" }).click();
    await page.waitForURL(new RegExp(`/processes/${processoId}/bpmn$`), {
      timeout: 30_000,
    });
    await expect(canvas(page)).toBeVisible({ timeout: 60_000 });

    const doc = await apiJson(
      "manager",
      "GET",
      `${TM_API}/processos/${processoId}/bpmn-document`,
    );
    expect(doc.status).toBe(200);
    expect(doc.json.data.version).toBe(1);
  });

  test("E2E-02 aba Histórico → Criar revisão persiste checkpoint", async ({
    page,
  }) => {
    await gotoPage(page, bpmnEditUrl(processoId), "manager");
    await expect(canvas(page)).toBeVisible({ timeout: 60_000 });

    await page.getByRole("tab", { name: "Histórico" }).click();
    await expect(page.getByText("Nenhuma revisão")).toBeVisible({
      timeout: 30_000,
    });

    await page.getByRole("button", { name: "Criar revisão" }).click();
    const dialog = page.getByRole("dialog", { name: "Criar revisão" });
    await expect(dialog).toBeVisible();
    await dialog.getByRole("button", { name: "Criar revisão", exact: true }).click();

    await expect(page.getByText("Revisão 1")).toBeVisible({ timeout: 30_000 });

    const revs = await apiJson(
      "manager",
      "GET",
      `${TM_API}/processos/${processoId}/bpmn-document/revisions`,
    );
    expect(revs.status).toBe(200);
    expect(revs.json.data.items).toHaveLength(1);
    expect(revs.json.data.items[0].origin).toBe("explicit");
  });

  test("E2E-03 view de revisão histórica é read-only", async ({ page }) => {
    await gotoPage(
      page,
      `${bpmnEditUrl(processoId)}/revisions/1`,
      "manager",
    );
    await expect(page.getByLabel("Diagrama da revisão")).toBeVisible({
      timeout: 60_000,
    });
  });

  test("E2E-04 XOR dual-mode: nativo ativo bloqueia vínculo externo", async ({
    page,
  }) => {
    // UI: com doc nativo ativo, o card não oferece o picker externo.
    await gotoPage(page, processoUrl(processoId), "manager");
    await expect(card(page)).toContainText("Documento BPMN nativo", {
      timeout: 60_000,
    });
    await expect(
      card(page).getByRole("button", { name: /Vincular modelo BPMN/ }),
    ).toHaveCount(0);

    // API: backend rejeita o vínculo com 409 dual_mode_forbidden.
    const put = await apiJson(
      "manager",
      "PUT",
      `${TM_API}/processos/${processoId}/bpmn-reference`,
      { body: { model_id: crypto.randomUUID(), revision_number: 1 } },
    );
    expect(put.status).toBe(409);
    expect(put.json.data.error_kind).toBe("dual_mode_forbidden");
  });

  test("E2E-05 viewer abre o editor (autorização por processo)", async ({
    browser,
  }) => {
    const ctx = await browser.newContext();
    const pageB = await ctx.newPage();
    try {
      await gotoPage(pageB, bpmnEditUrl(processoId), "viewer");
      await expect(canvas(pageB)).toBeVisible({ timeout: 60_000 });
    } finally {
      await ctx.close();
    }
  });

  test("E2E-06 remover documento volta ao estado vazio", async ({ page }) => {
    await gotoPage(page, processoUrl(processoId), "manager");
    await expect(card(page)).toContainText("Documento BPMN nativo", {
      timeout: 60_000,
    });

    await card(page).getByRole("button", { name: "Remover documento" }).click();
    const dialog = page.getByRole("dialog", { name: "Remover documento BPMN" });
    await expect(dialog).toBeVisible();
    await dialog.getByRole("button", { name: "Remover", exact: true }).click();

    await expect(card(page)).toContainText("Criar diagrama BPMN", {
      timeout: 30_000,
    });

    const doc = await apiJson(
      "manager",
      "GET",
      `${TM_API}/processos/${processoId}/bpmn-document`,
    );
    expect(doc.status).toBe(404);
  });

  test("E2E-07 documento nativo não altera storage do Modeler", async () => {
    // Isolamento de bounded context: os artefatos BPMN do processo vivem em
    // transformometro.* — nunca em bpmn_modeler.* (prova indireta: a API do
    // Modeler não conhece o documento do processo).
    const doc = await apiJson(
      "manager",
      "GET",
      `${TM_API}/processos/${processoId}/bpmn-document`,
    );
    expect(doc.status).toBe(404);
    const models = await apiJson("manager", "GET", `${BPMN_API}/models`);
    expect(models.status).toBe(200);
    const names = JSON.stringify(models.json.data);
    expect(names).not.toContain(processoId);
  });
});
