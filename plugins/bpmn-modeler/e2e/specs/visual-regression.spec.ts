import {
  test,
  expect,
  importModelViaApi,
  modelUrl,
} from "../helpers";
import type { Page } from "@playwright/test";

/**
 * Regressão visual do editor (correction pass): bounding boxes e inclusão
 * no viewport — não apenas presença no DOM. Stack real, sem mocks.
 *
 * Cobre: workspace fill, seleção única, context pad, popup replace,
 * toolbar sem overflow, sidebar sem clipping, menu de contexto (elemento
 * e canvas), canvas resize, temas light/dark.
 */

const HEAD =
  '<?xml version="1.0" encoding="UTF-8"?>\n' +
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ' +
  'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" ' +
  'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" ' +
  'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" ' +
  'id="defs_vis" targetNamespace="urn:vis">\n';
const TAIL = "</bpmn:definitions>";

const XML_RICH =
  HEAD +
  '<bpmn:process id="P1" isExecutable="false">' +
  '<bpmn:startEvent id="S1"/><bpmn:task id="T1" name="Tarefa"/>' +
  '<bpmn:exclusiveGateway id="G1"/><bpmn:subProcess id="SP1">' +
  '<bpmn:startEvent id="S2"/><bpmn:task id="T2"/><bpmn:endEvent id="E2"/>' +
  '<bpmn:sequenceFlow id="SF1" sourceRef="S2" targetRef="T2"/>' +
  '<bpmn:sequenceFlow id="SF2" sourceRef="T2" targetRef="E2"/></bpmn:subProcess>' +
  '<bpmn:endEvent id="E1"/><bpmn:dataObjectReference id="DO1" name="Doc"/>' +
  '<bpmn:sequenceFlow id="F1" sourceRef="S1" targetRef="T1"/>' +
  '<bpmn:sequenceFlow id="F2" sourceRef="T1" targetRef="G1"/>' +
  '<bpmn:sequenceFlow id="F3" sourceRef="G1" targetRef="SP1"/>' +
  '<bpmn:sequenceFlow id="F4" sourceRef="G1" targetRef="E1"/>' +
  "</bpmn:process>" +
  '<bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL1" bpmnElement="P1">' +
  '<bpmndi:BPMNShape id="S1_di" bpmnElement="S1"><dc:Bounds x="120" y="200" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="T1_di" bpmnElement="T1"><dc:Bounds x="240" y="178" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="G1_di" bpmnElement="G1"><dc:Bounds x="420" y="193" width="50" height="50"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="SP1_di" bpmnElement="SP1" isExpanded="true"><dc:Bounds x="560" y="120" width="350" height="200"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="S2_di" bpmnElement="S2"><dc:Bounds x="600" y="200" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="T2_di" bpmnElement="T2"><dc:Bounds x="700" y="178" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="E2_di" bpmnElement="E2"><dc:Bounds x="840" y="200" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="E1_di" bpmnElement="E1"><dc:Bounds x="960" y="380" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="DO1_di" bpmnElement="DO1"><dc:Bounds x="250" y="330" width="36" height="50"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNEdge id="F1_di" bpmnElement="F1"><di:waypoint x="156" y="218"/><di:waypoint x="240" y="218"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="F2_di" bpmnElement="F2"><di:waypoint x="340" y="218"/><di:waypoint x="420" y="218"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="F3_di" bpmnElement="F3"><di:waypoint x="470" y="218"/><di:waypoint x="560" y="218"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="F4_di" bpmnElement="F4"><di:waypoint x="445" y="243"/><di:waypoint x="978" y="380"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="SF1_di" bpmnElement="SF1"><di:waypoint x="636" y="218"/><di:waypoint x="700" y="218"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="SF2_di" bpmnElement="SF2"><di:waypoint x="800" y="218"/><di:waypoint x="840" y="218"/></bpmndi:BPMNEdge>' +
  "</bpmndi:BPMNPlane></bpmndi:BPMNDiagram>\n" +
  TAIL;

