import { test, expect, importModelViaApi, modelUrl } from "../helpers";
import type { Page } from "@playwright/test";

/**
 * E2E-40 — bpmn-js interaction chrome (drag/drop/context pad/popup/direct
 * edit/resize) integrado ao tema light/dark do produto.
 *
 * O vendor resolve todo o chrome por tokens `--bio-*`/`--shape-*` definidos
 * em `.bio-theme-parent`/`.djs-parent`; o MFE remapeia esses extension
 * points para os tokens `--delpi-ui-*` do portal. As asserções são de
 * computed style (luminância/alpha), não de screenshots.
 */

const XML_CHROME =
  '<?xml version="1.0" encoding="UTF-8"?>' +
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ' +
  'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" ' +
  'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" ' +
  'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" ' +
  'id="defs_ch" targetNamespace="urn:ch">' +
  '<bpmn:collaboration id="C1"><bpmn:participant id="PA1" name="Pool" processRef="P1"/></bpmn:collaboration>' +
  '<bpmn:process id="P1" isExecutable="false">' +
  '<bpmn:laneSet id="LS1"><bpmn:lane id="L1" name="Lane"><bpmn:flowNodeRef>T1</bpmn:flowNodeRef></bpmn:lane></bpmn:laneSet>' +
  '<bpmn:startEvent id="S1"/><bpmn:task id="T1" name="Tarefa"/>' +
  '<bpmn:subProcess id="SP1"><bpmn:startEvent id="S2"/><bpmn:endEvent id="E2"/></bpmn:subProcess>' +
  '<bpmn:endEvent id="E1"/>' +
  '<bpmn:sequenceFlow id="F1" sourceRef="S1" targetRef="T1"/>' +
  '<bpmn:sequenceFlow id="F2" sourceRef="T1" targetRef="SP1"/>' +
  '<bpmn:sequenceFlow id="F3" sourceRef="SP1" targetRef="E1"/>' +
  '</bpmn:process>' +
  '<bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL1" bpmnElement="C1">' +
  '<bpmndi:BPMNShape id="PA1_di" bpmnElement="PA1" isHorizontal="true"><dc:Bounds x="100" y="80" width="900" height="420"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="L1_di" bpmnElement="L1" isHorizontal="true"><dc:Bounds x="130" y="80" width="870" height="420"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="S1_di" bpmnElement="S1"><dc:Bounds x="160" y="140" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="T1_di" bpmnElement="T1"><dc:Bounds x="260" y="120" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="SP1_di" bpmnElement="SP1" isExpanded="true"><dc:Bounds x="460" y="110" width="300" height="110"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="S2_di" bpmnElement="S2"><dc:Bounds x="475" y="145" width="30" height="30"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="E2_di" bpmnElement="E2"><dc:Bounds x="710" y="145" width="30" height="30"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="E1_di" bpmnElement="E1"><dc:Bounds x="840" y="135" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNEdge id="F1_di" bpmnElement="F1"><di:waypoint x="196" y="158"/><di:waypoint x="260" y="158"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="F2_di" bpmnElement="F2"><di:waypoint x="360" y="160"/><di:waypoint x="460" y="165"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="F3_di" bpmnElement="F3"><di:waypoint x="760" y="165"/><di:waypoint x="840" y="153"/></bpmndi:BPMNEdge>' +
  '</bpmndi:BPMNPlane></bpmndi:BPMNDiagram></bpmn:definitions>';

/** Luminância relativa de "rgb(a)(r, g, b, a)" ou "color(srgb r g b / a)". */
function luminance(css: string): number {
  const nums = css.match(/[\d.]+/g)?.map(Number) ?? [1, 1, 1];
  const norm = css.startsWith("color") ? nums : nums.map((n) => n / 255);
  return 0.2126 * norm[0] + 0.7152 * norm[1] + 0.0722 * norm[2];
}

