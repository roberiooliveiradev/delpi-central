// @vitest-environment jsdom
/**
 * G9-LAYOUT-1 §46 — pipeline completo ponta a ponta com ELK real
 * (main-thread bundled — o Worker path do layoutEngine é o mesmo algoritmo
 * e grafo; aqui provamos a GEOMETRIA, não o transporte):
 *
 *   snapshotFromXml → applyTextFitSizing → buildElkGraph → ELK
 *   → buildDiOps → assertContained em TODA a hierarquia
 *
 * Fixture espelha a topologia PROC-0067 (participant + 5 lanes + tasks
 * com nomes longos do print real).
 */
import { describe, expect, it } from "vitest";
import ELK from "elkjs/lib/elk.bundled.js";

import { buildElkGraph, type LayoutNode } from "./elkGraph";
import { containerPadFor } from "./layoutProfile";
import {
  applyTextFitSizing,
  buildDiOps,
  snapshotFromXml,
  type DiLayoutOp,
} from "./diProposal";

const HEAD =
  '<?xml version="1.0" encoding="UTF-8"?>' +
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ' +
  'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" ' +
  'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" ' +
  'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" ' +
  'id="defs" targetNamespace="urn:t">';

/** PROC-0067-like: pool com 5 lanes, fluxo com tarefas de nome longo
 *  progredindo entre lanes (cross-lane edges). */
const PROC67 = () =>
  HEAD +
  '<bpmn:collaboration id="C1"><bpmn:participant id="POOL" name="Gerenciamento de Rotina" processRef="P1"/></bpmn:collaboration>' +
  '<bpmn:process id="P1"><bpmn:laneSet>' +
  '<bpmn:lane id="L_COLETA" name="Coleta"><bpmn:flowNodeRef>S1</bpmn:flowNodeRef><bpmn:flowNodeRef>T_REG</bpmn:flowNodeRef></bpmn:lane>' +
  '<bpmn:lane id="L_INTEG" name="Integração"><bpmn:flowNodeRef>T_API</bpmn:flowNodeRef><bpmn:flowNodeRef>T_TRAT</bpmn:flowNodeRef></bpmn:lane>' +
  '<bpmn:lane id="L_TV" name="TV"><bpmn:flowNodeRef>T_TV</bpmn:flowNodeRef></bpmn:lane>' +
  '<bpmn:lane id="L_GEST" name="Gestão"><bpmn:flowNodeRef>T_ACOMP</bpmn:flowNodeRef><bpmn:flowNodeRef>T_DESV</bpmn:flowNodeRef></bpmn:lane>' +
  '<bpmn:lane id="L_DIR" name="Direção"><bpmn:flowNodeRef>T_DEC</bpmn:flowNodeRef><bpmn:flowNodeRef>E1</bpmn:flowNodeRef></bpmn:lane>' +
  "</bpmn:laneSet>" +
  '<bpmn:startEvent id="S1" name="Início"/>' +
  '<bpmn:task id="T_REG" name="Dados são registrados nas bases corporativas"/>' +
  '<bpmn:task id="T_API" name="APIs consultam as bases de dados"/>' +
  '<bpmn:task id="T_TRAT" name="Dados são tratados e indicadores calculados automaticamente"/>' +
  '<bpmn:task id="T_TV" name="Painéis TV é atualizado automaticamente"/>' +
  '<bpmn:task id="T_ACOMP" name="Acompanhar indicadores"/>' +
  '<bpmn:task id="T_DESV" name="Identificar desvios"/>' +
  '<bpmn:task id="T_DEC" name="Analisar e apoiar tomada de decisão"/>' +
  '<bpmn:endEvent id="E1" name="Fim"/>' +
  '<bpmn:sequenceFlow id="F1" sourceRef="S1" targetRef="T_REG"/>' +
  '<bpmn:sequenceFlow id="F2" sourceRef="T_REG" targetRef="T_API"/>' +
  '<bpmn:sequenceFlow id="F3" sourceRef="T_API" targetRef="T_TRAT"/>' +
  '<bpmn:sequenceFlow id="F4" sourceRef="T_TRAT" targetRef="T_TV"/>' +
  '<bpmn:sequenceFlow id="F5" sourceRef="T_TV" targetRef="T_ACOMP"/>' +
  '<bpmn:sequenceFlow id="F6" sourceRef="T_ACOMP" targetRef="T_DESV"/>' +
  '<bpmn:sequenceFlow id="F7" sourceRef="T_DESV" targetRef="T_DEC"/>' +
  '<bpmn:sequenceFlow id="F8" sourceRef="T_DEC" targetRef="E1"/>' +
  "</bpmn:process>" +
  '<bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL1" bpmnElement="C1">' +
  '<bpmndi:BPMNShape id="sh_POOL" bpmnElement="POOL" isHorizontal="true"><dc:Bounds x="100" y="100" width="600" height="250"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sh_L1" bpmnElement="L_COLETA" isHorizontal="true"><dc:Bounds x="130" y="110" width="570" height="120"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sh_L2" bpmnElement="L_INTEG" isHorizontal="true"><dc:Bounds x="130" y="230" width="570" height="120"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sh_L3" bpmnElement="L_TV" isHorizontal="true"><dc:Bounds x="130" y="350" width="570" height="120"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sh_L4" bpmnElement="L_GEST" isHorizontal="true"><dc:Bounds x="130" y="470" width="570" height="120"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sh_L5" bpmnElement="L_DIR" isHorizontal="true"><dc:Bounds x="130" y="590" width="570" height="120"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sh_S1" bpmnElement="S1"><dc:Bounds x="180" y="150" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sh_TREG" bpmnElement="T_REG"><dc:Bounds x="260" y="130" width="180" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sh_TAPI" bpmnElement="T_API"><dc:Bounds x="240" y="250" width="160" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sh_TTRAT" bpmnElement="T_TRAT"><dc:Bounds x="440" y="250" width="220" height="90"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sh_TTV" bpmnElement="T_TV"><dc:Bounds x="300" y="370" width="190" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sh_TACOMP" bpmnElement="T_ACOMP"><dc:Bounds x="260" y="490" width="140" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sh_TDESV" bpmnElement="T_DESV"><dc:Bounds x="430" y="490" width="140" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sh_TDEC" bpmnElement="T_DEC"><dc:Bounds x="280" y="610" width="230" height="90"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sh_E1" bpmnElement="E1"><dc:Bounds x="560" y="640" width="36" height="36"/></bpmndi:BPMNShape>' +
  "</bpmndi:BPMNPlane></bpmndi:BPMNDiagram></bpmn:definitions>";