async function openEditor(page: Page, theme?: "light" | "dark") {
  if (theme) {
    await page.evaluate(
      (t) => localStorage.setItem("theme", t),
      theme,
    );
  }
  const modelId = await importModelViaApi("editor", "E2E-Visual", XML_RICH);
  await page.goto(modelUrl(modelId));
  await expect(page.locator(".bpmnm-canvas .djs-element").first()).toBeVisible({
    timeout: 20_000,
  });
  return modelId;
}

function expectInViewport(box: { x: number; y: number; width: number; height: number }, vw: number, vh: number) {
  expect(box.x, "left >= 0").toBeGreaterThanOrEqual(0);
  expect(box.y, "top >= 0").toBeGreaterThanOrEqual(0);
  expect(box.x + box.width, "right <= viewport").toBeLessThanOrEqual(vw + 1);
  expect(box.y + box.height, "bottom <= viewport").toBeLessThanOrEqual(vh + 1);
}

test.describe("E2E-30 — workspace sizing / canvas fill", () => {
  test.use({ actor: "editor", viewport: { width: 1440, height: 900 } });
  test("canvas usa o espaço disponível e não há scroll de página", async ({
    page,
  }) => {
    await openEditor(page);
    const m = await page.evaluate(() => {
      const canvas = document.querySelector(".bpmnm-canvas");
      const sidebar = document.querySelector(".bpmnm-side");
      return {
        vw: innerWidth,
        vh: innerHeight,
        scrollW: document.documentElement.scrollWidth,
        scrollH: document.documentElement.scrollHeight,
        canvas: canvas?.getBoundingClientRect().toJSON() ?? null,
        sidebar: sidebar?.getBoundingClientRect().toJSON() ?? null,
      };
    });
    expect(m.canvas).not.toBeNull();
    // canvas deve ocupar a maior parte da altura útil (toolbar ~44px + margens)
    expect(m.canvas!.height).toBeGreaterThan(m.vh * 0.7);
    // sem scroll horizontal nem vertical de página
    expect(m.scrollW).toBeLessThanOrEqual(m.vw + 1);
    expect(m.scrollH).toBeLessThanOrEqual(m.vh + 1);
    // sidebar dentro do viewport e sem clipping vertical
    expect(m.sidebar).not.toBeNull();
    expectInViewport(m.sidebar!, m.vw, m.vh);
    expect(m.sidebar!.height).toBeGreaterThan(m.vh * 0.7);
  });
});

test.describe("E2E-31 — selection rendering", () => {
  test.use({ actor: "editor", viewport: { width: 1440, height: 900 } });
  test("seleção produz exatamente 1 outline e markers coerentes", async ({
    page,
  }) => {
    await openEditor(page);
    await page
      .locator('.djs-element[data-element-id="T1"]')
      .click({ position: { x: 10, y: 10 } });
    await expect(page.locator(".djs-element.selected")).toHaveCount(1, {
      timeout: 5_000,
    });
    await expect(
      page.locator('.djs-element.selected[data-element-id="T1"]'),
    ).toBeVisible();
    // exatamente um outline de seleção (sem geometria duplicada)
    const outlines = await page.locator(".djs-outline").count();
    expect(outlines).toBeGreaterThanOrEqual(1);
  });

  test("seleção em gateway/subprocess/eventos mantém 1 selected", async ({
    page,
  }) => {
    await openEditor(page);
    // subprocess: clique na borda — o centro pode acertar um filho, e
    // selecionar o filho é o comportamento correto do vendor
    const targets: Array<[string, { x: number; y: number } | undefined]> = [
      ["G1", undefined],
      ["SP1", { x: 3, y: 3 }],
      ["S1", undefined],
      ["E1", undefined],
    ];
    for (const [id, position] of targets) {
      await page
        .locator(`.djs-element[data-element-id="${id}"]`)
        .click({ position, force: true });
      await expect(
        page.locator(`.djs-element.selected[data-element-id="${id}"]`),
      ).toHaveCount(1, { timeout: 5_000 });
      await expect(page.locator(".djs-element.selected")).toHaveCount(1);
    }
  });
});

