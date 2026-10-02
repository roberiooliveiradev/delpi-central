import { test, expect, importModelViaApi, modelUrl, apiToken } from "../helpers";
import type { Page } from "@playwright/test";
import { request } from "@playwright/test";
import path from "node:path";
import fs from "node:fs";

const SHOTS = path.resolve(import.meta.dirname, "../../.tmp-shots");
async function shot(page: Page, name: string) {
  fs.mkdirSync(SHOTS, { recursive: true });
  await page.screenshot({ path: path.join(SHOTS, `${name}.png`) });
}

/**
 * E2E-48 — auto-layout: labels externas (BPMNLabel) acompanham o owner.
 *
 * Regressão corrigida: shape movido pelo ELK mas a BPMNLabel ficava na
 * posição anterior (o pipeline nunca tocava di.label.bounds nem o
 * label element). Política:
 *   shape-attached label → traduz pelo delta do owner (offset preservado)
 *   edge-attached label  → traduz pelo delta do ponto médio da polyline
 *   label sem BPMNLabel explícito → label element move pelo delta;
 *     vendor reauto-posiciona no reload (canonical continua limpo).
 */

const XML =
  '<?xml version="1.0" encoding="UTF-8"?>' +
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ' +
  'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" ' +
  'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" ' +
  'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" ' +
  'id="defs_lbl" targetNamespace="urn:lbl">' +
  '<bpmn:process id="P1" isExecutable="false">' +
  '<bpmn:startEvent id="S1" name="Início"/>' +
  '<bpmn:task id="T1" name="Tarefa"/>' +
  '<bpmn:exclusiveGateway id="G1" name="Decisão"/>' +
  '<bpmn:task id="T2"/>' +
  '<bpmn:endEvent id="E1" name="Fim"/>' +
  '<bpmn:dataObjectReference id="DO1" name="Doc"/>' +
  '<bpmn:dataStoreReference id="DS1" name="Estoque"/>' +
  '<bpmn:sequenceFlow id="F1" sourceRef="S1" targetRef="T1"/>' +
  '<bpmn:sequenceFlow id="F2" sourceRef="T1" targetRef="G1"/>' +
  '<bpmn:sequenceFlow id="F3" sourceRef="G1" targetRef="T2"/>' +
  '<bpmn:sequenceFlow id="F4" sourceRef="T2" targetRef="E1" name="Aprovado"/>' +
  "</bpmn:process>" +
  '<bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL1" bpmnElement="P1">' +
  '<bpmndi:BPMNShape id="sp_S1" bpmnElement="S1"><dc:Bounds x="100" y="100" width="36" height="36"/>' +
  '<bpmndi:BPMNLabel><dc:Bounds x="90" y="140" width="56" height="14"/></bpmndi:BPMNLabel></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_T1" bpmnElement="T1"><dc:Bounds x="200" y="78" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_G1" bpmnElement="G1"><dc:Bounds x="350" y="93" width="50" height="50"/>' +
  '<bpmndi:BPMNLabel><dc:Bounds x="343" y="150" width="64" height="14"/></bpmndi:BPMNLabel></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_T2" bpmnElement="T2"><dc:Bounds x="450" y="78" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_E1" bpmnElement="E1"><dc:Bounds x="600" y="100" width="36" height="36"/>' +
  '<bpmndi:BPMNLabel><dc:Bounds x="602" y="140" width="28" height="14"/></bpmndi:BPMNLabel></bpmndi:BPMNShape>' +
  // Doc com offset custom (à direita do shape — não centralizado abaixo)
  '<bpmndi:BPMNShape id="sp_DO1" bpmnElement="DO1"><dc:Bounds x="200" y="220" width="36" height="50"/>' +
  '<bpmndi:BPMNLabel><dc:Bounds x="248" y="236" width="30" height="14"/></bpmndi:BPMNLabel></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sp_DS1" bpmnElement="DS1"><dc:Bounds x="400" y="220" width="50" height="50"/>' +
  '<bpmndi:BPMNLabel><dc:Bounds x="393" y="276" width="64" height="14"/></bpmndi:BPMNLabel></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNEdge id="e_F1" bpmnElement="F1"><di:waypoint x="136" y="118"/><di:waypoint x="200" y="118"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="e_F2" bpmnElement="F2"><di:waypoint x="300" y="118"/><di:waypoint x="350" y="118"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="e_F3" bpmnElement="F3"><di:waypoint x="400" y="118"/><di:waypoint x="450" y="118"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="e_F4" bpmnElement="F4"><di:waypoint x="550" y="118"/><di:waypoint x="600" y="118"/>' +
  '<bpmndi:BPMNLabel><dc:Bounds x="545" y="140" width="60" height="14"/></bpmndi:BPMNLabel></bpmndi:BPMNEdge>' +
  "</bpmndi:BPMNPlane></bpmndi:BPMNDiagram></bpmn:definitions>";

