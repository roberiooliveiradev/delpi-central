import { execSync } from "node:child_process";
import { request } from "@playwright/test";
import { test, expect, apiToken, loginAs } from "../helpers";

/**
 * G5-ACC-1 — Cross-app acceptance: Transformômetro ↔ BPMN Modeler.
 *
 * Browser real contra LOCAL INTEGRATION RUNTIME: portal + MFEs + APIs +
 * Keycloak + DBs. Zero mocks — todo read-back passa pelo contrato HTTP
 * público das duas APIs e pelo audit_logs do schema transformometro.
 *
 * Contrato (ADR-005): referência = (model_id, revision_number) explícita,
 * imutável, owned pelo Transformômetro; resolução remota via bearer do
 * usuário; sem auto-follow-latest; falha do Modeler degrada a leitura.
 */

const TM_API = "/apps/transformometro-api/transformometro";
const BPMN_API = "/apps/bpmn-modeler-api";

const RUN = `g5e2e-${Date.now().toString(36)}`;
const MODEL_A = `G5 E2E Modelo A ${RUN}`;
const MODEL_B = `G5 E2E Modelo B ${RUN}`;

const WC_XML = (marker: string) =>
  '<?xml version="1.0" encoding="UTF-8"?>' +
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ' +
  `id="defs_${marker}" targetNamespace="urn:g5e2e">` +
  '<bpmn:process id="p1" isExecutable="false">' +
  '<bpmn:startEvent id="s1"/><bpmn:task id="t1" name="Etapa"/>' +
  '<bpmn:endEvent id="e1"/>' +
  '<bpmn:sequenceFlow id="f1" sourceRef="s1" targetRef="t1"/>' +
  '<bpmn:sequenceFlow id="f2" sourceRef="t1" targetRef="e1"/>' +
  "</bpmn:process></bpmn:definitions>";

type Actor = "manager" | "viewer" | "editor";

const BASE = process.env.BPMN_E2E_BASE_URL ?? "http://localhost";

async function api(
  actor: Actor,
  method: string,
  path: string,
  opts: { body?: unknown; headers?: Record<string, string>; raw?: string } = {},
) {
  const token = await apiToken(actor);
  const ctx = await request.newContext({ baseURL: BASE });
  const resp = await ctx.fetch(path, {
    method,
    headers: {
      ...(opts.raw ? { "Content-Type": "application/xml" } : { "Content-Type": "application/json" }),
      Authorization: `Bearer ${token}`,
      ...opts.headers,
    },
    data: opts.raw ?? (opts.body ? JSON.stringify(opts.body) : undefined),
  });
  return resp;
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

async function modelVersion(actor: Actor, modelId: string): Promise<number> {
  const { json } = await apiJson(actor, "GET", `${BPMN_API}/models/${modelId}`);
  return json.data.version as number;
}

async function saveWorkingCopy(actor: Actor, modelId: string, xml: string): Promise<void> {
  const version = await modelVersion(actor, modelId);
  const resp = await api(actor, "PUT", `${BPMN_API}/models/${modelId}/working-copy`, {
    raw: xml,
    headers: { "If-Match": `"v${version}"` },
  });
  if (!resp.ok()) throw new Error(`save working copy failed: ${resp.status()} ${await resp.text()}`);
}

async function createRevision(actor: Actor, modelId: string, name: string): Promise<void> {
  const version = await modelVersion(actor, modelId);
  const resp = await api(actor, "POST", `${BPMN_API}/models/${modelId}/revisions`, {
    body: { name },
    headers: { "If-Match": `"v${version}"` },
  });
  if (resp.status() !== 201)
    throw new Error(`create revision failed: ${resp.status()} ${await resp.text()}`);
}

async function createModelWithRevision(
  actor: Actor,
  displayName: string,
  marker: string,
): Promise<string> {
  const { status, json } = await apiJson(actor, "POST", `${BPMN_API}/models`, {
    body: { display_name: displayName },
  });
  if (status !== 201) throw new Error(`create model failed: ${status}`);
  const modelId = json.data.model_id as string;
  await saveWorkingCopy(actor, modelId, WC_XML(marker));
  await createRevision(actor, modelId, "R1 acceptance");
  return modelId;
}

type BpmnRef = {
  reference: { model_id: string; revision_number: number } | null;
  resolved: { state: string; model_display_name?: string; latest_revision_number?: number } | null;
};

async function tmReference(actor: Actor, processoId: string): Promise<BpmnRef> {
  const { status, json } = await apiJson(
    actor,
    "GET",
    `${TM_API}/processos/${processoId}/bpmn-reference`,
  );
  if (status !== 200) throw new Error(`GET reference failed: ${status}`);
  return json.data as BpmnRef;
}

function auditReferenceRows(processoId: string): { action: string; old: string; new: string }[] {
  const sql =
    `SELECT action || '|' || ` +
    `COALESCE(payload_json->'old_reference'->>'revision_number','null') || '|' || ` +
    `COALESCE(payload_json->'new_reference'->>'revision_number','null') || '|' || ` +
    `COALESCE(payload_json->'old_reference'->>'model_id','null') || '|' || ` +
    `COALESCE(payload_json->'new_reference'->>'model_id','null') ` +
    `FROM transformometro.audit_logs ` +
    `WHERE entity_type='processo_bpmn_reference' AND entity_id='${processoId}' ORDER BY created_at`;
  const out = execSync(
    `docker exec delpi-postgres-plugins psql -U plugins_user -d plugins_hub -t -A -c "${sql}"`,
    { encoding: "utf-8" },
  );
  return out
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean)
    .map((l) => {
      const [action, oldRev, newRev, oldModel, newModel] = l.split("|");
      return { action, old: `${oldModel}/R${oldRev}`, new: `${newModel}/R${newRev}` };
    });
}

