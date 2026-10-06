import { test, expect, importModelViaApi, modelUrl, apiToken } from "../helpers";
import type { Page } from "@playwright/test";
import { request } from "@playwright/test";

/**
 * GROUP — auto-layout preserva o enclosure VISUAL de bpmn:group.
 *
 * bpmn:group é Artifact: não é container semântico (sem flowNodeRef,
 * children ou processRef). A relação "o grupo contém esses elementos"
 * é derivada do BPMN-DI (enclosure geométrica total). Após Organizar,
 * os bounds do grupo são recalculados como bbox dos membros visuais
 * + padding — a intenção visual do usuário sobrevive ao layout sem
 * virar ownership semântico.
 *
 * Política:
 *   FULLY_INSIDE     → membro visual
 *   PARTIAL_OVERLAP  → não é membro
 *   EMPTY_GROUP      → bounds DI preservados
 */

const XML =
  '<?xml version="1.0" encoding="UTF-8"?>' +
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ' +
  'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" ' +
  'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" ' +
  'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" ' +
  'id="defs_grp" targetNamespace="urn:grp">' +
  '<bpmn:process id="P1">' +
  '<bpmn:startEvent id="S1"/><bpmn:task id="T1" name="A"/>' +
  '<bpmn:task id="T2" name="B"/><bpmn:endEvent id="E1"/>' +
  '<bpmn:group id="GRP_A"/>' +
  '<bpmn:group id="GRP_EMPTY"/>' +
  '<bpmn:group id="GRP_PARTIAL"/>' +
  '<bpmn:sequenceFlow id="F1" sourceRef="S1" targetRef="T1"/>' +
  '<bpmn:sequenceFlow id="F2" sourceRef="T1" targetRef="T2"/>' +
  '<bpmn:sequenceFlow id="F3" sourceRef="T2" targetRef="E1"/>' +
  "</bpmn:process>" +
  '<bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL1" bpmnElement="P1">' +
  '<bpmndi:BPMNShape id="sp_S1" bpmnElement="S1"><dc:Bounds x="40" y="100" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_T1" bpmnElement="T1"><dc:Bounds x="150" y="90" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_T2" bpmnElement="T2"><dc:Bounds x="300" y="90" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_E1" bpmnElement="E1"><dc:Bounds x="500" y="100" width="36" height="36"/></bpmndi:BPMNShape>' +
  // GRP_A encloses T1+T2 completamente (130..440 x, 70..190 y)
  '<bpmndi:BPMNShape id="sp_GRP_A" bpmnElement="GRP_A"><dc:Bounds x="130" y="70" width="310" height="120"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_GRP_EMPTY" bpmnElement="GRP_EMPTY"><dc:Bounds x="600" y="300" width="100" height="60"/></bpmndi:BPMNShape>' +
  // GRP_PARTIAL sobrepõe E1 parcialmente (E1 top=100 < 110)
  '<bpmndi:BPMNShape id="sp_GRP_PARTIAL" bpmnElement="GRP_PARTIAL"><dc:Bounds x="480" y="110" width="140" height="40"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNEdge id="e_F1" bpmnElement="F1"><di:waypoint x="76" y="118"/><di:waypoint x="150" y="130"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="e_F2" bpmnElement="F2"><di:waypoint x="250" y="130"/><di:waypoint x="300" y="130"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="e_F3" bpmnElement="F3"><di:waypoint x="400" y="130"/><di:waypoint x="500" y="118"/></bpmndi:BPMNEdge>' +
  "</bpmndi:BPMNPlane></bpmndi:BPMNDiagram></bpmn:definitions>";

type Bounds = { x: number; y: number; width: number; height: number };

const encloses = (outer: Bounds, inner: Bounds) =>
  inner.x >= outer.x &&
  inner.y >= outer.y &&
  inner.x + inner.width <= outer.x + outer.width &&
  inner.y + inner.height <= outer.y + outer.height;

async function openEditor(page: Page): Promise<string> {
  const modelId = await importModelViaApi("editor", "E2E-Group", XML);
  await page.goto(modelUrl(modelId));
  await expect(page.locator('.djs-element[data-element-id="T1"]')).toBeVisible({
    timeout: 20_000,
  });
  await page.waitForTimeout(600);
  return modelId;
}