type Bounds = { x: number; y: number; width: number; height: number };

async function openEditor(page: Page): Promise<string> {
  const modelId = await importModelViaApi("editor", "E2E-LayoutLabels", XML);
  await page.goto(modelUrl(modelId));
  await expect(
    page.locator('.djs-element[data-element-id="T1"]'),
  ).toBeVisible({ timeout: 20_000 });
  await page.waitForTimeout(600);
  return modelId;
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

/** { ownerId → { shape/edge bounds, labelBounds? } } do XML DI. */
function parseDi(xml: string) {
  const out = new Map<string, { owner?: Bounds; label?: Bounds }>();
  const num = (s: string | null | undefined) => Number(s);
  const shapeRe =
    /BPMNShape[^>]*bpmnElement="([^"]+)"[^>]*>\s*<dc:Bounds x="([-\d.]+)" y="([-\d.]+)" width="([-\d.]+)" height="([-\d.]+)"\s*\/>(?:\s*<bpmndi:BPMNLabel[^>]*>\s*<dc:Bounds x="([-\d.]+)" y="([-\d.]+)" width="([-\d.]+)" height="([-\d.]+)"\s*\/>)?/g;
  let m: RegExpExecArray | null;
  while ((m = shapeRe.exec(xml))) {
    out.set(m[1], {
      owner: { x: num(m[2]), y: num(m[3]), width: num(m[4]), height: num(m[5]) },
      label: m[6] !== undefined
        ? { x: num(m[6]), y: num(m[7]), width: num(m[8]), height: num(m[9]) }
        : undefined,
    });
  }
  const edgeRe =
    /BPMNEdge[^>]*bpmnElement="([^"]+)"[^>]*>([\s\S]*?)<\/bpmndi:BPMNEdge>/g;
  while ((m = edgeRe.exec(xml))) {
    const body = m[2];
    const pts = [...body.matchAll(/waypoint x="([-\d.]+)" y="([-\d.]+)"/g)].map(
      (w) => ({ x: +w[1], y: +w[2] }),
    );
    const lb = /BPMNLabel[^>]*>\s*<dc:Bounds x="([-\d.]+)" y="([-\d.]+)" width="([-\d.]+)" height="([-\d.]+)"\s*\/>/.exec(
      body,
    );
    const first = pts[0];
    out.set(m[1], {
      owner: first
        ? { x: first.x, y: first.y, width: 0, height: 0 }
        : undefined,
      label: lb
        ? { x: +lb[1], y: +lb[2], width: +lb[3], height: +lb[4] }
        : undefined,
    });
    // pontos completos para o cálculo do mid
    (out.get(m[1]) as { pts?: { x: number; y: number }[] }).pts = pts;
  }
  return out;
}

