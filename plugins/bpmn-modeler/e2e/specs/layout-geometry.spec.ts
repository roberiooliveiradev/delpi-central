import { test, expect, importModelViaApi, modelUrl, apiToken } from "../helpers";
import type { Page } from "@playwright/test";
import { request } from "@playwright/test";

/**
 * E2E-47 — auto-layout preserva dimensões de shapes (BPMN-DI).
 *
 * Regressão corrigida: o grafo ELK recebia uma TABELA de tamanhos por
 * tipo (nodeSizeFor) em vez dos bounds DI vigentes, e o Accept gravava
 * width/height do ELK no di.bounds — elementos custom ou fora do
 * default eram "escalados". Política:
 *   SIZE_PRESERVED     — todo nó não-container (event/task/gateway/data)
 *   LAYOUT_MAY_RESIZE  — participant/lane/subProcess expandido/etc
 * Preview é artefato transient; canonical só muda no Accept.
 */

const XML =
  '<?xml version="1.0" encoding="UTF-8"?>' +
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ' +
  'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" ' +
  'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" ' +
  'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" ' +
  'id="defs_lgeo" targetNamespace="urn:lgeo">' +
  '<bpmn:collaboration id="C1">' +
  '<bpmn:participant id="POOL1" name="Pool" processRef="P1"/>' +
  "</bpmn:collaboration>" +
  '<bpmn:process id="P1">' +
  '<bpmn:laneSet><bpmn:lane id="LANE1" name="Lane">' +
  "<bpmn:flowNodeRef>S1</bpmn:flowNodeRef><bpmn:flowNodeRef>T1</bpmn:flowNodeRef>" +
  "<bpmn:flowNodeRef>G1</bpmn:flowNodeRef><bpmn:flowNodeRef>T2</bpmn:flowNodeRef>" +
  "<bpmn:flowNodeRef>E1</bpmn:flowNodeRef><bpmn:flowNodeRef>SUB1</bpmn:flowNodeRef>" +
  "</bpmn:lane></bpmn:laneSet>" +
  '<bpmn:startEvent id="S1"/><bpmn:task id="T1" name="Custom"/>' +
  '<bpmn:exclusiveGateway id="G1"/><bpmn:task id="T2"/><bpmn:endEvent id="E1"/>' +
  '<bpmn:subProcess id="SUB1" name="Sub">' +
  '<bpmn:startEvent id="SS1"/><bpmn:task id="ST1"/><bpmn:endEvent id="SE1"/>' +
  '<bpmn:sequenceFlow id="SF1" sourceRef="SS1" targetRef="ST1"/>' +
  '<bpmn:sequenceFlow id="SF2" sourceRef="ST1" targetRef="SE1"/>' +
  "</bpmn:subProcess>" +
  '<bpmn:dataStoreReference id="DS1"/>' +
  '<bpmn:sequenceFlow id="F1" sourceRef="S1" targetRef="T1"/>' +
  '<bpmn:sequenceFlow id="F2" sourceRef="T1" targetRef="G1"/>' +
  '<bpmn:sequenceFlow id="F3" sourceRef="G1" targetRef="T2"/>' +
  '<bpmn:sequenceFlow id="F4" sourceRef="T2" targetRef="E1"/>' +
  '<bpmn:sequenceFlow id="F5" sourceRef="G1" targetRef="SUB1"/>' +
  '<bpmn:sequenceFlow id="F6" sourceRef="SUB1" targetRef="E1"/>' +
  "</bpmn:process>" +
  '<bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL1" bpmnElement="C1">' +
  '<bpmndi:BPMNShape id="sp_POOL1" bpmnElement="POOL1"><dc:Bounds x="60" y="60" width="750" height="330"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_LANE1" bpmnElement="LANE1"><dc:Bounds x="90" y="80" width="690" height="290"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_S1" bpmnElement="S1"><dc:Bounds x="120" y="120" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_T1" bpmnElement="T1"><dc:Bounds x="210" y="98" width="140" height="90"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_G1" bpmnElement="G1"><dc:Bounds x="400" y="118" width="50" height="50"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_T2" bpmnElement="T2"><dc:Bounds x="500" y="98" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_E1" bpmnElement="E1"><dc:Bounds x="650" y="120" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_SUB1" bpmnElement="SUB1" isExpanded="true"><dc:Bounds x="150" y="190" width="380" height="220"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_SS1" bpmnElement="SS1"><dc:Bounds x="170" y="230" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_ST1" bpmnElement="ST1"><dc:Bounds x="240" y="208" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_SE1" bpmnElement="SE1"><dc:Bounds x="400" y="230" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_DS1" bpmnElement="DS1"><dc:Bounds x="560" y="220" width="60" height="60"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNEdge id="e_F1" bpmnElement="F1"><di:waypoint x="156" y="138"/><di:waypoint x="210" y="138"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="e_F2" bpmnElement="F1"><di:waypoint x="350" y="143"/><di:waypoint x="400" y="143"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="e_F3" bpmnElement="F3"><di:waypoint x="450" y="143"/><di:waypoint x="500" y="138"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="e_F4" bpmnElement="F4"><di:waypoint x="600" y="138"/><di:waypoint x="650" y="138"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="e_F5" bpmnElement="F5"><di:waypoint x="425" y="168"/><di:waypoint x="300" y="190"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="e_F6" bpmnElement="F6"><di:waypoint x="530" y="260"/><di:waypoint x="668" y="156"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="e_SF1" bpmnElement="SF1"><di:waypoint x="206" y="248"/><di:waypoint x="240" y="248"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="e_SF2" bpmnElement="SF2"><di:waypoint x="340" y="248"/><di:waypoint x="400" y="248"/></bpmndi:BPMNEdge>' +
  "</bpmndi:BPMNPlane></bpmndi:BPMNDiagram></bpmn:definitions>";