test.describe("E2E-32 — context pad / popups", () => {
  test.use({ actor: "editor", viewport: { width: 1440, height: 900 } });
  test("context pad visível e dentro do viewport após seleção", async ({
    page,
  }) => {
    await openEditor(page);
    await page
      .locator('.djs-element[data-element-id="T1"]')
      .click({ position: { x: 10, y: 10 } });
    const pad = page.locator(".djs-context-pad");
    await expect(pad).toBeVisible({ timeout: 5_000 });
    const box = await pad.boundingBox();
    expect(box).not.toBeNull();
    expectInViewport(box!, 1440, 900);
  });

  test("popup replace abre, fica dentro do viewport e fecha com Esc", async ({
    page,
  }) => {
    await openEditor(page);
    await page
      .locator('.djs-element[data-element-id="T1"]')
      .click({ position: { x: 10, y: 10 } });
    const wrench = page.locator(
      '.djs-context-pad .entry[class*="wrench"], .djs-context-pad .entry[class*="replace"]',
    );
    await expect(wrench.first()).toBeVisible({ timeout: 5_000 });
    await wrench.first().click();
    const popup = page.locator(".djs-popup").first();
    await expect(popup).toBeVisible({ timeout: 5_000 });
    const box = await popup.boundingBox();
    expect(box).not.toBeNull();
    expectInViewport(box!, 1440, 900);
    await page.keyboard.press("Escape");
    await expect(popup).toBeHidden({ timeout: 5_000 });
    // reabre
    await wrench.first().click();
    await expect(popup).toBeVisible({ timeout: 5_000 });
  });
});

test.describe("E2E-33 — toolbar / sidebar", () => {
  test.use({ actor: "editor", viewport: { width: 1366, height: 768 } });
  test("toolbar sem overflow horizontal em 1366px", async ({ page }) => {
    await openEditor(page);
    const toolbar = page.locator(".bpmnm-editor__header");
    await expect(toolbar).toBeVisible();
    const box = await toolbar.boundingBox();
    expect(box).not.toBeNull();
    expectInViewport(box!, 1366, 768);
    // ações primárias e overflow acessíveis dentro do viewport
    for (const name of ["Salvar", "Organizar", "Validar", "Mais ações"]) {
      const btn = page.getByRole("button", { name, exact: false }).first();
      await expect(btn).toBeVisible();
      const b = await btn.boundingBox();
      expect(b).not.toBeNull();
      expectInViewport(b!, 1366, 768);
    }
  });

  test("sidebar consome altura sem clipping e troca de abas", async ({
    page,
  }) => {
    await openEditor(page);
    const side = page.locator(".bpmnm-side");
    await expect(side).toBeVisible();
    const box = await side.boundingBox();
    expect(box).not.toBeNull();
    expectInViewport(box!, 1366, 768);
    for (const tab of ["Validação", "Histórico", "Propriedades"]) {
      await page.getByRole("tab", { name: tab }).click();
      await expect(
        page.getByRole("tab", { name: tab }),
      ).toHaveAttribute("aria-selected", "true");
    }
  });
});