function mid(pts: { x: number; y: number }[]) {
  const first = pts[0];
  const last = pts[pts.length - 1];
  let total = 0;
  const segs: number[] = [];
  for (let i = 1; i < pts.length; i++) {
    const l = Math.hypot(pts[i].x - pts[i - 1].x, pts[i].y - pts[i - 1].y);
    segs.push(l);
    total += l;
  }
  let rest = total / 2;
  for (let i = 0; i < segs.length; i++) {
    if (rest <= segs[i] || i === segs.length - 1) {
      const t = segs[i] === 0 ? 0 : rest / segs[i];
      return {
        x: pts[i].x + (pts[i + 1].x - pts[i].x) * t,
        y: pts[i].y + (pts[i + 1].y - pts[i].y) * t,
      };
    }
    rest -= segs[i];
  }
  return last ?? first;
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

const NAMED = ["S1", "G1", "E1", "DO1", "DS1"]; // shapes c/ BPMNLabel

test.describe("E2E-48 — label geometry segue o owner", () => {
  test.use({ actor: "editor", viewport: { width: 1440, height: 900 } });

  test("LABEL-01: labels de shape seguem owner pelo delta (offset+dims)", async ({
    page,
  }) => {
    const modelId = await openEditor(page);
    const before = parseDi(await workingCopyXml(modelId));
    await shot(page, "layout-labels-before");

    await organize(page, true);
    await save(page);
    await shot(page, "layout-labels-after-accept");
    const after = parseDi(await workingCopyXml(modelId));

    for (const id of NAMED) {
      const b = before.get(id)!;
      const a = after.get(id)!;
      expect(b.label, `${id} tinha BPMNLabel`).toBeTruthy();
      expect(a.label, `${id} label persistida`).toBeTruthy();
      // offset owner→label preservado exatamente
      expect(a.label!.x - a.owner!.x, `${id} offset x`).toBeCloseTo(
        b.label!.x - b.owner!.x,
        0,
      );
      expect(a.label!.y - a.owner!.y, `${id} offset y`).toBeCloseTo(
        b.label!.y - b.owner!.y,
        0,
      );
      // dims da label preservadas
      expect(a.label!.width).toBeCloseTo(b.label!.width, 0);
      expect(a.label!.height).toBeCloseTo(b.label!.height, 0);
    }
  });

  test("LABEL-02: label de flow acompanha o mid da nova polyline", async ({
    page,
  }) => {
    const modelId = await openEditor(page);
    const before = parseDi(await workingCopyXml(modelId));
    const bF4 = before.get("F4")! as {
      label: Bounds;
      pts: { x: number; y: number }[];
    };
    expect(bF4.label).toBeTruthy();

    await organize(page, true);
    await save(page);
    const after = parseDi(await workingCopyXml(modelId));
    const aF4 = after.get("F4")! as {
      label: Bounds;
      pts: { x: number; y: number }[];
    };

    const dOld = mid(bF4.pts);
    const dNew = mid(aF4.pts);
    // label moveu junto com o mid da edge (±2px de arredondamento)
    expect(Math.abs(aF4.label.x - (bF4.label.x + (dNew.x - dOld.x)))).toBeLessThanOrEqual(2);
    expect(Math.abs(aF4.label.y - (bF4.label.y + (dNew.y - dOld.y)))).toBeLessThanOrEqual(2);
    // label continua próxima da edge, não ficou na posição antiga
    expect(
      Math.abs(aF4.label.x + aF4.label.width / 2 - dNew.x),
    ).toBeLessThan(150);
  });

  test("LABEL-03: cancel não altera labels nem canonical", async ({ page }) => {
    const modelId = await openEditor(page);
    const xmlA = await workingCopyXml(modelId);
    await organize(page, false);
    const xmlB = await workingCopyXml(modelId);
    expect(xmlB).toBe(xmlA); // preview é transient — canonical intacto
  });

  test("LABEL-04: undo/redo restaura label junto do shape", async ({
    page,
  }) => {
    const modelId = await openEditor(page);
    const before = parseDi(await workingCopyXml(modelId));
    // posição DOM da label antes do layout (vendor recentra no import)
    const labelPos = async (id: string) => {
      const tf = await page
        .locator(`.djs-element[data-element-id="${id}_label"]`)
        .getAttribute("transform");
      const p = /(?:translate|matrix)\(([^)]*)\)/.exec(tf ?? "")?.[1]
        ?.split(/[ ,]+/)
        .filter(Boolean)
        .map(Number) ?? [NaN];
      return { x: p.length >= 6 ? p[4] : p[0], y: p.length >= 6 ? p[5] : p[1] };
    };
    const gBefore = await labelPos("G1");

    await organize(page, true);
    await save(page);
    const accepted = parseDi(await workingCopyXml(modelId));
    // DOM: label moveu junto (posição diferente da original)
    const gAccepted = await labelPos("G1");
    expect(
      gAccepted.x !== gBefore.x || gAccepted.y !== gBefore.y,
    ).toBe(true);

    await page.locator('button[aria-label="Desfazer"]').click();
    await page.waitForTimeout(300);
    const gUndo = await labelPos("G1");
    expect(gUndo.x).toBeCloseTo(gBefore.x, 0);
    expect(gUndo.y).toBeCloseTo(gBefore.y, 0);

    await page.locator('button[aria-label="Refazer"]').click();
    await page.waitForTimeout(300);
    const gRedo = await labelPos("G1");
    expect(gRedo.x).toBeCloseTo(gAccepted.x, 0);
    expect(gRedo.y).toBeCloseTo(gAccepted.y, 0);
    void accepted;
    void modelId;
  });

  test("LABEL-05: reload mantém label associada", async ({ page }) => {
    const modelId = await openEditor(page);
    await organize(page, true);
    await save(page);
    const di = parseDi(await workingCopyXml(modelId));
    await page.reload();
    await expect(
      page.locator('.djs-element[data-element-id="DO1"]'),
    ).toBeVisible({ timeout: 20_000 });
    // label renderizada como elemento irmão *_label próxima ao owner
    const lbl = page.locator('.djs-element[data-element-id="DO1_label"]');
    await expect(lbl).toBeAttached();
    const owner = di.get("DO1")!;
    const lb = di.get("DO1")!.label!;
    expect(lb.x - owner.owner!.x).toBeCloseTo(48, 0); // offset custom +48
  });
});
