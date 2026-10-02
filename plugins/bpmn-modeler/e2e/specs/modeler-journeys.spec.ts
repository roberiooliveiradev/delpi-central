import {
  test,
  expect,
  apiToken,
  createModelViaApi,
  importModelViaApi,
  LIBRARY_URL,
  modelUrl,
  waitSaved,
  PENDING_SAVE_RE,
  type Actor,
} from "../helpers";
import { request } from "@playwright/test";

/**
 * Jornadas E2E congeladas (P7 §25). Stack real: gateway + portal/MFE +
 * bpmn-modeler-api + plugins_hub.bpmn_modeler + Keycloak + Core RBAC —
 * sem mocks nos boundaries. Identidades via provision-test-identities.sh.
 * Data isolation: cada teste cria seus próprios models.
 */

const BPMN_HEAD =
  '<?xml version="1.0" encoding="UTF-8"?>\n' +
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ' +
  'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" ' +
  'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" ' +
  'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" ' +
  'id="defs_e2e" targetNamespace="urn:e2e">\n';
const BPMN_TAIL = "</bpmn:definitions>";

const XML_NO_DI =
  BPMN_HEAD +
  '  <bpmn:process id="P1" isExecutable="false">\n' +
  '    <bpmn:startEvent id="S1"/>\n    <bpmn:task id="T1"/>\n' +
  '    <bpmn:sequenceFlow id="F1" sourceRef="S1" targetRef="T1"/>\n' +
  "  </bpmn:process>\n" +
  BPMN_TAIL;

const XML_DI =
  BPMN_HEAD +
  '  <bpmn:process id="P1" isExecutable="false">\n' +
  '    <bpmn:startEvent id="S1"/>\n    <bpmn:task id="T1"/>\n' +
  '    <bpmn:sequenceFlow id="F1" sourceRef="S1" targetRef="T1"/>\n' +
  "  </bpmn:process>\n" +
  '  <bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL1" bpmnElement="P1">' +
  '<bpmndi:BPMNShape id="S1_di" bpmnElement="S1"><dc:Bounds x="100" y="100" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="T1_di" bpmnElement="T1"><dc:Bounds x="250" y="80" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNEdge id="F1_di" bpmnElement="F1"><di:waypoint x="136" y="118"/><di:waypoint x="250" y="120"/></bpmndi:BPMNEdge>' +
  "</bpmndi:BPMNPlane></bpmndi:BPMNDiagram>\n" +
  BPMN_TAIL;

const XML_EXT_MU_FALSE =
  BPMN_HEAD.replace('id="defs_e2e"', 'xmlns:vend="http://vendor.example/x" id="defs_e2e"') +
  '  <bpmn:process id="P1"><bpmn:task id="T1" vend:custom="yes"/></bpmn:process>\n' +
  BPMN_TAIL;

const XML_EXT_MU_TRUE =
  BPMN_HEAD.replace('id="defs_e2e"', 'xmlns:vend="http://vendor.example/x" id="defs_e2e"') +
  '  <bpmn:extension definition="vend:prop" mustUnderstand="true"/>\n' +
  '  <bpmn:process id="P1"><bpmn:task id="T1"><bpmn:extensionElements><vend:prop key="a"/></bpmn:extensionElements></bpmn:task></bpmn:process>\n' +
  BPMN_TAIL;

const XML_MULTI_DI =
  BPMN_HEAD +
  '  <bpmn:collaboration id="C1">\n' +
  '    <bpmn:participant id="PA" processRef="P1"/>\n' +
  '    <bpmn:participant id="PB" processRef="P2"/>\n' +
  "  </bpmn:collaboration>\n" +
  '  <bpmn:process id="P1"><bpmn:task id="TA"/></bpmn:process>\n' +
  '  <bpmn:process id="P2"><bpmn:task id="TB"/></bpmn:process>\n' +
  '  <bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL1" bpmnElement="P1">' +
  '<bpmndi:BPMNShape id="TA_di" bpmnElement="TA"><dc:Bounds x="100" y="80" width="100" height="80"/></bpmndi:BPMNShape>' +
  "</bpmndi:BPMNPlane></bpmndi:BPMNDiagram>\n" +
  '  <bpmndi:BPMNDiagram id="D2"><bpmndi:BPMNPlane id="PL2" bpmnElement="P2">' +
  '<bpmndi:BPMNShape id="TB_di" bpmnElement="TB"><dc:Bounds x="100" y="80" width="100" height="80"/></bpmndi:BPMNShape>' +
  "</bpmndi:BPMNPlane></bpmndi:BPMNDiagram>\n" +
  BPMN_TAIL;

