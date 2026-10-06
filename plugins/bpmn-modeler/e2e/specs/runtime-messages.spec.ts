import { test, expect, importModelViaApi, modelUrl } from "../helpers";
import type { Page } from "@playwright/test";
import path from "node:path";
import fs from "node:fs";

/**
 * E2E-44 — runtime/modeling messages PT-BR.
 *
 * Regras BPMN rejeitadas em runtime (shape.move.rejected / create.rejected)
 * exibem tooltips de erro do vendor via ModelingFeedback. As strings passam
 * pelo serviço `translate` (ptBrTranslateModule) — aqui o tooltip real é
 * disparado por drag/drop no browser, não apenas o dicionário.
 *
 * O branding BPMN.io NÃO pode ser removido: a licença do pacote bpmn-js
 * exige o watermark visível — o teste de branding apenas garante que ele
 * permanece renderizado (atribuição preservada).
 */

const XML_COLLAB =
  '<?xml version="1.0" encoding="UTF-8"?>' +
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ' +
  'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" ' +
  'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" ' +
  'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" ' +
  'id="defs_rm" targetNamespace="urn:rm">' +
  '<bpmn:collaboration id="C1"><bpmn:participant id="PA1" name="Pool" processRef="P1"/></bpmn:collaboration>' +
  '<bpmn:process id="P1" isExecutable="false">' +
  '<bpmn:startEvent id="S1"/><bpmn:task id="T1" name="Tarefa"/><bpmn:endEvent id="E1"/>' +
  '<bpmn:sequenceFlow id="F1" sourceRef="S1" targetRef="T1"/>' +
  '<bpmn:sequenceFlow id="F2" sourceRef="T1" targetRef="E1"/>' +
  '</bpmn:process>' +
  '<bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL1" bpmnElement="C1">' +
  '<bpmndi:BPMNShape id="PA1_di" bpmnElement="PA1" isHorizontal="true"><dc:Bounds x="100" y="80" width="600" height="300"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="S1_di" bpmnElement="S1"><dc:Bounds x="160" y="150" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="T1_di" bpmnElement="T1"><dc:Bounds x="280" y="130" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="E1_di" bpmnElement="E1"><dc:Bounds x="480" y="152" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNEdge id="F1_di" bpmnElement="F1"><di:waypoint x="196" y="168"/><di:waypoint x="280" y="168"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="F2_di" bpmnElement="F2"><di:waypoint x="380" y="168"/><di:waypoint x="480" y="170"/></bpmndi:BPMNEdge>' +
  '</bpmndi:BPMNPlane></bpmndi:BPMNDiagram></bpmn:definitions>';

const SHOTS = path.resolve(import.meta.dirname, "../../.tmp-shots");

async function openEditor(page: Page, theme: "light" | "dark") {
  await page.evaluate((t) => {
    localStorage.setItem("theme", t);
    document.documentElement.setAttribute("data-theme", t);
  }, theme);
  const modelId = await importModelViaApi("editor", "E2E-RuntimeMsg", XML_COLLAB);
  await page.goto(modelUrl(modelId));
  await expect(
    page.locator('.djs-element[data-element-id="T1"]'),
  ).toBeVisible({ timeout: 20_000 });
  await page.waitForTimeout(600);
}

async function shot(page: Page, name: string) {
  fs.mkdirSync(SHOTS, { recursive: true });
  await page.screenshot({ path: path.join(SHOTS, `${name}.png`) });
}

/** Ponto do root canvas (Collaboration) fora do pool — drop inválido. */
async function outsidePool(page: Page) {
  const pool = page.locator('.djs-element[data-element-id="PA1"]');
  const box = await pool.boundingBox();
  if (!box) throw new Error("pool not found");
  const canvas = page.locator(".bpmnm-canvas");
  const cb = await canvas.boundingBox();
  if (!cb) throw new Error("canvas not found");
  return {
    x: box.x + box.width / 2,
    y: Math.min(box.y + box.height + 60, cb.y + cb.height - 30),
  };
}

/** Drag real engajando o move/create do diagram-js (pequeno deslocamento + pausa). */
async function drag(page: Page, fromX: number, fromY: number, toX: number, toY: number) {
  await page.mouse.move(fromX, fromY);
  await page.mouse.down();
  await page.mouse.move(fromX + 15, fromY, { steps: 4 });
  await page.waitForTimeout(200);
  await page.mouse.move(toX, toY, { steps: 12 });
  await page.waitForTimeout(200);
  await page.mouse.up();
}