type Bounds = { x: number; y: number; width: number; height: number };

async function openEditor(page: Page): Promise<string> {
  const modelId = await importModelViaApi("editor", "E2E-LayoutGeom", XML);
  await page.goto(modelUrl(modelId));
  await expect(
    page.locator('.djs-element[data-element-id="T1"]'),
  ).toBeVisible({ timeout: 20_000 });
  await page.waitForTimeout(600);
  return modelId;
}

/** Bounds do elemento no DOM do canvas (translate + bbox do visual). */
async function domBounds(page: Page, id: string): Promise<Bounds> {
  return page.evaluate((elId) => {
    const g = document.querySelector(
      `[data-element-id="${elId}"]`,
    ) as SVGGElement | null;
    if (!g) return null;
    const tf = g.getAttribute("transform") ?? "";
    // bpmn-js emite translate(x,y) no import e matrix(a,b,c,d,e,f) após layout
    const m =
      /translate\(([-\d.e]+)[ ,]+([-\d.e]+)\)/.exec(tf) ??
      /matrix\([-\d.e]+[ ,]+[-\d.e]+[ ,]+[-\d.e]+[ ,]+[-\d.e]+[ ,]+([-\d.e]+)[ ,]+([-\d.e]+)\)/.exec(
        tf,
      );
    const visual = g.querySelector(".djs-visual") as SVGGElement | null;
    const bb = (visual ?? g).getBBox();
    return {
      x: Number(m?.[1] ?? NaN),
      y: Number(m?.[2] ?? NaN),
      width: bb.width,
      height: bb.height,
    };
  }, id) as Promise<Bounds>;
}

async function diBoundsFromXml(modelId: string): Promise<Map<string, Bounds>> {
  const base = process.env.BPMN_E2E_BASE_URL ?? "http://localhost";
  const token = await apiToken("editor");
  const ctx = await request.newContext({ baseURL: base });
  const resp = await ctx.get(
    `/apps/bpmn-modeler-api/models/${modelId}/working-copy`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
  if (!resp.ok()) throw new Error(`read-back failed: ${resp.status()}`);
  const xml = await resp.text();
  const map = new Map<string, Bounds>();
  const re =
    /bpmnElement="([^"]+)"[^>]*>\s*<dc:Bounds x="([-\d.]+)" y="([-\d.]+)" width="([-\d.]+)" height="([-\d.]+)"/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(xml))) {
    map.set(m[1], {
      x: +m[2],
      y: +m[3],
      width: +m[4],
      height: +m[5],
    });
  }
  return map;
}