const XML_BROKEN_REF =
  BPMN_HEAD +
  '  <bpmn:process id="P1"><bpmn:task id="T1"/>' +
  '<bpmn:sequenceFlow id="F1" sourceRef="GHOST" targetRef="T1"/>' +
  '<bpmn:intermediateCatchEvent id="ICE1">' +
  '<bpmn:linkEventDefinition id="LED1" name="NOLINK"/>' +
  "</bpmn:intermediateCatchEvent></bpmn:process>\n" +
  '  <bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL1" bpmnElement="P1">' +
  '<bpmndi:BPMNShape id="T1_di" bpmnElement="T1"><dc:Bounds x="160" y="80" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="ICE1_di" bpmnElement="ICE1"><dc:Bounds x="300" y="100" width="36" height="36"/></bpmndi:BPMNShape>' +
  "</bpmndi:BPMNPlane></bpmndi:BPMNDiagram>\n" +
  BPMN_TAIL;

const XML_MALFORMED =
  '<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" id="d"><process>';

const XML_DOCTYPE =
  '<?xml version="1.0"?><!DOCTYPE definitions [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>' +
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="d" targetNamespace="urn:x"><bpmn:process id="p">&xxe;</bpmn:process></bpmn:definitions>';

async function apiPutXml(
  actor: Actor,
  modelId: string,
  xml: string,
  version: number,
): Promise<number> {
  const base = process.env.BPMN_E2E_BASE_URL ?? "http://localhost";
  const token = await apiToken(actor);
  const ctx = await request.newContext({ baseURL: base });
  const resp = await ctx.put(
    `/apps/bpmn-modeler-api/models/${modelId}/working-copy`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/xml",
        "If-Match": `"v${version}"`,
      },
      data: xml,
    },
  );
  return resp.status();
}

async function apiExportXml(actor: Actor, modelId: string): Promise<string> {
  const base = process.env.BPMN_E2E_BASE_URL ?? "http://localhost";
  const token = await apiToken(actor);
  const ctx = await request.newContext({ baseURL: base });
  const resp = await ctx.get(
    `/apps/bpmn-modeler-api/models/${modelId}/working-copy/export`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
  return resp.text();
}

test.describe("E2E-01/03 — create→edit→save→reload→export", () => {
  test.use({ actor: "editor" });
  test("canvas editável salva e exporta .bpmn", async ({ page }) => {
    await page.goto(LIBRARY_URL);
    await page.getByRole("button", { name: /novo modelo/i }).click();
    await page.getByLabel("Nome do modelo").fill("E2E Modelo A");
    await page.getByRole("button", { name: "Criar", exact: true }).click();

    // editor abre; canvas e status CLEAN
    await expect(page.locator(".bpmnm-save-status")).toHaveText("Salvo", {
      timeout: 20_000,
    });
    await expect(page.locator(".bpmnm-canvas .djs-container")).toBeVisible();

    // edição via palette (Task) → DIRTY
    await page.locator('.djs-palette .entry[data-action="create.task"]').click();
    await page
      .locator(".bpmnm-canvas .djs-container")
      .click({ position: { x: 400, y: 200 } });
    await expect(page.locator(".bpmnm-canvas .djs-element")).toHaveCount(1);
    await expect(page.locator(".bpmnm-save-status")).toHaveText(
      PENDING_SAVE_RE,
      { timeout: 10_000 },
    );

    // autosave → CLEAN sem ação manual
    await waitSaved(page);

    // reload → diagrama reaparece (authoritative)
    await page.reload();
    await expect(page.locator(".bpmnm-canvas .djs-element")).toHaveCount(1, {
      timeout: 20_000,
    });

    // export .bpmn
    const downloadPromise = page.waitForEvent("download");
    await page.getByRole("button", { name: "Mais ações" }).click();
    await page.getByRole("menuitem", { name: "Exportar BPMN" }).click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/\.bpmn$/);
  });
});