const processoUrl = (pid: string) => `/apps/transformometro/processes/${pid}#diagrama`;
const card = (page: import("@playwright/test").Page) =>
  page.getByTestId("bpmn-reference-card");

/** storageState pode capturar cookies KC antes do portal reidratar a sessão —
 *  se cair na tela de login, refaz o fluxo SSO real uma vez. */
async function gotoProcesso(
  page: import("@playwright/test").Page,
  pid: string,
) {
  await page.goto(processoUrl(pid));
  const sso = page.getByRole("button", { name: /Entrar com DELPI SSO/ });
  if (await sso.isVisible().catch(() => false)) {
    await loginAs(page, "manager");
    await page.goto(processoUrl(pid));
  }
}

test.describe("G5 — Transformômetro ↔ BPMN Modeler (cross-app, runtime real)", () => {
  test.describe.configure({ mode: "serial" });
  test.use({ actor: "manager", viewport: { width: 1440, height: 900 } });
  test.setTimeout(120_000);

  let processoId = "";
  let modelA = "";
  let modelB = "";

  test.beforeAll(async () => {
    processoId = await createProcesso("manager", `G5 E2E Processo ${RUN}`);
    modelA = await createModelWithRevision("manager", MODEL_A, "a1");
    modelB = await createModelWithRevision("manager", MODEL_B, "b1");
  });

  test("E2E-01 empty → link → authoritative read-back", async ({ page }) => {
    await gotoProcesso(page, processoId);
    await expect(card(page)).toBeVisible({ timeout: 60_000 });
    await expect(card(page)).toContainText("Nenhum modelo BPMN vinculado");

    await card(page).getByRole("button", { name: /Vincular modelo BPMN/ }).click();
    const dialog = page.getByRole("dialog", { name: "Vincular modelo BPMN" });
    await expect(dialog).toBeVisible();
    await dialog.getByRole("button", { name: new RegExp(MODEL_A) }).click();
    await dialog.getByRole("radio", { name: /^R1(\s|$)/ }).check();
    await dialog.getByRole("button", { name: "Confirmar vínculo" }).click();

    await expect(card(page)).toContainText(MODEL_A);
    await expect(card(page)).toContainText("revisão vinculada: R1");

    const ref = await tmReference("manager", processoId);
    expect(ref.reference?.model_id).toBe(modelA);
    expect(ref.reference?.revision_number).toBe(1);
    expect(ref.resolved?.state).toBe("resolved");

    const remote = await apiJson("manager", "GET", `${BPMN_API}/models/${modelA}/revisions/1`);
    expect(remote.status).toBe(200);
  });

  test("E2E-02 visualizar revisão abre historical revision read-only", async ({ page }) => {
    await gotoProcesso(page, processoId);
    await expect(card(page)).toContainText("revisão vinculada: R1", { timeout: 60_000 });

    const [revPage] = await Promise.all([
      page.context().waitForEvent("page"),
      card(page).getByRole("link", { name: /Visualizar revisão/ }).click(),
    ]);
    await revPage.waitForURL(`**/apps/bpmn-modeler/models/${modelA}/revisions/1`);
    await expect(revPage.getByRole("heading", { name: /Revisão 1/ })).toBeVisible({
      timeout: 60_000,
    });
    await expect(revPage.getByText("Somente leitura", { exact: true })).toBeVisible();
    await revPage.close();
  });

  test("E2E-03 abrir no Modelador não altera a revisão vinculada", async ({ page }) => {
    await gotoProcesso(page, processoId);
    await expect(card(page)).toContainText("revisão vinculada: R1", { timeout: 60_000 });

    const [editorPage] = await Promise.all([
      page.context().waitForEvent("page"),
      card(page).getByRole("link", { name: /Abrir no Modelador/ }).click(),
    ]);
    await editorPage.waitForURL(`**/apps/bpmn-modeler/models/${modelA}`);
    await expect(editorPage.locator(".bpmnm-canvas")).toBeVisible({ timeout: 60_000 });
    await editorPage.close();

    const ref = await tmReference("manager", processoId);
    expect(ref.reference?.revision_number).toBe(1);
  });

  test("E2E-04 nova revisão BPMN não move o vínculo (no auto-follow)", async ({ page }) => {
    await saveWorkingCopy("manager", modelA, WC_XML("a2"));
    await createRevision("manager", modelA, "R2 acceptance");

    await gotoProcesso(page, processoId);
    await expect(card(page)).toContainText("revisão vinculada: R1", { timeout: 60_000 });
    await expect(page.getByTestId("bpmn-newer-revision")).toContainText("R2");

    const ref = await tmReference("manager", processoId);
    expect(ref.reference?.revision_number).toBe(1);
    expect(ref.resolved?.latest_revision_number).toBe(2);
  });

  test("E2E-05 atualização explícita de revisão R1 → R2 + audit", async ({ page }) => {
    await gotoProcesso(page, processoId);
    await expect(card(page)).toContainText("revisão vinculada: R1", { timeout: 60_000 });

    await card(page).getByRole("button", { name: /Alterar vínculo/ }).click();
    const dialog = page.getByRole("dialog", { name: "Vincular modelo BPMN" });
    await dialog.getByRole("button", { name: new RegExp(MODEL_A) }).click();
    await dialog.getByRole("radio", { name: /^R2(\s|$)/ }).check();
    await dialog.getByRole("button", { name: "Confirmar vínculo" }).click();

    await expect(card(page)).toContainText("revisão vinculada: R2");

    const ref = await tmReference("manager", processoId);
    expect(ref.reference?.revision_number).toBe(2);

    const updates = auditReferenceRows(processoId).filter((r) => r.action === "update");
    const last = updates.at(-1);
    expect(last?.old).toBe(`${modelA}/R1`);
    expect(last?.new).toBe(`${modelA}/R2`);
  });

  test("E2E-06 troca de modelo A/R2 → B/R1 + audit old/new", async ({ page }) => {
    await gotoProcesso(page, processoId);
    await expect(card(page)).toContainText("revisão vinculada: R2", { timeout: 60_000 });

    await card(page).getByRole("button", { name: /Alterar vínculo/ }).click();
    const dialog = page.getByRole("dialog", { name: "Vincular modelo BPMN" });
    await expect(dialog).toContainText("Atual:");
    await dialog.getByRole("button", { name: new RegExp(MODEL_B) }).click();
    await dialog.getByRole("radio", { name: /^R1(\s|$)/ }).check();
    await dialog.getByRole("button", { name: "Confirmar vínculo" }).click();

    await expect(card(page)).toContainText(MODEL_B);
    await expect(card(page)).toContainText("revisão vinculada: R1");

    const ref = await tmReference("manager", processoId);
    expect(ref.reference?.model_id).toBe(modelB);
    expect(ref.reference?.revision_number).toBe(1);

    const updates = auditReferenceRows(processoId).filter((r) => r.action === "update");
    const last = updates.at(-1);
    expect(last?.old).toBe(`${modelA}/R2`);
    expect(last?.new).toBe(`${modelB}/R1`);
  });

  test("E2E-07 unlink não exclui o modelo BPMN", async ({ page }) => {
    await gotoProcesso(page, processoId);
    await expect(card(page)).toContainText("revisão vinculada: R1", { timeout: 60_000 });

    await card(page).getByRole("button", { name: "Desvincular" }).click();
    const dialog = page.getByRole("dialog", { name: "Desvincular modelo BPMN" });
    await expect(dialog).toContainText("não excluirá o modelo BPMN");
    await dialog.getByRole("button", { name: "Desvincular", exact: true }).click();

    await expect(card(page)).toContainText("Nenhum modelo BPMN vinculado");

    const ref = await tmReference("manager", processoId);
    expect(ref.reference).toBeNull();

    const remote = await apiJson("manager", "GET", `${BPMN_API}/models/${modelB}`);
    expect(remote.status).toBe(200);
  });

  test("E2E-08 cross-owner: usuário sem ownership do modelo vê referência degradada", async ({
    page,
    browser,
  }) => {
    // setup governado: manager re-vincula A/R2 como dono
    const put = await apiJson("manager", "PUT", `${TM_API}/processos/${processoId}/bpmn-reference`, {
      body: { model_id: modelA, revision_number: 2 },
    });
    expect(put.status).toBe(200);

    await gotoProcesso(page, processoId);
    await expect(card(page)).toContainText(MODEL_A, { timeout: 60_000 });
    await page.close();

    // User B (viewer): tem transformometro.access, não é owner do modelo A
    const ctxB = await browser.newContext();
    const pageB = await ctxB.newPage();
    await loginAs(pageB, "viewer");
    await gotoProcesso(pageB, processoId, "viewer");
    await expect(card(pageB)).toBeVisible({ timeout: 60_000 });
    await expect(card(pageB)).toContainText("sem acesso ou não encontrada");
    await expect(card(pageB)).toContainText(modelA);
    await expect(card(pageB)).not.toContainText(MODEL_A);
    await ctxB.close();

    const refB = await tmReference("viewer", processoId);
    expect(refB.reference?.model_id).toBe(modelA);
    expect(refB.reference?.revision_number).toBe(2);
    expect(refB.resolved?.state).toBe("inaccessible_or_missing");
  });
});
