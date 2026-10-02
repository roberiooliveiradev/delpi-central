// @vitest-environment jsdom
/**
 * snapshotFromXml — containers não-nó (process/collaboration/laneSet)
 * repassam parentId; nós internos a um processo simples não podem
 * ficar órfãos (regressão: grafo ELK vazio → canvas em branco).
 */
import { describe, expect, it } from "vitest";

import { buildElkGraph } from "./elkGraph";
import {
  buildDiOps,
  hasBpmnDi,
  planeElementFor,
  snapshotFromXml,
} from "./diProposal";

const HEAD =
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ' +
  'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" ' +
  'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" ' +
  'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" ' +
  'id="defs" targetNamespace="urn:t">';

const SIMPLE =
  HEAD +
  '<bpmn:process id="P1" isExecutable="false">' +
  '<bpmn:startEvent id="S1"/><bpmn:task id="T1"/>' +
  '<bpmn:sequenceFlow id="F1" sourceRef="S1" targetRef="T1"/>' +
  "</bpmn:process></bpmn:definitions>";

const NESTED =
  HEAD +
  '<bpmn:process id="P1">' +
  '<bpmn:subProcess id="SUB1"><bpmn:task id="INNER"/></bpmn:subProcess>' +
  '<bpmn:task id="T1"/>' +
  "</bpmn:process></bpmn:definitions>";

const LANES =
  HEAD +
  '<bpmn:process id="P1"><bpmn:laneSet id="LS1">' +
  '<bpmn:lane id="L1"><bpmn:flowNodeRef>T1</bpmn:flowNodeRef></bpmn:lane>' +
  "</bpmn:laneSet><bpmn:task id=\"T1\"/></bpmn:process></bpmn:definitions>";

describe("snapshotFromXml", () => {
  it("promove filhos de <process> para a raiz (sem órfãos)", () => {
    const s = snapshotFromXml(SIMPLE);
    expect(s.nodes.map((n) => n.id).sort()).toEqual(["S1", "T1"]);
    expect(s.nodes.every((n) => n.parentId === undefined)).toBe(true);
    expect(s.edges).toEqual([
      { id: "F1", sourceId: "S1", targetId: "T1" },
    ]);
    const graph = buildElkGraph(s);
    expect(graph.children?.map((c) => c.id).sort()).toEqual(["S1", "T1"]);
    expect(graph.edges?.map((e) => e.id)).toEqual(["F1"]);
  });

  it("subProcess é nó e seus filhos ficam aninhados", () => {
    const s = snapshotFromXml(NESTED);
    const sub = s.nodes.find((n) => n.id === "SUB1");
    const inner = s.nodes.find((n) => n.id === "INNER");
    expect(sub?.parentId).toBeUndefined();
    expect(inner?.parentId).toBe("SUB1");
    const graph = buildElkGraph(s);
    const subNode = graph.children?.find((c) => c.id === "SUB1");
    expect(subNode?.children?.[0]?.id).toBe("INNER");
  });

  it("laneSet repassa parentId; lane é nó", () => {
    const s = snapshotFromXml(LANES);
    expect(s.nodes.find((n) => n.id === "L1")?.parentId).toBeUndefined();
    expect(s.nodes.find((n) => n.id === "T1")?.parentId).toBeUndefined();
  });

  it("captura bounds DI vigentes no snapshot (fonte do tamanho)", () => {
    const xml =
      SIMPLE.replace("</bpmn:definitions>",
        '<bpmndi:BPMNDiagram id="d1"><bpmndi:BPMNPlane id="p1" bpmnElement="P1">' +
        '<bpmndi:BPMNShape id="s_T1" bpmnElement="T1">' +
        '<dc:Bounds x="50" y="60" width="140" height="90"/></bpmndi:BPMNShape>' +
        '<bpmndi:BPMNShape id="s_S1" bpmnElement="S1">' +
        '<dc:Bounds x="10" y="10" width="36" height="36"/></bpmndi:BPMNShape>' +
        "</bpmndi:BPMNPlane></bpmndi:BPMNDiagram></bpmn:definitions>");
    const s = snapshotFromXml(xml);
    expect(s.nodes.find((n) => n.id === "T1")).toMatchObject({
      width: 140,
      height: 90,
    });
    expect(s.nodes.find((n) => n.id === "S1")).toMatchObject({
      width: 36,
      height: 36,
    });
  });

  it("hasBpmnDi/planeElementFor respeitam o artefato", () => {
    expect(hasBpmnDi(SIMPLE)).toBe(false);
    expect(planeElementFor(SIMPLE)).toBe("P1");
    expect(hasBpmnDi(SIMPLE.replace("</bpmn:definitions>",
      '<bpmndi:BPMNDiagram id="d1"/></bpmn:definitions>'))).toBe(true);
  });
});

describe("size preservation policy", () => {
  it("ELK input usa bounds atuais; default vendor só sem DI", () => {
    const s = snapshotFromXml(SIMPLE);
    const g = buildElkGraph(s);
    const t1 = g.children?.find((c) => c.id === "T1");
    expect(t1?.width).toBe(100); // fallback do profile sem DI

    const sized = {
      nodes: s.nodes.map((n) =>
        n.id === "T1" ? { ...n, width: 160, height: 120 } : n,
      ),
      edges: s.edges,
    };
    const g2 = buildElkGraph(sized);
    expect(g2.children?.find((c) => c.id === "T1")?.width).toBe(160);
    expect(g2.children?.find((c) => c.id === "T1")?.height).toBe(120);
  });

  it("buildDiOps preserva w/h de não-container mesmo se ELK mudou", () => {
    const snapshot = {
      nodes: [
        { id: "T1", type: "bpmn:task", width: 160, height: 120 },
        { id: "S1", type: "bpmn:startEvent", width: 36, height: 36 },
        { id: "SUB1", type: "bpmn:subProcess", width: 350, height: 200 },
        { id: "POOL", type: "bpmn:participant", isParticipant: true, width: 700, height: 300 },
      ],
      edges: [],
    };
    const laidOut = {
      id: "__root__",
      children: [
        { id: "T1", x: 300, y: 200, width: 100, height: 80 }, // ELK "encolheu"
        { id: "S1", x: 0, y: 0, width: 50, height: 50 },
        { id: "SUB1", x: 0, y: 300, width: 400, height: 260 }, // container pode
        { id: "POOL", x: 0, y: 600, width: 800, height: 400 },
      ],
    };
    const ops = buildDiOps(laidOut, snapshot);
    const byId = new Map(ops.map((o) => [o.elementId, o.bounds]));

    // SIZE_PRESERVED: x/y novos do ELK, w/h vigentes
    expect(byId.get("T1")).toMatchObject({ x: 300, y: 200, width: 160, height: 120 });
    expect(byId.get("S1")).toMatchObject({ x: 0, y: 0, width: 36, height: 36 });
    // LAYOUT_MAY_RESIZE: containers aceitam o tamanho do ELK
    expect(byId.get("SUB1")).toMatchObject({ width: 400, height: 260 });
    expect(byId.get("POOL")).toMatchObject({ width: 800, height: 400 });
  });

  it("nó sem DI vigente aceita o tamanho ELK (primeiro layout)", () => {
    const snapshot = { nodes: [{ id: "T1", type: "bpmn:task" }], edges: [] };
    const laidOut = {
      id: "__root__",
      children: [{ id: "T1", x: 10, y: 20, width: 100, height: 80 }],
    };
    const ops = buildDiOps(laidOut, snapshot);
    expect(ops[0].bounds).toMatchObject({ width: 100, height: 80 });
  });
});