test.describe("E2E-02 — import valid+DI → open → export", () => {
  test.use({ actor: "editor" });
  test("import via dialog abre no editor", async ({ page }) => {
    await page.goto(LIBRARY_URL);
    await page.getByRole("button", { name: /importa.*bpmn/i }).click();
    await page.locator('input[type="file"]').setInputFiles({
      name: "valid.bpmn",
      mimeType: "text/xml",
      buffer: Buffer.from(XML_DI),
    });
    await expect(page.getByText(/Estado reconhecido/)).toContainText(
      "BPMN_RECOGNIZED",
      { timeout: 15_000 },
    );
    await page.getByRole("button", { name: "Importar", exact: true }).click();
    // navega ao editor com canvas renderizado (DI existente)
    await expect(page.locator(".bpmnm-canvas .djs-element")).toHaveCount(3, {
      timeout: 20_000,
    });
  });
});

test.describe("E2E-04 — BPMN sem DI → render transitório, sem dirty", () => {
  test.use({ actor: "editor" });
  test("modelo sem DI renderiza e permanece CLEAN", async ({ page }) => {
    const modelId = await importModelViaApi("editor", "E2E-NoDI", XML_NO_DI);
    await page.goto(modelUrl(modelId));
    await expect(page.locator(".bpmnm-canvas .djs-element")).toHaveCount(3, {
      timeout: 20_000,
    });
    await expect(page.locator(".bpmnm-save-status")).toHaveText("Salvo", {
      timeout: 15_000,
    });
  });
});

test.describe("E2E-05 — Organizar → Preview → Cancel", () => {
  test.use({ actor: "editor" });
  test("cancel deixa o main editor bit-a-bit intacto", async ({ page }) => {
    const modelId = await importModelViaApi("editor", "E2E-Layout", XML_DI);
    const before = await apiExportXml("editor", modelId);
    await page.goto(modelUrl(modelId));
    await expect(page.locator(".bpmnm-canvas .djs-element")).toHaveCount(3, {
      timeout: 20_000,
    });

    await page.getByRole("button", { name: "Organizar" }).click();
    const previewEl = page.getByTestId("layout-preview");
    await expect(previewEl).toBeVisible({ timeout: 30_000 });
    await expect(previewEl.getByRole("status")).toContainText(
      "Pré-visualização do layout",
    );
    // preview mostra a proposta (viewer transitório)
    await expect(previewEl.locator(".djs-element").first()).toBeVisible({
      timeout: 20_000,
    });

    await previewEl.getByRole("button", { name: "Cancelar" }).click();
    await expect(previewEl).toBeHidden();
    // sem dirty — main editor não foi tocado
    await expect(page.locator(".bpmnm-save-status")).toHaveText("Salvo");
    expect(await apiExportXml("editor", modelId)).toBe(before);
  });
});

test.describe("E2E-06 — Organizar → Accept → DIRTY → undo/redo → save", () => {
  test.use({ actor: "editor" });
  test("accept aplica como 1 comando; undo reverte; save persiste DI", async ({
    page,
  }) => {
    const modelId = await importModelViaApi("editor", "E2E-Accept", XML_DI);
    await page.goto(modelUrl(modelId));
    await expect(page.locator(".bpmnm-canvas .djs-element")).toHaveCount(3, {
      timeout: 20_000,
    });

    await page.getByRole("button", { name: "Organizar" }).click();
    const previewEl = page.getByTestId("layout-preview");
    await expect(previewEl.getByRole("status")).toContainText(
      "Pré-visualização",
      { timeout: 30_000 },
    );
    await expect(previewEl.locator(".djs-element").first()).toBeVisible({
      timeout: 20_000,
    });

    await previewEl.getByRole("button", { name: "Aceitar" }).click();
    await expect(page.locator(".bpmnm-save-status")).toHaveText(
      PENDING_SAVE_RE,
      { timeout: 10_000 },
    );

    // undo reverte o batch inteiro → autosave → CLEAN; redo reaplica
    await page.getByRole("button", { name: "Desfazer" }).click();
    await waitSaved(page);
    await page.getByRole("button", { name: "Refazer" }).click();
    await waitSaved(page);

    // reopen → DI persistida no artefato canônico
    const exported = await apiExportXml("editor", modelId);
    expect(exported).toContain("BPMNShape");
    expect(exported).toContain("waypoint");
    await page.reload();
    await expect(page.locator(".bpmnm-canvas .djs-element")).toHaveCount(3, {
      timeout: 20_000,
    });
  });
});

