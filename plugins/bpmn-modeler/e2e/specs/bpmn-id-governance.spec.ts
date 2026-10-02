import { test, expect, waitSaved, importModelViaApi, modelUrl, apiToken } from "../helpers";
import { request } from "@playwright/test";
import type { Page } from "@playwright/test";
import path from "node:path";
import fs from "node:fs";

/**
 * E2E-45 — BPMN ID governance + collapse control + properties visual parity.
 *
 * O `id` BPMN é propriedade técnica: fica no grupo "Configurações avançadas"
 * (provider oficial, `propertiesPanel.registerProvider`), com label
 * "ID BPMN" e help. Toda edição passa pelo command stack vendor
 * (undo/redo/save read-back) — o produto não cria form paralelo.
 *
 * `Model.id` da API é autoridade separada: mudar o BPMN id nunca altera
 * model_id nem revision identity.
 */

const XML_ID =
  '<?xml version="1.0" encoding="UTF-8"?>' +
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ' +
  'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" ' +
  'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" ' +
  'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" ' +
  'id="defs_id" targetNamespace="urn:id">' +
  '<bpmn:process id="P1" isExecutable="false" name="Processo de Compras">' +
  '<bpmn:startEvent id="S1"/><bpmn:task id="T1" name="Tarefa"/><bpmn:endEvent id="E1"/>' +
  '<bpmn:sequenceFlow id="F1" sourceRef="S1" targetRef="T1"/>' +
  '<bpmn:sequenceFlow id="F2" sourceRef="T1" targetRef="E1"/>' +
  '</bpmn:process>' +
  '<bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL1" bpmnElement="P1">' +
  '<bpmndi:BPMNShape id="S1_di" bpmnElement="S1"><dc:Bounds x="140" y="140" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="T1_di" bpmnElement="T1"><dc:Bounds x="240" y="120" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="E1_di" bpmnElement="E1"><dc:Bounds x="400" y="140" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNEdge id="F1_di" bpmnElement="F1"><di:waypoint x="176" y="158"/><di:waypoint x="240" y="158"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="F2_di" bpmnElement="F2"><di:waypoint x="340" y="158"/><di:waypoint x="400" y="158"/></bpmndi:BPMNEdge>' +
  '</bpmndi:BPMNPlane></bpmndi:BPMNDiagram></bpmn:definitions>';

const XML_POOL =
  '<?xml version="1.0" encoding="UTF-8"?>' +
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ' +
  'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" ' +
  'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" ' +
  'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" ' +
  'id="defs_pool" targetNamespace="urn:pool">' +
  '<bpmn:collaboration id="C1"><bpmn:participant id="PA1" name="Pool" processRef="P1"/></bpmn:collaboration>' +
  '<bpmn:process id="P1" isExecutable="false"><bpmn:startEvent id="S1"/><bpmn:task id="T1"/>' +
  '<bpmn:sequenceFlow id="F1" sourceRef="S1" targetRef="T1"/></bpmn:process>' +
  '<bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL1" bpmnElement="C1">' +
  '<bpmndi:BPMNShape id="PA1_di" bpmnElement="PA1" isHorizontal="true"><dc:Bounds x="100" y="80" width="600" height="300"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="S1_di" bpmnElement="S1"><dc:Bounds x="160" y="150" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="T1_di" bpmnElement="T1"><dc:Bounds x="280" y="130" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNEdge id="F1_di" bpmnElement="F1"><di:waypoint x="196" y="168"/><di:waypoint x="280" y="168"/></bpmndi:BPMNEdge>' +
  '</bpmndi:BPMNPlane></bpmndi:BPMNDiagram></bpmn:definitions>';

const SHOTS = path.resolve(import.meta.dirname, "../../.tmp-shots");

async function openEditor(page: Page, theme: "light" | "dark" = "dark", xml = XML_ID) {
  await page.evaluate((t) => {
    localStorage.setItem("theme", t);
    document.documentElement.setAttribute("data-theme", t);
  }, theme);
  const modelId = await importModelViaApi("editor", "E2E-BpmnId", xml);
  await page.goto(modelUrl(modelId));
  await expect(
    page.locator('.djs-element[data-element-id="T1"]'),
  ).toBeVisible({ timeout: 20_000 });
  await page.waitForTimeout(800);
  return modelId;
}