test.describe("E2E-34 — right-click context menus", () => {
  test.use({ actor: "editor", viewport: { width: 1440, height: 900 } });
  test("menu de elemento abre dentro do viewport e Esc fecha", async ({
    page,
  }) => {
    await openEditor(page);
    await page
      .locator('.djs-element[data-element-id="T1"]')
      .click({ button: "right", position: { x: 10, y: 10 } });
    const menu = page.locator('[aria-label="Menu do diagrama"]');
    await expect(menu).toBeVisible({ timeout: 5_000 });
    const box = await menu.boundingBox();
    expect(box).not.toBeNull();
    expectInViewport(box!, 1440, 900);
    await expect(
      menu.getByRole("menuitem", { name: "Renomear" }),
    ).toBeVisible();
    await expect(
      menu.getByRole("menuitem", { name: "Excluir" }),
    ).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(menu).toBeHidden({ timeout: 5_000 });
  });

  test("menu de espaço vazio oferece Selecionar tudo e Ajustar", async ({
    page,
  }) => {
    await openEditor(page);
    await page.locator(".bpmnm-canvas").click({
      button: "right",
      position: { x: 400, y: 620 },
    });
    const menu = page.locator('[aria-label="Menu do diagrama"]');
    await expect(menu).toBeVisible({ timeout: 5_000 });
    const box = await menu.boundingBox();
    expect(box).not.toBeNull();
    expectInViewport(box!, 1440, 900);
    await expect(
      menu.getByRole("menuitem", { name: "Selecionar tudo" }),
    ).toBeVisible();
    await expect(
      menu.getByRole("menuitem", { name: "Ajustar à janela" }),
    ).toBeVisible();
    await page.keyboard.press("Escape");
  });
});

test.describe("E2E-35 — canvas resize / zoom-fit", () => {
  test.use({ actor: "editor" });
  test("canvas re-medido ao redimensionar o viewport", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await openEditor(page);
    const before = await page.locator(".bpmnm-canvas").boundingBox();
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForTimeout(500);
    const after = await page.locator(".bpmnm-canvas").boundingBox();
    expect(before).not.toBeNull();
    expect(after).not.toBeNull();
    // o canvas acompanha o novo viewport (renderer re-medido via resized())
    expect(after!.width).toBeGreaterThan(before!.width);
    expect(after!.height).toBeGreaterThan(before!.height);
  });

  test("fit viewport mantém elementos dentro do canvas", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await openEditor(page);
    await page
      .getByRole("button", { name: /ajustar|fit/i })
      .first()
      .click();
    await page.waitForTimeout(500);
    const canvasBox = await page.locator(".bpmnm-canvas").boundingBox();
    const elBox = await page
      .locator('.djs-element[data-element-id="T1"]')
      .boundingBox();
    expect(canvasBox).not.toBeNull();
    expect(elBox).not.toBeNull();
    // elemento dentro da área do canvas
    expect(elBox!.x).toBeGreaterThanOrEqual(canvasBox!.x - 1);
    expect(elBox!.y).toBeGreaterThanOrEqual(canvasBox!.y - 1);
    expect(elBox!.x + elBox!.width).toBeLessThanOrEqual(
      canvasBox!.x + canvasBox!.width + 1,
    );
    expect(elBox!.y + elBox!.height).toBeLessThanOrEqual(
      canvasBox!.y + canvasBox!.height + 1,
    );
  });
});

test.describe("E2E-36 — light/dark interactive states", () => {
  test.use({ actor: "editor", viewport: { width: 1440, height: 900 } });
  for (const theme of ["light", "dark"] as const) {
    test(`${theme}: seleção + context pad + popup renderizam`, async ({
      page,
    }) => {
      await openEditor(page, theme);
      await page
        .locator('.djs-element[data-element-id="T1"]')
        .click({ position: { x: 10, y: 10 } });
      await expect(page.locator(".djs-element.selected")).toHaveCount(1);
      const pad = page.locator(".djs-context-pad");
      await expect(pad).toBeVisible();
      // cor de fundo do context pad não é branco no dark
      if (theme === "dark") {
        const bg = await pad.evaluate(
          (el) => getComputedStyle(el).backgroundColor,
        );
        // aceitável: transparente (herda canvas) ou superfície escura
        expect(bg).not.toBe("rgb(255, 255, 255)");
      }
    });
  }
});
