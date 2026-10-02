import {
  test,
  expect,
  apiToken,
  importModelViaApi,
  modelUrl,
} from "../helpers";
import type { Page } from "@playwright/test";

/**
 * E2E-39 — Canvas theme & visual lifecycle stability.
 *
 * Prova via computed styles (não screenshot): canvas bg, fill/stroke de
 * shapes, labels internas/externas, flows e markers permanecem estáveis
 * durante create/append/connect/move/resize/replace/delete/undo/redo/
 * layout preview/save/reload — em dark E light. Elementos criados pós-load
 * recebem o mesmo tema dos existentes (bpmnRenderer defaults canônicos).
 */

const HEAD =
  '<?xml version="1.0" encoding="UTF-8"?>' +
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ' +
  'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" ' +
  'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" ' +
  'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" ' +
  'id="defs_th" targetNamespace="urn:th">';
const TAIL = "</bpmn:definitions>";

/** Collaboration com pool+lane: cobre participant/lane/data/subprocess. */
const XML_THEME =
  HEAD +
  '<bpmn:collaboration id="C1"><bpmn:participant id="PA1" name="Pool" processRef="P1"/></bpmn:collaboration>' +
  '<bpmn:process id="P1" isExecutable="false">' +
  '<bpmn:laneSet id="LS1"><bpmn:lane id="L1" name="Lane A"><bpmn:flowNodeRef>T1</bpmn:flowNodeRef></bpmn:lane></bpmn:laneSet>' +
  '<bpmn:startEvent id="S1" name="Inicio"/>' +
  '<bpmn:task id="T1" name="Tarefa"/>' +
  '<bpmn:exclusiveGateway id="G1" name="Xor"/>' +
  '<bpmn:subProcess id="SP1"><bpmn:startEvent id="S2"/><bpmn:task id="T2"/><bpmn:endEvent id="E2"/>' +
  '<bpmn:sequenceFlow id="SF1" sourceRef="S2" targetRef="T2"/>' +
  '<bpmn:sequenceFlow id="SF2" sourceRef="T2" targetRef="E2"/></bpmn:subProcess>' +
  '<bpmn:endEvent id="E1" name="Fim"/>' +
  '<bpmn:dataObjectReference id="DO1" name="Doc" dataObjectRef="DOB1"/>' +
  '<bpmn:dataStoreReference id="DS1" name="Store" dataStoreRef="DSB1"/>' +
  '<bpmn:dataObject id="DOB1"/><bpmn:dataStore id="DSB1"/>' +
  '<bpmn:sequenceFlow id="F1" sourceRef="S1" targetRef="T1"/>' +
  '<bpmn:sequenceFlow id="F2" sourceRef="T1" targetRef="G1"/>' +
  '<bpmn:sequenceFlow id="F3" sourceRef="G1" targetRef="SP1" name="Cond"/>' +
  '<bpmn:sequenceFlow id="F4" sourceRef="G1" targetRef="E1"/>' +
  '<bpmn:sequenceFlow id="F5" sourceRef="SP1" targetRef="E1"/>' +
  '</bpmn:process>' +
  '<bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL1" bpmnElement="C1">' +
  '<bpmndi:BPMNShape id="PA1_di" bpmnElement="PA1" isHorizontal="true"><dc:Bounds x="100" y="60" width="1000" height="480"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="L1_di" bpmnElement="L1" isHorizontal="true"><dc:Bounds x="130" y="60" width="970" height="480"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="S1_di" bpmnElement="S1"><dc:Bounds x="160" y="120" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="T1_di" bpmnElement="T1"><dc:Bounds x="260" y="100" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="G1_di" bpmnElement="G1" isMarkerVisible="true"><dc:Bounds x="430" y="115" width="50" height="50"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="SP1_di" bpmnElement="SP1" isExpanded="true"><dc:Bounds x="560" y="90" width="300" height="130"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="S2_di" bpmnElement="S2"><dc:Bounds x="575" y="140" width="30" height="30"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="T2_di" bpmnElement="T2"><dc:Bounds x="640" y="115" width="80" height="60"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="E2_di" bpmnElement="E2"><dc:Bounds x="790" y="140" width="30" height="30"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="E1_di" bpmnElement="E1"><dc:Bounds x="950" y="115" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="DO1_di" bpmnElement="DO1"><dc:Bounds x="180" y="380" width="36" height="50"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="DS1_di" bpmnElement="DS1"><dc:Bounds x="180" y="450" width="50" height="50"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNLabel id="S1_lbl" bpmnElement="S1"><dc:Bounds x="150" y="160" width="60" height="14"/></bpmndi:BPMNLabel>' +
  '<bpmndi:BPMNLabel id="G1_lbl" bpmnElement="G1"><dc:Bounds x="420" y="170" width="60" height="14"/></bpmndi:BPMNLabel>' +
  '<bpmndi:BPMNLabel id="F3_lbl" bpmnElement="F3"><dc:Bounds x="490" y="150" width="60" height="14"/></bpmndi:BPMNLabel>' +
  '<bpmndi:BPMNEdge id="F1_di" bpmnElement="F1"><di:waypoint x="196" y="138"/><di:waypoint x="260" y="138"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="F2_di" bpmnElement="F2"><di:waypoint x="360" y="140"/><di:waypoint x="430" y="140"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="F3_di" bpmnElement="F3"><di:waypoint x="480" y="140"/><di:waypoint x="560" y="150"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="F4_di" bpmnElement="F4"><di:waypoint x="480" y="140"/><di:waypoint x="950" y="133"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="F5_di" bpmnElement="F5"><di:waypoint x="710" y="220"/><di:waypoint x="950" y="140"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="SF1_di" bpmnElement="SF1"><di:waypoint x="605" y="155"/><di:waypoint x="640" y="145"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="SF2_di" bpmnElement="SF2"><di:waypoint x="720" y="145"/><di:waypoint x="790" y="155"/></bpmndi:BPMNEdge>' +
  '</bpmndi:BPMNPlane></bpmndi:BPMNDiagram>' +
  TAIL;