async function shot(page: Page, name: string) {
  fs.mkdirSync(SHOTS, { recursive: true });
  await page.screenshot({ path: path.join(SHOTS, `${name}.png`) });
}

/** Seleciona o processo raiz clicando em área vazia do canvas. */
async function selectRoot(page: Page) {
  await page.keyboard.press("Escape");
  const cv = await page.locator(".bpmnm-canvas").boundingBox();
  if (!cv) throw new Error("canvas not found");
  await page.mouse.click(cv.x + cv.width - 60, cv.y + cv.height - 60);
  await page.waitForTimeout(500);
}

const advancedGroupHeader = (page: Page) =>
  page.locator('[data-group-id="group-advanced"] .bio-properties-panel-group-header-title');

const advancedGroup = (page: Page) =>
  page.locator('[data-group-id="group-advanced"]');

const idInput = (page: Page, entryId = "id") =>
  page.locator(`[data-entry-id="${entryId}"] input`).first();

async function expandAdvanced(page: Page) {
  const header = advancedGroupHeader(page);
  await expect(header).toBeVisible();
  const open = await advancedGroup(page)
    .locator(".bio-properties-panel-group-header.open")
    .count();
  if (!open) {
    await header.click();
    await page.waitForTimeout(400);
  }
}

async function readBackXml(modelId: string): Promise<string> {
  const base = process.env.BPMN_E2E_BASE_URL ?? "http://localhost";
  const token = await apiToken("editor");
  const ctx = await request.newContext({ baseURL: base });
  const resp = await ctx.get(
    `/apps/bpmn-modeler-api/models/${modelId}/working-copy`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
  if (!resp.ok()) throw new Error(`read-back failed: ${resp.status()}`);
  return resp.text();
}

test.describe("E2E-45 — BPMN ID governance", () => {
  test.use({ actor: "editor", viewport: { width: 1440, height: 900 } });

  test("IDG-01: ID BPMN vive em Configurações avançadas — Geral tem Nome", async ({
    page,
  }) => {
    await openEditor(page);
    await selectRoot(page);

    // header do elemento = tipo PT-BR
    await expect(
      page.locator(".bio-properties-panel-header-type"),
    ).toHaveText("Processo");

    // Geral: Nome + Executável, sem ID
    const general = page.locator('[data-group-id="group-general"]');
    await expect(general.getByText("Nome", { exact: true })).toBeVisible();
    await expect(general).not.toContainText("ID BPMN");

    // avançado: fechado por padrão, contém ID BPMN ao expandir
    await expandAdvanced(page);
    await expect(
      page.locator('[data-entry-id="id"]'),
    ).toContainText("ID BPMN");
    await expect(idInput(page)).toHaveValue("P1");
    await shot(page, "bpmn-id-advanced-dark");
    await shot(page, "properties-process-dark");

    // focus ring no field técnico
    await idInput(page).focus();
    await page.waitForTimeout(200);
    await shot(page, "bpmn-id-focus");
  });

  test("IDG-02: editar ID → undo/redo via command stack → save → read-back XML", async ({
    page,
  }) => {
    const modelId = await openEditor(page);
    await selectRoot(page);
    await expandAdvanced(page);

    await idInput(page).fill("Proc_Compras");
    await page.keyboard.press("Tab"); // blur → commit vendor debounce // blur → commit
    await page.waitForTimeout(400);

    // dirty state + read-back já no modeler em memória
    const undo = page.locator('button[aria-label="Desfazer"]');
    await expect(undo).toBeEnabled();

    await undo.click();
    await page.waitForTimeout(300);
    await expect(idInput(page)).toHaveValue("P1");

    await page.locator('button[aria-label="Refazer"]').click();
    await page.waitForTimeout(300);
    await expect(idInput(page)).toHaveValue("Proc_Compras");

    // save → authoritative read-back pela API
    // autosave: write → read-back → Salvo
    await waitSaved(page);

    const xml = await readBackXml(modelId);
    expect(xml).toContain('id="Proc_Compras"');
    expect(xml).not.toContain('id="P1"');

    // model_id (autoridade da API) NÃO mudou
    expect(page.url()).toContain(`/models/${modelId}`);
    const xml2 = await readBackXml(modelId);
    expect(xml2).toContain('id="Proc_Compras"');
  });

  test("IDG-03: validação vendor — duplicado, vazio, léxico", async ({ page }) => {
    await openEditor(page);
    await selectRoot(page);
    await expandAdvanced(page);
    const field = page.locator('[data-entry-id="id"]');

    // duplicado
    await idInput(page).fill("T1");
    await page.waitForTimeout(600);
    await expect(field).toContainText("O ID deve ser único");

    // vazio
    await idInput(page).fill("");
    await page.waitForTimeout(600);
    await expect(field).toContainText("O ID não pode ficar vazio");

    // léxico: espaço e prefixo numérico rejeitados
    await idInput(page).fill("Process Compras");
    await page.waitForTimeout(600);
    await expect(field).toContainText("O ID não pode conter espaços");

    await idInput(page).fill("123Process");
    await page.waitForTimeout(600);
    await expect(field).toContainText(/QName|válido/);

    // valor válido: erro some
    await idInput(page).fill("Process_Compras");
    await page.waitForTimeout(600);
    await expect(field).not.toContainText("O ID");
    await shot(page, "bpmn-id-valid-dark");
  });

  test("IDG-04: rename de task propaga sourceRef/targetRef/bpmnElement no XML", async ({
    page,
  }) => {
    const modelId = await openEditor(page);
    await page
      .locator('.djs-element[data-element-id="T1"]')
      .click({ position: { x: 30, y: 30 }, force: true });
    await page.waitForTimeout(600);
    await shot(page, "properties-task-dark");
    await expandAdvanced(page);
    await idInput(page).fill("T1_Renamed");
    await page.keyboard.press("Tab"); // blur → commit vendor debounce
    await page.waitForTimeout(400);

    // autosave: write → read-back → Salvo
    await waitSaved(page);

    const xml = await readBackXml(modelId);
    expect(xml).toContain('id="T1_Renamed"');
    // referências internas re-apontadas (moddle → serialize)
    expect(xml).toContain('targetRef="T1_Renamed"');
    expect(xml).toContain('sourceRef="T1_Renamed"');
    // BPMN-DI coerente
    expect(xml).toContain('bpmnElement="T1_Renamed"');
    expect(xml).not.toMatch(/(sourceRef|targetRef|bpmnElement)="T1"/);
  });

  test("IDG-05: processId via participant → processRef coerente no XML", async ({
    page,
  }) => {
    const modelId = await openEditor(page, "dark", XML_POOL);
    await page
      .locator('.djs-element[data-element-id="PA1"]')
      .click({ position: { x: 40, y: 40 }, force: true });
    await page.waitForTimeout(600);
    await expandAdvanced(page);

    const procId = page.locator('[data-entry-id="processId"] input').first();
    await expect(procId).toHaveValue("P1");
    await procId.fill("P_V2");
    await page.keyboard.press("Tab"); // blur → commit vendor debounce
    await page.waitForTimeout(400);

    // autosave: write → read-back → Salvo
    await waitSaved(page);

    const xml = await readBackXml(modelId);
    expect(xml).toContain('id="P_V2"');
    expect(xml).toContain('processRef="P_V2"');
    expect(xml).not.toContain('processRef="P1"');
  });
});

test.describe("E2E-45b — collapse control estrutural", () => {
  test.use({ actor: "editor", viewport: { width: 1440, height: 900 } });

  test("SID-01: controle de recolher é célula separada das tabs", async ({
    page,
  }) => {
    await openEditor(page);
    const cell = page.locator(".bpmnm-side__collapse");
    await expect(cell).toBeVisible();
    // divisória vertical separa o controle das tabs
    const border = await cell.evaluate(
      (el) => getComputedStyle(el).borderInlineStartWidth,
    );
    expect(border).toBe("1px");
    // ordem do DOM: tabs antes do controle
    const order = await page.evaluate(() => {
      const head = document.querySelector(".bpmnm-side__head")!;
      const kids = [...head.children].map((c) => c.className);
      return kids.join("|");
    });
    expect(order).toContain("bpmnm-side__tabs");
    expect(order.indexOf("bpmnm-side__collapse")).toBeGreaterThan(
      order.indexOf("bpmnm-side__tabs"),
    );
    await shot(page, "sidebar-expanded-control-dark");

    // collapsed rail: expander → separador → 3 tabs, todos IconButton
    await page.locator('button[aria-label="Recolher painel lateral"]').click();
    await page.waitForTimeout(400);
    const rail = page.locator(".bpmnm-side__rail");
    expect(await rail.locator("button").count()).toBe(4);
    await expect(page.locator(".bpmnm-side__rail-sep")).toBeVisible();
    const sepBox = await page.locator(".bpmnm-side__rail-sep").boundingBox();
    const railBox = await rail.boundingBox();
    expect(sepBox!.width).toBeGreaterThan(railBox!.width * 0.6);
    await shot(page, "sidebar-collapsed-control-dark");

    await page.locator('button[aria-label="Expandir painel lateral"]').click();
    await page.waitForTimeout(400);
  });

  test("SID-03: responsivo — collapse control íntegro em 1366–1920", async ({
    page,
  }) => {
    await openEditor(page);
    for (const width of [1920, 1600, 1440, 1366]) {
      await page.setViewportSize({ width, height: 900 });
      await page.waitForTimeout(300);
      await expect(
        page.locator('button[aria-label="Recolher painel lateral"]'),
      ).toBeVisible();
      const scrollW = await page.evaluate(
        () => document.documentElement.scrollWidth,
      );
      const innerW = await page.evaluate(() => innerWidth);
      expect(scrollW).toBeLessThanOrEqual(innerW);
      await page.locator('button[aria-label="Recolher painel lateral"]').click();
      await page.waitForTimeout(300);
      await expect(
        page.locator('button[aria-label="Expandir painel lateral"]'),
      ).toBeVisible();
      await page.locator('button[aria-label="Expandir painel lateral"]').click();
      await page.waitForTimeout(300);
    }
  });

  test("SID-02: collapse control em light + input parity evidence", async ({
    page,
  }) => {
    await openEditor(page, "light");
    await selectRoot(page);
    await expandAdvanced(page);
    await shot(page, "sidebar-expanded-control-light");
    await shot(page, "properties-process-light");
    // token check: input vendor herda os tokens --delpi-ui-control-*
    const probe = await page.evaluate(() => {
      const input = document.querySelector<HTMLInputElement>(
        '[data-entry-id="name"] input, [data-entry-id="id"] input',
      );
      if (!input) return null;
      const cs = getComputedStyle(input);
      return {
        height: cs.height,
        radius: cs.borderRadius,
        border: cs.borderColor,
        bg: cs.backgroundColor,
      };
    });
    expect(probe).not.toBeNull();
    expect(parseFloat(probe!.radius)).toBeGreaterThanOrEqual(4);
  });

  test("SID-04: browser zoom 110%/125% — labels, help e controle legíveis", async ({
    page,
  }) => {
    await openEditor(page);
    for (const zoom of [1.1, 1.25]) {
      await page.evaluate(
        (z) => ((document.body.style as any).zoom = String(z)),
        zoom,
      );
      await page.waitForTimeout(300);
      await selectRoot(page);
      await expandAdvanced(page);
      await expect(idInput(page)).toBeVisible();
      await expect(
        page.locator('button[aria-label="Recolher painel lateral"]'),
      ).toBeVisible();
      const scrollW = await page.evaluate(
        () => document.documentElement.scrollWidth,
      );
      const innerW = await page.evaluate(() => innerWidth);
      expect(scrollW).toBeLessThanOrEqual(innerW + 2);
    }
    await shot(page, "bpmn-id-help-zoom125");
  });
});