async function organize(page: Page, accept: boolean) {
  await page.getByRole("button", { name: "Organizar" }).click();
  await expect(
    page.getByRole("button", { name: "Aceitar" }),
  ).toBeVisible({ timeout: 20_000 });
  await page.waitForTimeout(400);
  await page
    .getByRole("button", { name: accept ? "Aceitar" : "Cancelar" })
    .first()
    .click();
  await page.waitForTimeout(500);
}

async function save(page: Page) {
  const btn = page.getByRole("button", { name: "Salvar" });
  await expect(btn).toBeEnabled({ timeout: 10_000 });
  await btn.click();
  await expect(btn).toBeDisabled({ timeout: 15_000 });
}

// famílias SIZE_PRESERVED (w/h nunca mudam no layout)
const PRESERVED = ["S1", "T1", "G1", "T2", "E1", "SS1", "ST1", "SE1", "DS1"];
// dimensões custom do fixture (≠ tabela vendor)
const CUSTOM: Record<string, { width: number; height: number }> = {
  T1: { width: 140, height: 90 },
  SUB1: { width: 380, height: 220 },
  DS1: { width: 60, height: 60 },
  POOL1: { width: 750, height: 330 },
  LANE1: { width: 690, height: 290 },
};

test.describe("E2E-47 — auto-layout size preservation", () => {
  test.use({ actor: "editor", viewport: { width: 1440, height: 900 } });

  test("LGEO-01: Accept preserva w/h de não-containers (DI read-back)", async ({
    page,
  }) => {
    const modelId = await openEditor(page);
    // fonte de verdade das dimensões: BPMN-DI vigente (working-copy)
    const beforeDi = await diBoundsFromXml(modelId);
    const beforeDom = new Map<string, Bounds>();
    for (const id of PRESERVED) beforeDom.set(id, await domBounds(page, id));
    expect(beforeDi.get("T1")).toMatchObject({ width: 140, height: 90 });

    await organize(page, true);

    const moved = new Set<string>();
    for (const id of PRESERVED) {
      const b = beforeDom.get(id)!;
      const a = await domBounds(page, id);
      expect(a.width, `${id}.width`).toBeCloseTo(b.width, 0);
      expect(a.height, `${id}.height`).toBeCloseTo(b.height, 0);
      if (a.x !== b.x || a.y !== b.y) moved.add(id);
    }
    expect(moved.size).toBeGreaterThan(0); // layout realmente moveu

    // authoritative read-back: DI persistido preserva w/h
    await save(page);
    const di = await diBoundsFromXml(modelId);
    for (const id of PRESERVED) {
      const b = beforeDi.get(id)!;
      const p = di.get(id);
      expect(p, `${id} ausente no DI`).toBeTruthy();
      expect(p!.width, `${id} DI width`).toBeCloseTo(b.width, 0);
      expect(p!.height, `${id} DI height`).toBeCloseTo(b.height, 0);
    }
    // reload: mesmo resultado visual
    await page.reload();
    await expect(
      page.locator('.djs-element[data-element-id="T1"]'),
    ).toBeVisible({ timeout: 20_000 });
    const reloaded = await domBounds(page, "T1");
    expect(reloaded.width).toBeCloseTo(140, 0);
    expect(reloaded.height).toBeCloseTo(90, 0);
  });

  test("LGEO-02: Cancel não altera geometria nem canonical", async ({
    page,
  }) => {
    const modelId = await openEditor(page);
    const before = await diBoundsFromXml(modelId);
    const domBefore = await domBounds(page, "T1");

    await organize(page, false);

    const domAfter = await domBounds(page, "T1");
    expect(domAfter).toEqual(domBefore);
    const after = await diBoundsFromXml(modelId);
    expect(after.get("T1")).toEqual(before.get("T1"));
    // Salvar continua desabilitado (preview não sujou o canvas)
    await expect(
      page.getByRole("button", { name: "Salvar" }),
    ).toBeDisabled();
  });

  test("LGEO-03: undo/redo restauram a geometria exata", async ({ page }) => {
    await openEditor(page);
    const before = await domBounds(page, "T1");
    const beforeG = await domBounds(page, "G1");

    await organize(page, true);
    const accepted = await domBounds(page, "T1");
    expect(accepted.x !== before.x || accepted.y !== before.y).toBe(true);

    await page.locator('button[aria-label="Desfazer"]').click();
    await page.waitForTimeout(300);
    expect(await domBounds(page, "T1")).toEqual(before);
    expect(await domBounds(page, "G1")).toEqual(beforeG);

    await page.locator('button[aria-label="Refazer"]').click();
    await page.waitForTimeout(300);
    const redone = await domBounds(page, "T1");
    expect(redone.x).toBeCloseTo(accepted.x, 0);
    expect(redone.width).toBeCloseTo(140, 0);
  });

  test("LGEO-04: novo elemento pós-layout tem escala da família", async ({
    page,
  }) => {
    await openEditor(page);
    await organize(page, true);

    // append via context pad (T2 no meio do canvas — S1 fica sob a palette)
    await page.locator('.djs-element[data-element-id="T2"]').click();
    const pad = page.locator(".djs-context-pad");
    await expect(pad).toBeVisible();
    await pad.locator('[data-action="append.append-task"]').click();
    await page.waitForTimeout(500);

    // novo task criado pelo bpmn-js (id gerado)
    const tasks = page.locator(
      '.djs-element[data-element-id^="Activity_"]',
    );
    await expect(tasks.first()).toBeVisible({ timeout: 5_000 });
    const freshId = await tasks.first().getAttribute("data-element-id");
    const fresh = await domBounds(page, freshId!);
    expect(fresh.width).toBeCloseTo(100, 0);
    expect(fresh.height).toBeCloseTo(80, 0);

    // e o elemento custom continua custom — escala única
    const t1 = await domBounds(page, "T1");
    expect(t1.width).toBeCloseTo(140, 0);
    const t2 = await domBounds(page, "T2");
    expect(t2.width).toBeCloseTo(100, 0); // default preservado igual ao novo
  });

  test("LGEO-05: selection outline segue bounds reais (sem fake)", async ({
    page,
  }) => {
    await openEditor(page);
    await organize(page, true);
    const t1 = await domBounds(page, "T1");

    await page.locator('.djs-element[data-element-id="T1"]').click();
    const outline = page.locator(
      '[data-element-id="T1"] > rect.djs-outline',
    );
    await expect(outline).toBeAttached();
    const w = Number(await outline.getAttribute("width"));
    const h = Number(await outline.getAttribute("height"));
    // outline = bounds + padding do selection (~10px)
    expect(w).toBeGreaterThan(t1.width);
    expect(w).toBeLessThan(t1.width + 30);
    expect(h).toBeGreaterThan(t1.height);
    expect(h).toBeLessThan(t1.height + 30);
    // context pad ancorado junto ao shape
    await expect(page.locator(".djs-context-pad")).toBeVisible();
  });

  test("LGEO-06: containers podem mudar de tamanho; filhos não escalam", async ({
    page,
  }) => {
    const modelId = await openEditor(page);
    await organize(page, true);
    await save(page);
    const di = await diBoundsFromXml(modelId);

    // filhos de lane/pool/subprocess preservam dims (children NOT scaled)
    const EXPECTED_W: Record<string, number> = {
      S1: 36, T1: 140, G1: 50, T2: 100, E1: 36,
      SS1: 36, ST1: 100, SE1: 36,
    };
    for (const [id, w] of Object.entries(EXPECTED_W)) {
      const p = di.get(id)!;
      expect(p.width, `${id}.width`).toBeCloseTo(w, 0);
    }
    // containers: dims presentes e positivas (ELK pode ajustar)
    for (const id of ["POOL1", "LANE1", "SUB1"]) {
      const p = di.get(id)!;
      expect(p.width).toBeGreaterThan(0);
      expect(p.height).toBeGreaterThan(0);
    }
    // subprocess filhos permanecem dentro do container
    const sub = di.get("SUB1")!;
    const st = di.get("ST1")!;
    expect(st.x).toBeGreaterThanOrEqual(sub.x);
    expect(st.x + st.width).toBeLessThanOrEqual(sub.x + sub.width);
    expect(st.y).toBeGreaterThanOrEqual(sub.y);
    expect(st.y + st.height).toBeLessThanOrEqual(sub.y + sub.height);
  });
});
