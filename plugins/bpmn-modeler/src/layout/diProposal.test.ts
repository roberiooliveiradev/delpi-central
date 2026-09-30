// @vitest-environment jsdom
/**
 * snapshotFromXml — containers não-nó (process/collaboration/laneSet)
 * repassam parentId; nós internos a um processo simples não podem
 * ficar órfãos (regressão: grafo ELK vazio → canvas em branco).
 */
import { describe, expect, it } from "vitest";

import { buildElkGraph } from "./elkGraph";
import { hasBpmnDi, planeElementFor, snapshotFromXml } from "./diProposal";

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

  it("hasBpmnDi/planeElementFor respeitam o artefato", () => {
    expect(hasBpmnDi(SIMPLE)).toBe(false);
    expect(planeElementFor(SIMPLE)).toBe("P1");
    expect(hasBpmnDi(SIMPLE.replace("</bpmn:definitions>",
      '<bpmndi:BPMNDiagram id="d1"/></bpmn:definitions>'))).toBe(true);
  });
});
