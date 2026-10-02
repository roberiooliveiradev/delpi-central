import { test, expect, importModelViaApi, modelUrl, apiToken } from "../helpers";
import type { Page } from "@playwright/test";
import { request } from "@playwright/test";

/**
 * E2E-48 — auto-layout: containment Pool/Lane/SubProcess + preview fidelity.
 *
 * Regressões corrigidas:
 *  A. lane.flowNodeRef / participant.processRef não dirigiam a hierarquia
 *     ELK → membros saíam do pool após Organizar.
 *  B. buildDiXml recriava BPMNShape sem atributos → isExpanded perdido no
 *     preview (subprocess expandido renderizava collapsed).
 * Política: containment ELK é derivado da semântica BPMN; containers
 * podem crescer para conter filhos; filhos nunca escalam.
 */

const XML =
  '<?xml version="1.0" encoding="UTF-8"?>' +
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ' +
  'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" ' +
  'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" ' +
  'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" ' +
  'id="defs_hier" targetNamespace="urn:hier">' +
  '<bpmn:collaboration id="C1">' +
  '<bpmn:participant id="POOL1" name="Pool A" processRef="P1"/>' +
  '<bpmn:participant id="POOL2" name="Pool B" processRef="P2"/>' +
  '<bpmn:messageFlow id="MF1" sourceRef="T_B" targetRef="T1"/>' +
  "</bpmn:collaboration>" +
  '<bpmn:process id="P1"><bpmn:laneSet>' +
  '<bpmn:lane id="LANE_A" name="Lane A">' +
  "<bpmn:flowNodeRef>S1</bpmn:flowNodeRef><bpmn:flowNodeRef>T1</bpmn:flowNodeRef>" +
  "<bpmn:flowNodeRef>G1</bpmn:flowNodeRef><bpmn:flowNodeRef>SUB1</bpmn:flowNodeRef>" +
  "<bpmn:flowNodeRef>DO1</bpmn:flowNodeRef></bpmn:lane>" +
  '<bpmn:lane id="LANE_B" name="Lane B">' +
  "<bpmn:flowNodeRef>T2</bpmn:flowNodeRef><bpmn:flowNodeRef>E1</bpmn:flowNodeRef>" +
  "<bpmn:flowNodeRef>SUBC</bpmn:flowNodeRef><bpmn:flowNodeRef>DS1</bpmn:flowNodeRef></bpmn:lane>" +
  "</bpmn:laneSet>" +
  '<bpmn:startEvent id="S1" name="Início"/><bpmn:task id="T1" name="Tarefa"/>' +
  '<bpmn:exclusiveGateway id="G1" name="Decisão"/>' +
  '<bpmn:task id="T2"/><bpmn:endEvent id="E1" name="Fim"/>' +
  '<bpmn:dataObjectReference id="DO1" name="Doc"/>' +
  '<bpmn:dataStoreReference id="DS1" name="Store"/>' +
  '<bpmn:subProcess id="SUB1" name="Sub expandido">' +
  '<bpmn:startEvent id="SS1"/><bpmn:task id="ST1"/><bpmn:endEvent id="SE1"/>' +
  '<bpmn:sequenceFlow id="SF1" sourceRef="SS1" targetRef="ST1"/>' +
  '<bpmn:sequenceFlow id="SF2" sourceRef="ST1" targetRef="SE1"/>' +
  "</bpmn:subProcess>" +
  '<bpmn:subProcess id="SUBC" name="Sub colapsado"><bpmn:task id="SC1"/></bpmn:subProcess>' +
  '<bpmn:sequenceFlow id="F1" sourceRef="S1" targetRef="T1"/>' +
  '<bpmn:sequenceFlow id="F2" sourceRef="T1" targetRef="G1"/>' +
  '<bpmn:sequenceFlow id="F3" name="Cross" sourceRef="G1" targetRef="T2"/>' +
  '<bpmn:sequenceFlow id="F4" sourceRef="T2" targetRef="E1"/>' +
  '<bpmn:sequenceFlow id="F5" sourceRef="G1" targetRef="SUB1"/>' +
  '<bpmn:sequenceFlow id="F6" sourceRef="T2" targetRef="SUBC"/>' +
  "</bpmn:process>" +
  '<bpmn:process id="P2"><bpmn:task id="T_B" name="Task B"/></bpmn:process>' +
  '<bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL1" bpmnElement="C1">' +
  '<bpmndi:BPMNShape id="sp_POOL1" bpmnElement="POOL1" isHorizontal="true">' +
  '<dc:Bounds x="60" y="60" width="840" height="560"/>' +
  '<bpmndi:BPMNLabel><dc:Bounds x="230" y="280" width="40" height="14"/></bpmndi:BPMNLabel></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_LANE_A" bpmnElement="LANE_A">' +
  '<dc:Bounds x="90" y="60" width="810" height="270"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_LANE_B" bpmnElement="LANE_B">' +
  '<dc:Bounds x="90" y="330" width="810" height="290"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_POOL2" bpmnElement="POOL2" isHorizontal="true">' +
  '<dc:Bounds x="60" y="680" width="840" height="200"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_S1" bpmnElement="S1"><dc:Bounds x="130" y="110" width="36" height="36"/>' +
  '<bpmndi:BPMNLabel><dc:Bounds x="123" y="150" width="50" height="14"/></bpmndi:BPMNLabel></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_T1" bpmnElement="T1"><dc:Bounds x="230" y="88" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_G1" bpmnElement="G1"><dc:Bounds x="390" y="103" width="50" height="50"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_DO1" bpmnElement="DO1"><dc:Bounds x="240" y="240" width="36" height="50"/>' +
  '<bpmndi:BPMNLabel><dc:Bounds x="245" y="294" width="26" height="14"/></bpmndi:BPMNLabel></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_SUB1" bpmnElement="SUB1" isExpanded="true">' +
  '<dc:Bounds x="490" y="80" width="360" height="220"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_SS1" bpmnElement="SS1"><dc:Bounds x="510" y="170" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_ST1" bpmnElement="ST1"><dc:Bounds x="600" y="148" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_SE1" bpmnElement="SE1"><dc:Bounds x="760" y="170" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_T2" bpmnElement="T2"><dc:Bounds x="230" y="390" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_E1" bpmnElement="E1"><dc:Bounds x="560" y="412" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_SUBC" bpmnElement="SUBC" isExpanded="false">' +
  '<dc:Bounds x="700" y="390" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_DS1" bpmnElement="DS1"><dc:Bounds x="390" y="405" width="50" height="50"/>' +
  '<bpmndi:BPMNLabel><dc:Bounds x="396" y="459" width="40" height="14"/></bpmndi:BPMNLabel></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_TB" bpmnElement="T_B"><dc:Bounds x="200" y="740" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNEdge id="e_F1" bpmnElement="F1"><di:waypoint x="166" y="128"/><di:waypoint x="230" y="128"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="e_F2" bpmnElement="F2"><di:waypoint x="330" y="128"/><di:waypoint x="390" y="128"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="e_F3" bpmnElement="F3"><di:waypoint x="415" y="153"/><di:waypoint x="280" y="390"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="e_F4" bpmnElement="F4"><di:waypoint x="330" y="430"/><di:waypoint x="560" y="430"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="e_F5" bpmnElement="F5"><di:waypoint x="415" y="103"/><di:waypoint x="490" y="148"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="e_F6" bpmnElement="F6"><di:waypoint x="330" y="430"/><di:waypoint x="700" y="430"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="e_SF1" bpmnElement="SF1"><di:waypoint x="546" y="188"/><di:waypoint x="600" y="188"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="e_SF2" bpmnElement="SF2"><di:waypoint x="700" y="188"/><di:waypoint x="760" y="188"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="e_MF1" bpmnElement="MF1"><di:waypoint x="250" y="740"/><di:waypoint x="280" y="168"/></bpmndi:BPMNEdge>' +
  "</bpmndi:BPMNPlane></bpmndi:BPMNDiagram></bpmn:definitions>";

