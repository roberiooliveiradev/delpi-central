import { test, expect, importModelViaApi, modelUrl } from "../helpers";
import type { Page } from "@playwright/test";

/**
 * E2E-43 — sidebar collapsible rail + topbar icons/help.
 *
 * Recolher a sidebar deve liberar espaço real para o canvas
 * (canvas.resized() preserva zoom/pan/seleção), a rail expõe atalhos
 * que expandem já na aba correta, e a aba ativa sobrevive ao ciclo
 * collapse→expand. Estado é UI-only — nunca vai para BPMN/backend.
 */

const XML =
  '<?xml version="1.0" encoding="UTF-8"?>' +
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ' +
  'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" ' +
  'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" ' +
  'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" ' +
  'id="defs_col" targetNamespace="urn:col">' +
  '<bpmn:process id="P1" isExecutable="false">' +
  '<bpmn:startEvent id="S1"/><bpmn:task id="T1" name="Tarefa"/>' +
  '<bpmn:endEvent id="E1"/>' +
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

async function openEditor(page: Page) {
  const modelId = await importModelViaApi("editor", "E2E-Collapse", XML);
  await page.goto(modelUrl(modelId));
  await expect(
    page.locator('.djs-element[data-element-id="T1"]'),
  ).toBeVisible({ timeout: 20_000 });
  await page.waitForTimeout(1000);
}

const side = (page: Page) => page.locator(".bpmnm-side");
const canvas = (page: Page) => page.locator(".bpmnm-canvas-wrap");

test.describe("E2E-43 — sidebar collapse", () => {
  test("top bar: ícones + helps nos controles textuais", async ({ page }) => {
    await openEditor(page);

    for (const label of ["Organizar", "Validar", "Salvar"]) {
      const btn = page.locator(`.bpmnm-editor__header button:has-text("${label}")`);
      await expect(btn).toBeVisible();
      // ícone lucide dentro do ActionButton
      await expect(btn.locator("svg")).toHaveCount(1);
      const title = await btn.getAttribute("title");
      expect(title).toBeTruthy();
      expect(title).toMatch(/[a-záàâãéêíóôõúç]/i);
    }
    await expect(
      page.locator('.bpmnm-editor__header button:has-text("Biblioteca") svg'),
    ).toHaveCount(1);
  });

  test("sidebar tabs têm ícone + tooltip PT-BR", async ({ page }) => {
    await openEditor(page);
    for (const tab of ["Propriedades", "Validação", "Histórico"]) {
      const t = page.getByRole("tab", { name: tab });
      await expect(t.locator("svg")).toHaveCount(1);
      expect(await t.getAttribute("title")).toBeTruthy();
    }
  });

  test("collapse → rail ~48px e canvas ganha largura", async ({ page }) => {
    await openEditor(page);
    const cwBefore = (await canvas(page).boundingBox())!.width;
    const swBefore = (await side(page).boundingBox())!.width;

    await page.locator('button[aria-label="Recolher painel lateral"]').click();
    await page.waitForTimeout(400);

    const cwAfter = (await canvas(page).boundingBox())!.width;
    const swAfter = (await side(page).boundingBox())!.width;
    expect(swAfter).toBeLessThan(60);
    expect(swAfter).toBeLessThan(swBefore);
    expect(cwAfter).toBeGreaterThan(cwBefore);
    expect(cwAfter - cwBefore).toBeGreaterThan(swBefore - swAfter - 20);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
      await page.evaluate(() => innerWidth),
    );

    // rail: 1 expander + 3 atalhos
    const rail = page.locator(".bpmnm-side__rail");
    await expect(rail).toBeVisible();
    expect(await rail.locator("button").count()).toBe(4);
  });

  test("rail expande direto na aba clicada", async ({ page }) => {
    await openEditor(page);
    await page.locator('button[aria-label="Recolher painel lateral"]').click();
    await page.waitForTimeout(300);

    await page.locator('.bpmnm-side__rail button[aria-label="Histórico"]').click();
    await page.waitForTimeout(400);

    expect(await page.locator('button[aria-label="Expandir painel lateral"]').count()).toBe(0);
    await expect(
      page.getByRole("tab", { name: "Histórico" }),
    ).toHaveAttribute("aria-selected", "true");
    await expect(page.locator(".bpmnm-revisions")).toBeVisible();
  });

  test("aba ativa sobrevive a collapse→expand", async ({ page }) => {
    await openEditor(page);
    await page.getByRole("tab", { name: "Validação" }).click();
    await expect(
      page.getByRole("tab", { name: "Validação" }),
    ).toHaveAttribute("aria-selected", "true");

    await page.locator('button[aria-label="Recolher painel lateral"]').click();
    await page.waitForTimeout(300);
    await page.locator('button[aria-label="Expandir painel lateral"]').click();
    await page.waitForTimeout(300);

    await expect(
      page.getByRole("tab", { name: "Validação" }),
    ).toHaveAttribute("aria-selected", "true");
  });

  test("view state (viewbox + seleção) preservado", async ({ page }) => {
    await openEditor(page);
    const viewbox = () =>
      page.locator(".bpmnm-canvas .djs-container .viewport").first().getAttribute("transform");

    await page.locator('.djs-element[data-element-id="T1"]').click();
    await page.waitForTimeout(400);
    const before = await viewbox();

    await page.locator('button[aria-label="Recolher painel lateral"]').click();
    await page.waitForTimeout(400);
    await page.locator('button[aria-label="Expandir painel lateral"]').click();
    await page.waitForTimeout(400);

    expect(await viewbox()).toBe(before);
    await expect(
      page.locator('.djs-element.selected[data-element-id="T1"]'),
    ).toHaveCount(1);
  });
});