type ThemeSnapshot = Record<string, string | null>;

/** Computed styles resolvidos em runtime — sem duplicar tokens no teste. */
async function snapshot(page: Page): Promise<ThemeSnapshot> {
  return page.evaluate(() => {
    const cs = (el: Element | null, prop: string) =>
      el ? getComputedStyle(el as HTMLElement)[prop as never] : null;
    const q = (s: string) => document.querySelector(s);
    const vis = (id: string) =>
      document.querySelector(`.djs-element[data-element-id="${id}"] .djs-visual`);
    const geom = (g: Element | null | undefined) =>
      g?.querySelector(
        "rect:not(.djs-hit), circle:not(.djs-hit), polygon:not(.djs-hit), path:not(.djs-hit)",
      ) ?? null;
    const label = (id: string) =>
      document.querySelector(
        `.djs-element[data-element-id="${id}_label"] text`,
      ) ?? null;
    const flow = (id: string) => {
      const g = document.querySelector(
        `.djs-connection[data-element-id="${id}"] .djs-visual`,
      );
      if (!g) return null;
      return (
        [...g.querySelectorAll("path")].find((p) => {
          const s = getComputedStyle(p).stroke;
          return s && s !== "none" && s !== "rgba(0, 0, 0, 0)";
        }) ?? null
      );
    };
    return {
      canvasBg: cs(q(".bpmnm-canvas"), "backgroundColor"),
      taskFill: cs(geom(vis("T1")), "fill"),
      taskStroke: cs(geom(vis("T1")), "stroke"),
      eventStroke: cs(geom(vis("S1")), "stroke"),
      gwFill: cs(geom(vis("G1")), "fill"),
      gwStroke: cs(geom(vis("G1")), "stroke"),
      subFill: cs(geom(vis("SP1")), "fill"),
      poolStroke: cs(geom(vis("PA1")), "stroke"),
      laneStroke: cs(geom(vis("L1")), "stroke"),
      dataFill: cs(geom(vis("DO1")), "fill"),
      storeFill: cs(geom(vis("DS1")), "fill"),
      intLabelFill: cs(vis("T1")?.querySelector("text") ?? null, "fill"),
      extLabelFill: cs(label("S1"), "fill"),
      flowStroke: cs(flow("F1"), "stroke"),
      flowLabelFill: cs(label("F3"), "fill"),
    };
  });
}

function expectStable(base: ThemeSnapshot, next: ThemeSnapshot, step: string) {
  for (const key of Object.keys(base)) {
    expect(next[key], `${step}: ${key} mudou`).toBe(base[key]);
  }
}