type Bounds = { x: number; y: number; width: number; height: number };

const inside = (inner: Bounds, outer: Bounds, tol = 2) =>
  inner.x >= outer.x - tol &&
  inner.y >= outer.y - tol &&
  inner.x + inner.width <= outer.x + outer.width + tol &&
  inner.y + inner.height <= outer.y + outer.height + tol;

async function openEditor(page: Page): Promise<string> {
  const modelId = await importModelViaApi("editor", "E2E-LayoutHier", XML);
  await page.goto(modelUrl(modelId));
  await expect(
    page.locator('.djs-element[data-element-id="T1"]'),
  ).toBeVisible({ timeout: 20_000 });
  await page.waitForTimeout(600);
  return modelId;
}

/** Bounds DOM (canvas principal ou preview) em px de tela —
 *  getBoundingClientRect é imune ao aninhamento djs-children do vendor. */
async function domBounds(
  page: Page,
  id: string,
  scope = "",
): Promise<Bounds | null> {
  return page.evaluate(
    ({ elId, sel }) => {
      const root = sel ? document.querySelector(sel) : document;
      const g = (root ?? document).querySelector(
        `[data-element-id="${elId}"]`,
      ) as SVGGElement | null;
      if (!g) return null;
      const visual = g.querySelector(":scope > .djs-visual") ?? g;
      const r = (visual as Element).getBoundingClientRect();
      return { x: r.x, y: r.y, width: r.width, height: r.height };
    },
    { elId: id, sel: scope },
  ) as Promise<Bounds | null>;
}