test.describe("runtime messages PT-BR", () => {
  test("RTM-01: drop de flow node fora do pool mostra erro em PT-BR (dark)", async ({
    page,
  }) => {
    await openEditor(page, "dark");
    const t1 = await page
      .locator('.djs-element[data-element-id="T1"]')
      .boundingBox();
    if (!t1) throw new Error("T1 not found");
    const target = await outsidePool(page);
    await drag(page, t1.x + t1.width / 2, t1.y + t1.height / 2, target.x, target.y);

    const tooltip = page.locator(".djs-tooltip.djs-tooltip-error").first();
    await expect(tooltip).toContainText(
      "Elementos de fluxo devem pertencer a um pool/participante",
      { timeout: 3000 },
    );
    await expect(tooltip).not.toContainText("flow elements must be children");
    await shot(page, "invalid-parent-dark-after");
  });

  test("RTM-02: drop de flow node fora do pool em PT-BR (light)", async ({
    page,
  }) => {
    await openEditor(page, "light");
    const t1 = await page
      .locator('.djs-element[data-element-id="T1"]')
      .boundingBox();
    if (!t1) throw new Error("T1 not found");
    const target = await outsidePool(page);
    await drag(page, t1.x + t1.width / 2, t1.y + t1.height / 2, target.x, target.y);

    const tooltip = page.locator(".djs-tooltip.djs-tooltip-error").first();
    await expect(tooltip).toContainText(
      "Elementos de fluxo devem pertencer a um pool/participante",
      { timeout: 3000 },
    );
    await shot(page, "invalid-parent-light-after");
  });

  test("RTM-03: create.rejected de data object fora do pool em PT-BR", async ({
    page,
  }) => {
    await openEditor(page, "dark");
    const entry = page
      .locator('.djs-palette .entry[data-action="create.data-object"]')
      .first();
    const eb = await entry.boundingBox();
    if (!eb) throw new Error("palette data-object not found");
    const target = await outsidePool(page);
    await drag(page, eb.x + eb.width / 2, eb.y + eb.height / 2, target.x, target.y);

    const tooltip = page.locator(".djs-tooltip.djs-tooltip-error").first();
    await expect(tooltip).toContainText(
      "Objeto de dados deve ser posicionado dentro de um pool/participante",
      { timeout: 3000 },
    );
    await expect(tooltip).not.toContainText("Data object must be placed");
    await shot(page, "invalid-data-object-dark-after");
  });

  test("RTM-04: conexão inválida (para start event) — not-ok, sem tooltip EN", async ({
    page,
  }) => {
    await openEditor(page, "dark");
    // context pad da T1 → "Connect to other element"
    await page.locator('.djs-element[data-element-id="T1"]').click();
    const connect = page
      .locator('.djs-context-pad .entry[data-action*="connect"]')
      .first();
    const cb = await connect.boundingBox();
    if (!cb) throw new Error("context pad connect not found");
    const s1 = await page
      .locator('.djs-element[data-element-id="S1"]')
      .boundingBox();
    if (!s1) throw new Error("S1 not found");

    // connect do context pad: click ativa o modo connect (vendor aceita click+dragstart)
    await connect.click();
    await page.mouse.move(s1.x + s1.width / 2 - 30, s1.y + s1.height / 2, {
      steps: 8,
    });
    await page.mouse.move(s1.x + s1.width / 2, s1.y + s1.height / 2, {
      steps: 8,
    });
    await page.waitForTimeout(400);

    // preview de conexão ativo durante o hover
    await expect(page.locator(".djs-dragger")).toHaveCount(1);
    await shot(page, "invalid-connection-after");

    // soltar sobre o start event: regra BPMN rejeita — nenhuma edge nova
    const edgesBefore = await page.locator(".djs-connection").count();
    await page.mouse.up();
    await page.waitForTimeout(300);
    expect(await page.locator(".djs-connection").count()).toBe(edgesBefore);

    // nenhum tooltip em inglês durante a tentativa de conexão inválida
    await expect(
      page.locator(
        '.djs-tooltip:has-text("must be"), .djs-tooltip:has-text("not allowed")',
      ),
    ).toHaveCount(0);
  });

  for (const theme of ["dark", "light"] as const) {
    test(`RTM-05: branding BPMN.io permanece visível — licença exige atribuição (${theme})`, async ({
      page,
    }) => {
      await openEditor(page, theme);
      const branding = page.locator(".bjs-powered-by");
      await expect(branding).toHaveCount(1);
      await expect(branding).toBeVisible();

      // R4: watermark não pode sobrepor/collidir com chrome do editor
      const geo = await page.evaluate(() => {
        const rect = (sel: string) =>
          document.querySelector(sel)?.getBoundingClientRect();
        const logo = rect(".bjs-powered-by")!;
        const canvas = rect(".bpmnm-canvas")!;
        const ctl = rect(".bpmnm-viewport-controls");
        const side = rect(".bpmnm-side");
        const overlap = (a: DOMRect, b: DOMRect) =>
          a.left < b.right &&
          a.right > b.left &&
          a.top < b.bottom &&
          a.bottom > b.top;
        return {
          insideCanvas:
            logo.left >= canvas.left &&
            logo.right <= canvas.right &&
            logo.top >= canvas.top &&
            logo.bottom <= canvas.bottom,
          overlapsControls: ctl ? overlap(logo, ctl) : false,
          overlapsSidebar: side ? overlap(logo, side) : false,
          width: logo.width,
          height: logo.height,
        };
      });
      expect(geo.insideCanvas).toBe(true);
      expect(geo.overlapsControls).toBe(false);
      expect(geo.overlapsSidebar).toBe(false);
      expect(geo.width).toBeGreaterThan(0);

      await shot(page, `canvas-${theme}-branding-attribution`);
      if (theme === "dark") {
        await shot(page, "viewport-controls-after-branding");
      }
    });
  }
});