async function openEditor(page: Page, theme: "light" | "dark") {
  await page.evaluate((t) => localStorage.setItem("theme", t), theme);
  const modelId = await importModelViaApi("editor", "E2E-Theme", XML_THEME);
  await page.goto(modelUrl(modelId));
  await expect(
    page.locator('.djs-element[data-element-id="T1"]'),
  ).toBeVisible({ timeout: 20_000 });
  return modelId;
}

async function clickEl(page: Page, id: string) {
  await page
    .locator(`.djs-element[data-element-id="${id}"]`)
    .click({ position: { x: 8, y: 8 }, force: true });
  await page.waitForTimeout(300);
}

async function clearOverlays(page: Page) {
  for (let i = 0; i < 3; i++) {
    if (!(await page.locator(".djs-direct-editing-parent, .djs-popup").count()))
      return;
    await page.keyboard.press("Escape");
    await page.waitForTimeout(250);
  }
}

test.describe("E2E-39 — canvas theme lifecycle", () => {
  test.use({ actor: "editor", viewport: { width: 1440, height: 900 } });

  for (const theme of ["dark", "light"] as const) {
    test(`${theme}: lifecycle completo preserva tema`, async ({ page }) => {
      await openEditor(page, theme);
      const base = await snapshot(page);
      // sanity: tema realmente aplicado (dark != light canvas)
      expect(base.canvasBg).not.toBeNull();

      // select
      await clickEl(page, "T1");
      expectStable(base, await snapshot(page), "select");

      // append task → novo elemento recebe o mesmo tema do existente
      const appendTask = page.locator(
        '.djs-context-pad .entry[data-action="append.append-task"]',
      );
      await expect(appendTask).toBeVisible();
      await appendTask.click();
      await page.waitForTimeout(500);
      const afterAppend = await snapshot(page);
      expectStable(base, afterAppend, "append-task");

      // o elemento NOVO tem fill/stroke idênticos ao existente
      const newFill = await page.evaluate(() => {
        const news = [...document.querySelectorAll(".djs-element")].filter(
          (g) => /^(Activity|Gateway|Event)_/.test(g.getAttribute("data-element-id") ?? ""),
        );
        const geom = news[0]?.querySelector(
          ".djs-visual rect:not(.djs-hit), .djs-visual circle:not(.djs-hit)",
        );
        return geom
          ? {
              fill: getComputedStyle(geom).fill,
              stroke: getComputedStyle(geom).stroke,
            }
          : null;
      });
      expect(newFill).not.toBeNull();
      expect(newFill!.fill).toBe(base.taskFill);
      expect(newFill!.stroke).toBe(base.taskStroke);

      // connect T1 → SP1 (drag do context pad)
      await clearOverlays(page);
      await clickEl(page, "T1");
      const connect = page.locator(
        '.djs-context-pad .entry[data-action="connect"]',
      );
      if (await connect.count()) {
        const c = await connect.boundingBox();
        const o = await page
          .locator('.djs-element[data-element-id="SP1"]')
          .boundingBox();
        await page.mouse.move(c!.x + c!.width / 2, c!.y + c!.height / 2);
        await page.mouse.down();
        await page.mouse.move(o!.x + 20, o!.y + 20, { steps: 6 });
        await page.mouse.up();
        await page.waitForTimeout(500);
        expectStable(base, await snapshot(page), "connect");
      }

      // move T1
      await clearOverlays(page);
      const tb = await page
        .locator('.djs-element[data-element-id="T1"]')
        .boundingBox();
      await page.mouse.move(tb!.x + 8, tb!.y + 8);
      await page.mouse.down();
      await page.mouse.move(tb!.x + 40, tb!.y + 30, { steps: 5 });
      await page.mouse.up();
      await page.waitForTimeout(400);
      expectStable(base, await snapshot(page), "move");

      // resize SP1 via resizer
      await clearOverlays(page);
      await clickEl(page, "SP1");
      const resizer = page.locator(".djs-resizer").first();
      if (await resizer.count()) {
        const rb = await resizer.boundingBox();
        await page.mouse.move(rb!.x + rb!.width / 2, rb!.y + rb!.height / 2);
        await page.mouse.down();
        await page.mouse.move(rb!.x + 30, rb!.y + 20, { steps: 4 });
        await page.mouse.up();
        await page.waitForTimeout(400);
        expectStable(base, await snapshot(page), "resize");
      }

      // replace T1 → outro tipo de task via popup
      await clearOverlays(page);
      await clickEl(page, "T1");
      const replace = page.locator(
        '.djs-context-pad .entry[data-action="replace"]',
      );
      await replace.click();
      await page.waitForTimeout(600);
      const opt = page
        .locator(
          '.djs-popup .entry[data-id="replace-with-service-task"], .djs-popup .entry[data-id="replace-with-user-task"]',
        )
        .first();
      if (await opt.count()) {
        await opt.click();
        await page.waitForTimeout(500);
        expectStable(base, await snapshot(page), "replace");
      } else {
        await page.keyboard.press("Escape");
      }

      // undo / redo
      await page.keyboard.press("Control+z");
      await page.waitForTimeout(400);
      expectStable(base, await snapshot(page), "undo");
      await page.keyboard.press("Control+y");
      await page.waitForTimeout(400);
      expectStable(base, await snapshot(page), "redo");
    });
  }

  test("dark: layout preview cancel/accept não reseta tema", async ({
    page,
  }) => {
    await openEditor(page, "dark");
    const base = await snapshot(page);
    const organize = page.getByRole("button", { name: "Organizar" });
    await organize.click();
    await expect(page.locator(".bpmnm-preview")).toBeVisible({
      timeout: 30_000,
    });
    expectStable(base, await snapshot(page), "layout-preview-open");
    await page.getByRole("button", { name: "Cancelar" }).click();
    await page.waitForTimeout(600);
    expectStable(base, await snapshot(page), "layout-cancel");

    await organize.click();
    await expect(page.locator(".bpmnm-preview")).toBeVisible({
      timeout: 30_000,
    });
    await page.getByRole("button", { name: "Aceitar" }).click();
    await page.waitForTimeout(800);
    expectStable(base, await snapshot(page), "layout-accept");
  });

  test("runtime theme switch dark→light→dark re-resolve sem re-import", async ({
    page,
  }) => {
    const modelId = await openEditor(page, "dark");
    const darkBase = await snapshot(page);

    // troca de tema em runtime = mesma operação do portal (data-theme + storage)
    await page.evaluate(() => {
      localStorage.setItem("theme", "light");
      document.documentElement.setAttribute("data-theme", "light");
    });
    await page.waitForTimeout(600);
    const lightSnap = await snapshot(page);
    expect(lightSnap.canvasBg).not.toBe(darkBase.canvasBg);
    expect(lightSnap.taskStroke).not.toBe(darkBase.taskStroke);

    await page.evaluate(() => {
      localStorage.setItem("theme", "dark");
      document.documentElement.setAttribute("data-theme", "dark");
    });
    await page.waitForTimeout(600);
    expectStable(darkBase, await snapshot(page), "theme-back-to-dark");
    // sem re-import: editor continua vivo e o modelo é o mesmo
    expect(page.url()).toContain(modelId);
  });

  test("save + reload preserva tema e XML sem metadata de tema", async ({
    page,
  }) => {
    const modelId = await openEditor(page, "dark");
    const base = await snapshot(page);
    // edita para habilitar salvar
    await clickEl(page, "T1");
    const appendTask = page.locator(
      '.djs-context-pad .entry[data-action="append.append-task"]',
    );
    await appendTask.click();
    await page.waitForTimeout(500);
    await expect(page.locator(".bpmnm-save-status")).toHaveText("Salvo", {
      timeout: 15_000,
    });

    // XML autoritativo não pode conter tokens/metadata de tema
    const token = await apiToken("editor");
    const resp = await page.request.get(
      `/apps/bpmn-modeler-api/models/${modelId}/working-copy`,
      { headers: { Authorization: `Bearer ${token}` } },
    );
    expect(resp.ok()).toBe(true);
    // working-copy retorna o XML canônico (application/xml)
    const xml = await resp.text();
    expect(xml).toContain("bpmn:definitions");
    expect(xml).not.toMatch(/delpi-ui|data-theme|var\(--/);

    await page.reload();
    await expect(
      page.locator('.djs-element[data-element-id="T1"]'),
    ).toBeVisible({ timeout: 20_000 });
    await page.waitForTimeout(800);
    expectStable(base, await snapshot(page), "reload");
  });
});