async function workingCopyXml(modelId: string): Promise<string> {
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

async function diBoundsFromXml(modelId: string): Promise<Map<string, Bounds>> {
  const xml = await workingCopyXml(modelId);
  const map = new Map<string, Bounds>();
  const re =
    /bpmnElement="([^"]+)"[^>]*>\s*<dc:Bounds x="([-\d.]+)" y="([-\d.]+)" width="([-\d.]+)" height="([-\d.]+)"/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(xml))) {
    map.set(m[1], { x: +m[2], y: +m[3], width: +m[4], height: +m[5] });
  }
  return map;
}

async function startOrganize(page: Page) {
  await page.getByRole("button", { name: "Organizar" }).click();
  await expect(
    page.getByRole("button", { name: "Aceitar" }),
  ).toBeVisible({ timeout: 20_000 });
  await expect(
    page.locator('[data-testid="layout-preview"] svg[data-element-id="C1"]'),
  ).toBeVisible({ timeout: 20_000 });
  await page.waitForTimeout(400);
}

async function save(page: Page) {
  const btn = page.getByRole("button", { name: "Salvar" });
  await expect(btn).toBeEnabled({ timeout: 10_000 });
  await btn.click();
  await expect(btn).toBeDisabled({ timeout: 15_000 });
}

const LANE_A_MEMBERS = ["S1", "T1", "G1", "SUB1", "DO1"];
const LANE_B_MEMBERS = ["T2", "E1", "SUBC", "DS1"];
const SUB1_CHILDREN = ["SS1", "ST1", "SE1"];
const PREVIEW = '[data-testid="layout-preview"]';