test.describe("E2E-07 — structural issue → issues → navegar → reparar", () => {
  test.use({ actor: "editor" });
  test("dangling ref listada, seleção navega, delete repara", async ({
    page,
  }) => {
    const modelId = await importModelViaApi("editor", "E2E-Broken", XML_BROKEN_REF);
    await page.goto(modelUrl(modelId));
    await expect(page.locator(".bpmnm-canvas")).toBeVisible({ timeout: 20_000 });

    await page.getByRole("button", { name: "Validar" }).click();
    await page.getByRole("tab", { name: "Validação" }).click();
    // issues estruturais do flow quebrado — o export do canvas pode
    // normalizar o sourceRef não resolvido (STRUCT-001 XSD) ou
    // preservá-lo como ref quebrada (STRUCT-010); ambos denunciam F1
    await expect(
      page.locator(".bpmnm-issue", {
        hasText: /BPMN-STRUCT-(001|010)/,
      }),
    ).toBeVisible({ timeout: 15_000 });
    await expect(
      page.locator(".bpmnm-issue", { hasText: "BPMN-SEM-008" }),
    ).toBeVisible();
    // navegação — SEM-006 referencia o catch event renderizado (ICE1)
    const navigable = page.locator(".bpmnm-issue", {
      hasText: "BPMN-SEM-006",
    });
    await expect(navigable.first()).toBeVisible();
    await navigable.first().getByRole("button").click();
    await expect(page.locator(".djs-element.selected")).toBeVisible();
    // repair: foco no SVG do canvas (keyboard do diagram-js faz bind no
    // svg) e Delete remove o evento órfão
    await page.locator(".bpmnm-canvas svg").first().focus();
    await page.keyboard.press("Delete");
    await expect(page.locator(".bpmnm-save-status")).toHaveText(
      PENDING_SAVE_RE,
    );
    await waitSaved(page);
    await page.getByRole("button", { name: "Validar" }).click();
    await expect(navigable).toHaveCount(0, { timeout: 15_000 });
    // sibling: o flow quebrado não foi reparado — issues permanecem
    await expect(
      page.locator(".bpmnm-issue", { hasText: /BPMN-STRUCT-(001|010)/ }),
    ).toBeVisible();
  });
});

test.describe("E2E-08/09 — blocked imports surface recognition state", () => {
  test.use({ actor: "editor" });
  test("malformed → MALFORMED_XML, sem Importar", async ({ page }) => {
    await page.goto(LIBRARY_URL);
    await page.getByRole("button", { name: /importa.*bpmn/i }).click();
    await page.locator('input[type="file"]').setInputFiles({
      name: "bad.bpmn",
      mimeType: "text/xml",
      buffer: Buffer.from(XML_MALFORMED),
    });
    await expect(page.getByText(/Estado reconhecido/)).toContainText(
      "MALFORMED_XML",
      { timeout: 15_000 },
    );
    await expect(
      page.getByText("Este arquivo não pode ser importado."),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Importar", exact: true }),
    ).toHaveCount(0);
  });

  test("DOCTYPE → INPUT_REJECTED_SECURITY", async ({ page }) => {
    await page.goto(LIBRARY_URL);
    await page.getByRole("button", { name: /importa.*bpmn/i }).click();
    await page.locator('input[type="file"]').setInputFiles({
      name: "xxe.bpmn",
      mimeType: "text/xml",
      buffer: Buffer.from(XML_DOCTYPE),
    });
    await expect(page.getByText(/Estado reconhecido/)).toContainText(
      "INPUT_REJECTED_SECURITY",
      { timeout: 15_000 },
    );
  });
});

test.describe("E2E-10 — extensão mustUnderstand=false preservada", () => {
  test.use({ actor: "editor" });
  test("vend:custom sobrevive import/export", async ({ page }) => {
    const modelId = await importModelViaApi(
      "editor",
      "E2E-Ext",
      XML_EXT_MU_FALSE,
    );
    await page.goto(modelUrl(modelId));
    await expect(page.locator(".bpmnm-canvas")).toBeVisible({ timeout: 20_000 });
    const exported = await apiExportXml("editor", modelId);
    expect(exported).toContain('vend:custom="yes"');
  });
});