/** Alpha < 1 → feedback translúcido (wash), não superfície sólida. */
function isTranslucent(css: string): boolean {
  const nums = css.match(/[\d.]+/g)?.map(Number) ?? [];
  return /rgba\(|color\(/.test(css) && nums[nums.length - 1] < 1;
}

async function openEditor(page: Page, theme: "light" | "dark") {
  await page.evaluate((t) => {
    localStorage.setItem("theme", t);
    document.documentElement.setAttribute("data-theme", t);
  }, theme);
  const modelId = await importModelViaApi("editor", "E2E-Chrome", XML_CHROME);
  await page.goto(modelUrl(modelId));
  await expect(
    page.locator('.djs-element[data-element-id="T1"]'),
  ).toBeVisible({ timeout: 20_000 });
  await page.waitForTimeout(800);
}

interface DragState {
  svgClass: string;
  svgBg: string;
  newParentFill: string | null;
  draggerStroke: string | null;
}

async function dragState(page: Page): Promise<DragState> {
  return page.evaluate(() => {
    const svg = document.querySelector(".djs-container svg");
    const np = document.querySelector(".djs-shape.new-parent");
    const visual = np?.querySelector(".djs-visual > :nth-child(1)");
    const dragger = document.querySelector(".djs-dragger");
    return {
      svgClass: svg?.getAttribute("class") ?? "",
      svgBg: svg ? getComputedStyle(svg).backgroundColor : "",
      newParentFill: visual ? getComputedStyle(visual).fill : null,
      draggerStroke: dragger
        ? getComputedStyle(
            dragger.querySelector("path,rect,circle,polygon") ?? dragger,
          ).stroke
        : null,
    };
  });
}

/** Mousedown num entry da palette e arrasta até (x, y) sem soltar. */
async function dragPalette(page: Page, action: string, x: number, y: number) {
  const entry = page.locator(`.djs-palette .entry[data-action*="${action}"]`).first();
  const box = await entry.boundingBox();
  if (!box) throw new Error("palette entry not found");
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  await page.mouse.move(x, y, { steps: 10 });
  await page.waitForTimeout(400);
}

async function elBox(page: Page, id: string) {
  const box = await page
    .locator(`.djs-element[data-element-id="${id}"]`)
    .boundingBox();
  if (!box) throw new Error(`element ${id} not found`);
  return box;
}

test.describe("E2E-40 — interaction chrome", () => {
  test.use({ actor: "editor", viewport: { width: 1440, height: 900 } });

  for (const theme of ["dark", "light"] as const) {
    test(`${theme}: drag/drop feedback translúcido + cleanup`, async ({
      page,
    }) => {
      await openEditor(page, theme);
      const cv = (await page.locator(".bpmnm-canvas").boundingBox())!;
      const pa = await elBox(page, "PA1");
      const sp = await elBox(page, "SP1");

      // root canvas fora de containers → drop-not-ok: wash translúcido,
      // nunca superfície clara sólida
      await dragPalette(page, "create.task", cv.x + 500, cv.y + 50);
      let st = await dragState(page);
      expect(st.svgClass).toContain("drop-not-ok");
      expect(isTranslucent(st.svgBg)).toBe(true);

      // sobre o pool → new-parent: fill translúcido (accent wash)
      await page.mouse.move(pa.x + 400, pa.y + pa.height - 60, { steps: 8 });
      await page.waitForTimeout(300);
      st = await dragState(page);
      expect(st.newParentFill).not.toBeNull();
      expect(isTranslucent(st.newParentFill!)).toBe(true);

      // sobre subprocess → idem
      await page.mouse.move(sp.x + sp.width - 60, sp.y + 30, { steps: 8 });
      await page.waitForTimeout(300);
      st = await dragState(page);
      expect(st.newParentFill).not.toBeNull();
      expect(isTranslucent(st.newParentFill!)).toBe(true);

      // drop válido na lane → cleanup total de markers/dragger
      await page.mouse.up();
      await page.waitForTimeout(500);
      st = await dragState(page);
      expect(st.svgClass).not.toMatch(/drop-|connect-|new-parent/);
      expect(st.draggerStroke).toBeNull();

      // cancel por Escape → idem
      await dragPalette(page, "create.task", cv.x + cv.width / 2, cv.y + cv.height / 2);
      await page.keyboard.press("Escape");
      await page.waitForTimeout(400);
      st = await dragState(page);
      expect(st.svgClass).not.toMatch(/drop-|connect-|new-parent/);
      expect(
        await page.locator(".djs-dragger, .djs-dragging").count(),
      ).toBe(0);
    });
  }

  test("dark: context pad, popup, direct edit e resizers temáticos", async ({
    page,
  }) => {
    await openEditor(page, "dark");

    // context pad: entries com respiro e superfície dark (não branco vendor)
    await page
      .locator('.djs-element[data-element-id="T1"]')
      .click({ position: { x: 8, y: 8 }, force: true });
    await expect(page.locator(".djs-context-pad.open")).toBeVisible();
    const pad = await page.evaluate(() => {
      const entries = [
        ...document.querySelectorAll(".djs-context-pad .entry"),
      ].map((e) => e.getBoundingClientRect());
      const cs = getComputedStyle(
        document.querySelector(".djs-context-pad .entry")!,
      );
      const gap =
        entries.length > 1 ? entries[1].x - (entries[0].x + entries[0].width) : 0;
      return { bg: cs.backgroundColor, gap, count: entries.length };
    });
    expect(pad.count).toBeGreaterThan(3);
    expect(pad.gap).toBeGreaterThanOrEqual(2);
    expect(luminance(pad.bg)).toBeLessThan(0.4);

    // replace popup: superfície dark, texto claro, dentro do viewport
    await page
      .locator('.djs-context-pad .entry[data-action="replace"]')
      .click();
    const popup = page.locator(".djs-popup");
    await expect(popup).toBeVisible();
    const pop = await page.evaluate(() => {
      const p = document.querySelector(".djs-popup")!;
      const r = p.getBoundingClientRect();
      const cs = getComputedStyle(p);
      return {
        bg: cs.backgroundColor,
        color: cs.color,
        inViewport:
          r.x >= 0 && r.y >= 0 && r.right <= innerWidth && r.bottom <= innerHeight,
        zIndex: Number(cs.zIndex),
      };
    });
    expect(luminance(pop.bg)).toBeLessThan(0.4);
    expect(luminance(pop.color)).toBeGreaterThan(luminance(pop.bg));
    expect(pop.inViewport).toBe(true);
    expect(pop.zIndex).toBeGreaterThanOrEqual(100);
    await page.keyboard.press("Escape");
    await expect(popup).toHaveCount(0, { timeout: 5000 });

    // direct edit: superfície escura legível, fecha com Esc
    const t1 = await elBox(page, "T1");
    await page.mouse.dblclick(t1.x + t1.width / 2, t1.y + t1.height / 2);
    const editing = page.locator(".djs-direct-editing-parent");
    await expect(editing).toBeVisible();
    const de = await editing.evaluate((el) => ({
      bg: getComputedStyle(el).backgroundColor,
      color: getComputedStyle(el).color,
    }));
    expect(luminance(de.bg)).toBeLessThan(0.4);
    await page.keyboard.press("Escape");
    await expect(editing).toHaveCount(0, { timeout: 5000 });

    // resizers: handles accent visíveis no subprocess selecionado
    await page
      .locator('.djs-element[data-element-id="SP1"]')
      .click({ position: { x: 20, y: 20 }, force: true });
    await page.waitForTimeout(400);
    const res = await page.evaluate(() => {
      const rs = [...document.querySelectorAll(".djs-resizer")];
      const fill = rs[0]
        ? getComputedStyle(rs[0].querySelector("rect") ?? rs[0]).fill
        : null;
      return { count: rs.length, fill };
    });
    expect(res.count).toBeGreaterThanOrEqual(4);
    expect(res.fill).toBeTruthy();
    expect(luminance(res.fill!)).toBeGreaterThan(0.15);
  });

  test("palette: ícones por font glyph, nomes acessíveis, sem raster", async ({
    page,
  }) => {
    await openEditor(page, "dark");
    const pal = await page.evaluate(() => {
      const entries = [...document.querySelectorAll(".djs-palette .entry")];
      return {
        count: entries.length,
        rasters: document.querySelectorAll(".djs-palette .entry img, .djs-palette .entry svg").length,
        missingLabel: entries.filter((e) => !e.getAttribute("aria-label")).length,
        color: getComputedStyle(entries[0]).color,
      };
    });
    expect(pal.count).toBeGreaterThan(8);
    expect(pal.rasters).toBe(0);
    expect(pal.missingLabel).toBe(0);
    // glyph segue o texto do tema (dark → claro)
    expect(luminance(pal.color)).toBeGreaterThan(0.5);
  });
});