test.describe("E2E-48 — auto-layout containment & preview fidelity", () => {
  test.use({ actor: "editor", viewport: { width: 1440, height: 900 } });

  test("HIER-01: Accept — lanes/pool/subprocess contêm seus membros", async ({
    page,
  }) => {
    await openEditor(page);
    await page.screenshot({
      path: "../.tmp-shots/layout-hier-before.png",
      fullPage: false,
    });
    await startOrganize(page);
    await page.getByRole("button", { name: "Aceitar" }).first().click();
    await page.waitForTimeout(600);

    const b = async (id: string) => (await domBounds(page, id))!;
    const laneA = await b("LANE_A");
    const laneB = await b("LANE_B");
    const pool1 = await b("POOL1");
    const pool2 = await b("POOL2");
    const sub1 = await b("SUB1");

    // ordem das lanes preservada (A acima de B)
    expect(laneA.y).toBeLessThan(laneB.y);

    for (const id of LANE_A_MEMBERS) {
      const m = await b(id);
      expect(inside(m, laneA), `${id} dentro de LANE_A`).toBe(true);
    }
    for (const id of LANE_B_MEMBERS) {
      const m = await b(id);
      expect(inside(m, laneB), `${id} dentro de LANE_B`).toBe(true);
    }
    for (const id of SUB1_CHILDREN) {
      const m = await b(id);
      expect(inside(m, sub1), `${id} dentro de SUB1`).toBe(true);
    }
    for (const id of [...LANE_A_MEMBERS, ...LANE_B_MEMBERS]) {
      const m = await b(id);
      expect(inside(m, pool1), `${id} dentro de POOL1`).toBe(true);
    }
    const tb = await b("T_B");
    expect(inside(tb, pool2), "T_B dentro de POOL2").toBe(true);

    // collapsed subprocess: conteúdo não renderizado, `isExpanded` intacto
    expect(await domBounds(page, "SC1")).toBeNull();

    await page.screenshot({
      path: "../.tmp-shots/layout-hier-after-accept.png",
      fullPage: false,
    });
  });

  test("HIER-02: preview mostra subProcess expandido + containment real", async ({
    page,
  }) => {
    await openEditor(page);
    await startOrganize(page);

    // Subprocess expandido no preview: filhos renderizados (não collapsed)
    const st1 = await domBounds(page, "ST1", PREVIEW);
    expect(st1, "ST1 visível no preview (SUB1 expandido)").not.toBeNull();
    // collapsed subprocess continua collapsed no preview
    expect(await domBounds(page, "SC1", PREVIEW)).toBeNull();

    // containment no preview == resultado que o Accept aplicará
    const laneA = (await domBounds(page, "LANE_A", PREVIEW))!;
    for (const id of LANE_A_MEMBERS) {
      const m = (await domBounds(page, id, PREVIEW))!;
      expect(m, `${id} presente no preview`).not.toBeNull();
      expect(inside(m, laneA), `${id} dentro de LANE_A no preview`).toBe(true);
    }
    const sub1 = (await domBounds(page, "SUB1", PREVIEW))!;
    for (const id of SUB1_CHILDREN) {
      const m = (await domBounds(page, id, PREVIEW))!;
      expect(inside(m, sub1), `${id} dentro de SUB1 no preview`).toBe(true);
    }
    await page.screenshot({
      path: "../.tmp-shots/layout-hier-preview.png",
      fullPage: false,
    });
  });

  test("HIER-03: Cancel não altera geometria nem canonical", async ({
    page,
  }) => {
    const modelId = await openEditor(page);
    const before = await diBoundsFromXml(modelId);
    const t1Before = await domBounds(page, "T1");
    await startOrganize(page);
    await page.getByRole("button", { name: "Cancelar" }).first().click();
    await page.waitForTimeout(500);

    const after = await diBoundsFromXml(modelId);
    expect(after.get("T1")).toEqual(before.get("T1"));
    const t1After = (await domBounds(page, "T1"))!;
    expect(t1After.x).toBeCloseTo(t1Before!.x, 0);
    expect(t1After.width).toBeCloseTo(t1Before!.width, 0);
  });

  test("HIER-04: collapsed permanece collapsed; expanded permanece expanded (DI)", async ({
    page,
  }) => {
    const modelId = await openEditor(page);
    await startOrganize(page);
    await page.getByRole("button", { name: "Aceitar" }).first().click();
    await save(page);
    const xml = await workingCopyXml(modelId);
    expect(xml).toContain('bpmnElement="SUB1" isExpanded="true"');
    expect(xml).toContain('bpmnElement="SUBC" isExpanded="false"');
    // semântica intacta: processRef, flowNodeRef, filhos do subprocess
    expect(xml).toContain('processRef="P1"');
    expect(xml).toContain("<bpmn:flowNodeRef>T1</bpmn:flowNodeRef>");
    expect(xml).toContain('<bpmn:task id="SC1"');
  });

  test("HIER-05: undo/redo restauram containment e geometria exata", async ({
    page,
  }) => {
    await openEditor(page);
    const before = new Map<string, Bounds>();
    for (const id of ["POOL1", "LANE_A", "LANE_B", "T1", "T2", "SUB1"]) {
      before.set(id, (await domBounds(page, id))!);
    }
    await startOrganize(page);
    await page.getByRole("button", { name: "Aceitar" }).first().click();
    await page.waitForTimeout(600);

    await page.locator('button[aria-label="Desfazer"]').click();
    await page.waitForTimeout(400);
    for (const [id, b0] of before) {
      const b1 = (await domBounds(page, id))!;
      expect(b1.x, `undo ${id}.x`).toBeCloseTo(b0.x, 0);
      expect(b1.y, `undo ${id}.y`).toBeCloseTo(b0.y, 0);
      expect(b1.width, `undo ${id}.w`).toBeCloseTo(b0.width, 0);
      expect(b1.height, `undo ${id}.h`).toBeCloseTo(b0.height, 0);
    }
    await page.locator('button[aria-label="Refazer"]').click();
    await page.waitForTimeout(400);
    const laneA = (await domBounds(page, "LANE_A"))!;
    expect(inside((await domBounds(page, "T1"))!, laneA)).toBe(true);
  });

  test("HIER-06: save + reload mantêm containment autoritativo", async ({
    page,
  }) => {
    const modelId = await openEditor(page);
    await startOrganize(page);
    await page.getByRole("button", { name: "Aceitar" }).first().click();
    await save(page);

    const di = await diBoundsFromXml(modelId);
    const laneA = di.get("LANE_A")!;
    for (const id of LANE_A_MEMBERS) {
      expect(
        inside(di.get(id)!, laneA),
        `DI ${id} dentro de LANE_A`,
      ).toBe(true);
    }
    const sub1 = di.get("SUB1")!;
    for (const id of SUB1_CHILDREN) {
      expect(inside(di.get(id)!, sub1), `DI ${id} dentro de SUB1`).toBe(true);
    }

    await page.reload();
    await expect(
      page.locator('.djs-element[data-element-id="T1"]'),
    ).toBeVisible({ timeout: 20_000 });
    await page.waitForTimeout(600);
    const laneADom = (await domBounds(page, "LANE_A"))!;
    expect(inside((await domBounds(page, "T1"))!, laneADom)).toBe(true);
    await page.screenshot({
      path: "../.tmp-shots/layout-hier-reloaded.png",
      fullPage: false,
    });
  });
});