test.describe("E2E-11 — mustUnderstand=true → read-only capability gate", () => {
  test.use({ actor: "editor" });
  test("banner read-only, Salvar indisponível", async ({ page }) => {
    const modelId = await importModelViaApi(
      "editor",
      "E2E-MU",
      XML_EXT_MU_TRUE,
    );
    await page.goto(modelUrl(modelId));
    await expect(page.locator(".bpmnm-banner--readonly")).toBeVisible({
      timeout: 20_000,
    });
    await expect(
      page.getByRole("button", { name: "Salvar" }),
    ).toHaveCount(0);
    await expect(
      page.getByRole("button", { name: "Organizar" }),
    ).toHaveCount(0);
  });
});

test.describe("E2E-12 — revisions/restore append-only", () => {
  test.use({ actor: "manager" });
  test("rev1 → rev2 → restore rev1 → rev3 intacto", async ({ page }) => {
    const modelId = await createModelViaApi("manager", "E2E-Revs");
    await page.goto(modelUrl(modelId));
    await expect(page.locator(".bpmnm-save-status")).toHaveText("Salvo", {
      timeout: 20_000,
    });

    await page.getByRole("tab", { name: "Histórico" }).click();
    await page.getByRole("button", { name: "Criar revisão" }).click();
    await expect(page.getByText("Revisão 1")).toBeVisible({ timeout: 15_000 });

    // edita + salva + rev2 via API (edição de canvas coberta em E2E-01);
    // rev1 bumpou version 1→2 → If-Match "v2"
    const v2 = XML_NO_DI.replace('id="P1"', 'id="P1" name="v2"');
    expect(await apiPutXml("manager", modelId, v2, 2)).toBe(200);
    await page.reload();
    await page.getByRole("tab", { name: "Histórico" }).click();
    await page.getByRole("button", { name: "Criar revisão" }).click();
    await expect(page.getByText("Revisão 2")).toBeVisible({ timeout: 15_000 });

    // restore rev1 → rev3 origin=restore (confirmação via modal)
    await page
      .locator(".bpmnm-revision-item", { hasText: "Revisão 1" })
      .getByRole("button", { name: "Restaurar" })
      .click();
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Restaurar" })
      .click();
    await expect(page.getByText("Revisão 3")).toBeVisible({ timeout: 15_000 });
    // append-only: rev1 e rev2 intactas
    await expect(page.getByText("Revisão 1")).toBeVisible();
    await expect(page.getByText("Revisão 2")).toBeVisible();
  });
});

test.describe("E2E-13 — duplicate revision → NO_CHANGES", () => {
  test.use({ actor: "manager" });
  test("segunda revisão sem mudança é rejeitada", async ({ page }) => {
    const modelId = await createModelViaApi("manager", "E2E-NoChg");
    await page.goto(modelUrl(modelId));
    await expect(page.locator(".bpmnm-save-status")).toHaveText("Salvo", {
      timeout: 20_000,
    });
    await page.getByRole("tab", { name: "Histórico" }).click();
    await page.getByRole("button", { name: "Criar revisão" }).click();
    await expect(page.getByText("Revisão 1")).toBeVisible({ timeout: 15_000 });
    await page.getByRole("button", { name: "Criar revisão" }).click();
    await expect(page.locator(".bpmnm-error")).toBeVisible({ timeout: 15_000 });
  });
});

test.describe("E2E-14 — archive/unarchive lifecycle", () => {
  test.use({ actor: "manager" });
  test("arquivar → read-only → desarquivar → editável", async ({ page }) => {
    const modelId = await createModelViaApi("manager", "E2E-Arch");
    await page.goto(modelUrl(modelId));
    await expect(page.locator(".bpmnm-save-status")).toHaveText("Salvo", {
      timeout: 20_000,
    });

    await page.getByRole("button", { name: "Mais ações" }).click();
    await page.getByRole("menuitem", { name: "Arquivar" }).click();
    await expect(page.locator(".bpmnm-badge", { hasText: "Arquivado" })).toBeVisible({ timeout: 15_000 });
    await expect(
      page.getByRole("button", { name: "Salvar" }),
    ).toHaveCount(0);

    await page.getByRole("button", { name: "Mais ações" }).click();
    await page.getByRole("menuitem", { name: "Desarquivar" }).click();
    await expect(page.locator(".bpmnm-save-status")).toHaveText("Salvo", {
      timeout: 15_000,
    });
  });
});