const EPS = 0.01;

function assertContained(
  child: { x: number; y: number; width: number; height: number },
  container: { x: number; y: number; width: number; height: number },
  pad: { left: number; top: number; right: number; bottom: number },
  label: string,
) {
  const msg = `${label}: ${JSON.stringify({ child, container, pad })}`;
  expect(child.x, msg).toBeGreaterThanOrEqual(container.x + pad.left - EPS);
  expect(child.y, msg).toBeGreaterThanOrEqual(container.y + pad.top - EPS);
  expect(child.x + child.width, msg).toBeLessThanOrEqual(
    container.x + container.width - pad.right + EPS,
  );
  expect(child.y + child.height, msg).toBeLessThanOrEqual(
    container.y + container.height - pad.bottom + EPS,
  );
}

describe("pipeline completo — PROC-0067-like (ELK real)", () => {
  it("zero overflow: todos os filhos contidos em lane/pool", async () => {
    const snapshot = applyTextFitSizing(snapshotFromXml(PROC67()));
    const graph = buildElkGraph(snapshot);
    const elk = new ELK();
    const laidOut = await elk.layout(graph);
    const ops = buildDiOps(laidOut, snapshot);

    const bounds = new Map<string, DiLayoutOp["bounds"] & object>();
    for (const op of ops) {
      if (op.bounds) bounds.set(op.elementId, op.bounds);
    }
    const byId = new Map(snapshot.nodes.map((n) => [n.id, n]));
    const lanePad = containerPadFor("lane");
    const poolPad = containerPadFor("participant");

    let violations = 0;
    const laneIds: string[] = [];
    for (const node of snapshot.nodes) {
      const parent = node.parentId ? byId.get(node.parentId) : undefined;
      if (!parent) continue;
      const child = bounds.get(node.id);
      const container = bounds.get(parent.id);
      if (!child || !container) continue;
      const pad = parent.isParticipant
        ? poolPad
        : parent.isLane
          ? lanePad
          : containerPadFor("subprocess");
      try {
        assertContained(child, container, pad, `${node.id} ⊂ ${parent.id}`);
      } catch {
        violations += 1;
      }
      if (node.isLane) laneIds.push(node.id);
    }

    // §33: as 5 lanes dividem mesma largura e empilham flush
    const lanes = laneIds.map((id) => bounds.get(id)!);
    expect(lanes.length).toBe(5);
    for (const l of lanes) {
      expect(l.x).toBeCloseTo(lanes[0].x, 4);
      expect(l.width).toBeCloseTo(lanes[0].width, 4);
    }
    const sorted = [...lanes].sort((a, b) => a.y - b.y);
    for (let i = 1; i < sorted.length; i++) {
      expect(sorted[i].y).toBeCloseTo(sorted[i - 1].y + sorted[i - 1].height, 4);
    }
    // lanes contidas no participant
    const pool = bounds.get("POOL")!;
    for (const l of lanes) assertContained(l, pool, poolPad, "lane ⊂ POOL");

    expect(violations).toBe(0);
  });

  it("filho crescido pelo text-fit é o bounds proposto (grow-only)", async () => {
    const snapshot = applyTextFitSizing(snapshotFromXml(PROC67()));
    const node = (id: string) =>
      snapshot.nodes.find((n) => n.id === id) as LayoutNode;
    // nome longo → text-fit cresceu acima do default vendor
    expect(node("T_TRAT").width!).toBeGreaterThan(100);
    const graph = buildElkGraph(snapshot);
    const laidOut = await new ELK().layout(graph);
    const ops = buildDiOps(laidOut, snapshot);
    const ttrat = ops.find((o) => o.elementId === "T_TRAT")!.bounds!;
    expect(ttrat.width).toBeGreaterThanOrEqual(200);
    // toda a largura foi absorvida pela lane (child ⊂ lane)
    const linteg = ops.find((o) => o.elementId === "L_INTEG")!.bounds!;
    const pad = containerPadFor("lane");
    assertContained(ttrat, linteg, pad, "T_TRAT ⊂ L_INTEG");
  });
});
