import { test, expect, importModelViaApi, modelUrl } from "../helpers";
import type { Page } from "@playwright/test";

/**
 * E2E-42 — Global editor PT-BR: chrome fora da sidebar.
 *
 * Cobre as superfícies user-facing do editor que não são o properties
 * panel: palette, context pad, replace popup (incl. busca), context
 * menu do canvas, top bar, viewport controls, ⋮ menu e estados.
 * `Powered by bpmn.io` é atribuição de licença do vendor — excluído.
 */

const XML_G =
  '<?xml version="1.0" encoding="UTF-8"?>' +
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ' +
  'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" ' +
  'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" ' +
  'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" ' +
  'id="defs_g" targetNamespace="urn:g">' +
  '<bpmn:collaboration id="C1"><bpmn:participant id="PA1" name="Pool" processRef="P1"/></bpmn:collaboration>' +
  '<bpmn:process id="P1" isExecutable="false">' +
  '<bpmn:startEvent id="S1"/><bpmn:task id="T1" name="Tarefa"/>' +
  '<bpmn:endEvent id="E1"/>' +
  '<bpmn:sequenceFlow id="F1" sourceRef="S1" targetRef="T1"/>' +
  '<bpmn:sequenceFlow id="F2" sourceRef="T1" targetRef="E1"/>' +
  '</bpmn:process>' +
  '<bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL1" bpmnElement="C1">' +
  '<bpmndi:BPMNShape id="PA1_di" bpmnElement="PA1" isHorizontal="true"><dc:Bounds x="100" y="80" width="900" height="400"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="S1_di" bpmnElement="S1"><dc:Bounds x="160" y="160" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="T1_di" bpmnElement="T1"><dc:Bounds x="280" y="140" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="E1_di" bpmnElement="E1"><dc:Bounds x="460" y="162" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNEdge id="F1_di" bpmnElement="F1"><di:waypoint x="196" y="178"/><di:waypoint x="280" y="178"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="F2_di" bpmnElement="F2"><di:waypoint x="380" y="180"/><di:waypoint x="460" y="180"/></bpmndi:BPMNEdge>' +
  '</bpmndi:BPMNPlane></bpmndi:BPMNDiagram></bpmn:definitions>';

/** Strings EN do vendor proibidas em qualquer superfície do editor.
 *  `Powered by bpmn.io` (atribuição exigida pela licença OSS) é o único
 *  caso justificado e é avaliado separadamente. */
const FORBIDDEN_EN = [
  "Activate",
  "Create ",
  "Append",
  "Add lane",
  "Divide into",
  "Connect ",
  "Change element",
  "results found",
  "result found",
  "Open entry documentation",
  "User task",
  "Service task",
  "Sub-process",
  "Select an element",
  "Loading",
  "Saving",
  "Undo",
  "Redo",
];

async function collectStrings(page: Page, selector: string): Promise<string[]> {
  return page.evaluate((sel) => {
    const out: string[] = [];
    document.querySelectorAll(sel).forEach((el) => {
      for (const attr of ["aria-label", "title", "placeholder"]) {
        const v = el.getAttribute(attr);
        if (v) out.push(v);
      }
      const t = el.textContent?.trim();
      if (t) out.push(t);
    });
    return out;
  }, selector);
}

function assertPtBr(strings: string[], surface: string) {
  const bad: string[] = [];
  for (const s of strings) {
    if (!s || s === "Powered by bpmn.io") continue;
    for (const en of FORBIDDEN_EN) {
      if (new RegExp(`\\b${en}`, "i").test(s) && !/^[a-z]+:/.test(s)) {
        bad.push(`${en} → "${s.slice(0, 80)}"`);
        break;
      }
    }
  }
  expect(bad, `residual EN em ${surface}: ${bad.join(" | ")}`).toEqual([]);
}

async function openEditor(page: Page) {
  const modelId = await importModelViaApi("editor", "E2E-i18n-Global", XML_G);
  await page.goto(modelUrl(modelId));
  await expect(
    page.locator('.djs-element[data-element-id="T1"]'),
  ).toBeVisible({ timeout: 20_000 });
  await page.waitForTimeout(1000);
}

test.describe("E2E-42 — editor global PT-BR", () => {
  test.use({ actor: "editor", viewport: { width: 1440, height: 900 } });

  test("palette: accessible names e tooltips em PT-BR", async ({ page }) => {
    await openEditor(page);
    const strings = await collectStrings(page, ".djs-palette .entry");
    expect(strings.length).toBeGreaterThan(10);
    assertPtBr(strings, "palette");
    await expect(
      page.locator('.djs-palette .entry[aria-label="Criar tarefa"]'),
    ).toBeVisible();
  });

  test("context pad e replace popup em PT-BR", async ({ page }) => {
    await openEditor(page);
    await page.locator('.djs-element[data-element-id="T1"]').click({
      position: { x: 50, y: 40 },
      force: true,
    });
    await expect(page.locator(".djs-context-pad.open")).toBeVisible({
      timeout: 8_000,
    });
    assertPtBr(
      await collectStrings(page, ".djs-context-pad .entry"),
      "context-pad",
    );

    const replace = page
      .locator('.djs-context-pad .entry[title="Trocar elemento"]')
      .first();
    await replace.click();
    await expect(page.locator(".djs-popup")).toBeVisible({ timeout: 8_000 });
    assertPtBr(await collectStrings(page, ".djs-popup"), "replace-popup");
    await expect(
      page.locator(".djs-popup").getByText("Tarefa de usuário"),
    ).toBeVisible();

    // busca no popup: contador vendor oculto, lista filtrada PT-BR
    const search = page.locator(".djs-popup-search input");
    if (await search.count()) {
      await search.fill("usu");
      await page.waitForTimeout(300);
      await expect(page.locator(".djs-popup-search-count")).toBeHidden();
      assertPtBr(await collectStrings(page, ".djs-popup"), "popup-search");
    }
  });

  test("canvas context menu, ⋮ menu, top bar e viewport em PT-BR", async ({
    page,
  }) => {
    await openEditor(page);

    // menu de contexto do canvas (elemento)
    await page.locator('.djs-element[data-element-id="T1"]').click({
      button: "right",
      position: { x: 50, y: 40 },
      force: true,
    });
    const menu = page.locator('[aria-label="Menu do diagrama"]');
    await expect(menu).toBeVisible({ timeout: 8_000 });
    assertPtBr(await collectStrings(page, '[aria-label="Menu do diagrama"]'), "canvas-menu");
    await page.keyboard.press("Escape");

    // ⋮ overflow
    await page.locator('button[aria-label="Mais ações"]').click();
    const more = page.locator('[aria-label="Mais ações do editor"]');
    await expect(more).toBeVisible({ timeout: 5_000 });
    assertPtBr(await collectStrings(page, '[aria-label="Mais ações do editor"]'), "more-menu");
    await page.keyboard.press("Escape");

    // top bar + viewport controls (texto, tooltips, aria-labels)
    assertPtBr(
      await collectStrings(
        page,
        ".dashboard-bpmn-modeler button[title], .dashboard-bpmn-modeler button[aria-label]",
      ),
      "topbar+viewport",
    );
  });
});