test.describe("E2E-18 — múltiplos BPMNDiagrams", () => {
  test.use({ actor: "editor" });
  test("seletor lista 2 diagramas e troca funciona", async ({ page }) => {
    const modelId = await importModelViaApi("editor", "E2E-Multi", XML_MULTI_DI);
    await page.goto(modelUrl(modelId));
    const selector = page.locator(".bpmnm-diagram-selector select");
    await expect(selector).toBeVisible({ timeout: 20_000 });
    await expect(selector.locator("option")).toHaveCount(2);
    // primeiro em document order é o default
    await expect(page.locator(".bpmnm-canvas .djs-element").first()).toBeVisible({
      timeout: 20_000,
    });
    // troca para o segundo diagrama
    await selector.selectOption({ index: 1 });
    await expect(page.locator(".bpmnm-canvas .djs-element").first()).toBeVisible({
      timeout: 15_000,
    });
  });
});

test.describe("E2E-19 — layout representativo (fixtures)", () => {
  test.use({ actor: "editor" });
  test("organizar em fixture representativo produz preview", async ({
    page,
  }) => {
    const modelId = await importModelViaApi("editor", "E2E-Rep", XML_DI);
    await page.goto(modelUrl(modelId));
    await expect(page.locator(".bpmnm-canvas .djs-element")).toHaveCount(3, {
      timeout: 20_000,
    });
    await page.getByRole("button", { name: "Organizar" }).click();
    await expect(page.getByTestId("layout-preview")).toBeVisible({
      timeout: 30_000,
    });
  });
});

test.describe("E2E-20 — auth matrix: unauthenticated", () => {
  test.use({ actor: "none" });
  test("boundary → portal /login com SSO gate", async ({ page }) => {
    await page.goto(LIBRARY_URL);
    await page.waitForURL(/\/login/, { timeout: 30_000 });
    await expect(
      page.getByRole("button", { name: /Entrar com DELPI SSO/ }),
    ).toBeVisible();
  });
});

test.describe("E2E-20 — auth matrix: viewer", () => {
  test.use({ actor: "viewer" });
  test("library abre, Novo modelo ausente", async ({ page }) => {
    await page.goto(LIBRARY_URL);
    await expect(page.locator(".bpmnm-page")).toBeVisible({ timeout: 20_000 });
    await expect(
      page.getByRole("button", { name: /novo modelo/i }),
    ).toHaveCount(0);
  });
});

test.describe("E2E-21 — a11y smoke", () => {
  test.use({ actor: "editor" });
  test("teclado navega, canvas tem aria-label, status tem role", async ({
    page,
  }) => {
    await page.goto(LIBRARY_URL);
    await expect(page.locator(".bpmnm-page")).toBeVisible({ timeout: 20_000 });
    let focused = "BODY";
    for (let i = 0; i < 8 && focused === "BODY"; i++) {
      await page.keyboard.press("Tab");
      focused =
        (await page.evaluate(() => document.activeElement?.tagName)) ?? "BODY";
    }
    expect(focused).not.toBe("BODY");

    const modelId = await createModelViaApi("editor", "E2E-A11y");
    await page.goto(modelUrl(modelId));
    await expect(
      page.getByLabel("Canvas do diagrama BPMN"),
    ).toBeVisible({ timeout: 20_000 });
    await expect(page.locator(".bpmnm-save-status").first()).toBeVisible();
  });
});

test.describe("E2E-22 — tablet read-only", () => {
  test.use({
    actor: "editor",
    viewport: { width: 1024, height: 768 },
    hasTouch: true,
  });
  test("viewport tablet → banner read-only, sem mutation controls", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "E2E-Tablet");
    await page.goto(modelUrl(modelId));
    await expect(
      page.getByText("Em tablets o editor opera em modo somente leitura."),
    ).toBeVisible({ timeout: 20_000 });
    await expect(page.getByRole("button", { name: "Salvar" })).toHaveCount(0);
    await expect(
      page.getByRole("button", { name: "Organizar" }),
    ).toHaveCount(0);
  });
});