async function domBounds(page: Page, id: string): Promise<Bounds> {
  return page.evaluate((elId) => {
    const g = document.querySelector(
      `[data-element-id="${elId}"]`,
    ) as SVGGElement | null;
    if (!g) return null;
    const tf = g.getAttribute("transform") ?? "";
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
    map.set(m[1], { x: +m[2], y: +m[3], width: +m[4], height: +m[5] });
  }
  return map;
}

async function organize(page: Page, accept: boolean) {
  await page.getByRole("button", { name: "Organizar" }).click();
  await expect(page.getByRole("button", { name: "Aceitar" })).toBeVisible({
    timeout: 20_000,
  });
  await page.waitForTimeout(400);
  await page
    .getByRole("button", { name: accept ? "Aceitar" : "Cancelar" })
    .first()
    .click();
  await page.waitForTimeout(500);
}

async function save(page: Page) {
  await expect(page.locator(".bpmnm-save-status")).toHaveText("Salvo", {
    timeout: 20_000,
  });
}

test.describe("GROUP — visual enclosure no auto-layout", () => {
  test.use({ actor: "editor", viewport: { width: 1440, height: 900 } });

  test("GROUP-01/02: Accept move membros e o grupo continua envolvendo-os", async ({
    page,
  }) => {
    const modelId = await openEditor(page);
    const beforeGrp = await domBounds(page, "GRP_A");
    const beforeT1 = await domBounds(page, "T1");
    expect(encloses(beforeGrp, beforeT1)).toBe(true);

    await organize(page, true);
    await save(page);

    const grp = await domBounds(page, "GRP_A");
    for (const id of ["T1", "T2"]) {
      const member = await domBounds(page, id);
      expect(encloses(grp, member), `${id} deve ficar dentro de GRP_A`).toBe(
        true,
      );
    }
    // membros realmente se moveram (layout aconteceu)
    const t1 = await domBounds(page, "T1");
    expect(t1.x !== beforeT1.x || t1.y !== beforeT1.y).toBe(true);

    // authoritative read-back: DI persistido reflete o enclosure
    const di = await diBoundsFromXml(modelId);
    const grpDi = di.get("GRP_A")!;
    expect(encloses(grpDi, di.get("T1")!)).toBe(true);
    expect(encloses(grpDi, di.get("T2")!)).toBe(true);
    // XML semântico intocado: grupo não ganhou membership
    const base = process.env.BPMN_E2E_BASE_URL ?? "http://localhost";
    const token = await apiToken("editor");
    const ctx = await request.newContext({ baseURL: base });
    const xml = await (
      await ctx.get(`/apps/bpmn-modeler-api/models/${modelId}/working-copy`, {
        headers: { Authorization: `Bearer ${token}` },
      })
    ).text();
    // o group continua um artifact vazio — nenhum filho/membership escrito
    expect(xml).toMatch(/<bpmn:group id="GRP_A"[^>]*\/>/);
    expect(xml).not.toContain("flowNodeRef");

    // GROUP-05: reload mantém o enclosure (só DI canônico — sem state local)
    await page.reload();
    await expect(
      page.locator('.djs-element[data-element-id="T1"]'),
    ).toBeVisible({ timeout: 20_000 });
    const grpReload = await domBounds(page, "GRP_A");
    for (const id of ["T1", "T2"]) {
      expect(encloses(grpReload, await domBounds(page, id))).toBe(true);
    }
  });

  test("GROUP-03: Cancel não muda o grupo nem suja o modelo", async ({
    page,
  }) => {
    await openEditor(page);
    const before = await domBounds(page, "GRP_A");
    await organize(page, false);
    expect(await domBounds(page, "GRP_A")).toEqual(before);
    await expect(page.locator(".bpmnm-save-status")).toHaveText("Salvo");
  });

  test("GROUP-04: undo/redo restauram e reaplicam bounds do grupo", async ({
    page,
  }) => {
    await openEditor(page);
    const before = await domBounds(page, "GRP_A");
    await organize(page, true);
    const accepted = await domBounds(page, "GRP_A");
    expect(accepted).not.toEqual(before);

    await page.locator('button[aria-label="Desfazer"]').click();
    await page.waitForTimeout(300);
    expect(await domBounds(page, "GRP_A")).toEqual(before);

    await page.locator('button[aria-label="Refazer"]').click();
    await page.waitForTimeout(300);
    const redone = await domBounds(page, "GRP_A");
    expect(redone.x).toBeCloseTo(accepted.x, 0);
    expect(redone.y).toBeCloseTo(accepted.y, 0);
    expect(redone.width).toBeCloseTo(accepted.width, 0);
  });

  test("GROUP-06/07: grupo vazio preserva DI; overlap parcial não vira membro", async ({
    page,
  }) => {
    const modelId = await openEditor(page);
    const beforeEmpty = await domBounds(page, "GRP_EMPTY");
    const beforePartial = await domBounds(page, "GRP_PARTIAL");

    await organize(page, true);
    await save(page);

    const di = await diBoundsFromXml(modelId);
    // EMPTY_GROUP: bounds DI originais preservados
    expect(di.get("GRP_EMPTY")).toMatchObject({
      x: beforeEmpty.x,
      y: beforeEmpty.y,
      width: beforeEmpty.width,
      height: beforeEmpty.height,
    });
    // PARTIAL_OVERLAP: GRP_PARTIAL não tinha membros → preserva DI
    expect(di.get("GRP_PARTIAL")).toMatchObject({
      x: beforePartial.x,
      y: beforePartial.y,
      width: beforePartial.width,
      height: beforePartial.height,
    });
  });
});
