import { describe, expect, it } from "vitest";

import { applySwimlaneBpmnTemplate, createLaneId, createNodeId, type FlowchartV1 } from "../types/diagram";
import {
  autoLayoutFlowchart,
  fitLaneHeightsToContent,
  laneIndexFromDragY,
  nextPaletteNodePosition,
  normalizeLanes,
  removeLane,
  reorderLanes,
  requiredLaneHeight,
} from "./diagramSwimlanes";

describe("autoLayoutFlowchart", () => {
  it("preserva faixas do template BPMN após auto-layout", () => {
    const template = applySwimlaneBpmnTemplate();
    const lanes = normalizeLanes(template.lanes);
    const comercialId = lanes[0]?.id;
    const engenhariaId = lanes[1]?.id;

    const laidOut = autoLayoutFlowchart(template);

    const comercialNodes = laidOut.nodes.filter((node) => node.lane_id === comercialId);
    const engenhariaNodes = laidOut.nodes.filter((node) => node.lane_id === engenhariaId);

    expect(comercialNodes.length).toBeGreaterThan(0);
    expect(engenhariaNodes.length).toBeGreaterThan(0);

    for (const node of comercialNodes) {
      expect(node.lane_id).toBe(comercialId);
    }
    for (const node of engenhariaNodes) {
      expect(node.lane_id).toBe(engenhariaId);
    }

    const solicitar = laidOut.nodes.find((node) =>
      node.label.includes("Solicitar informações faltantes")
    );
    expect(solicitar?.lane_id).toBe(comercialId);

    const ranksById = new Map(
      laidOut.nodes.map((node) => [node.id, node.position.x] as const)
    );
    const start = laidOut.nodes.find((node) => node.type === "start");
    const crm = laidOut.nodes.find((node) => node.label.includes("Registrar oportunidade"));
    expect(start).toBeTruthy();
    expect(crm).toBeTruthy();
    expect(ranksById.get(start!.id)!).toBeLessThan(ranksById.get(crm!.id)!);
  });

  it("expande faixas quando o layout vertical excede altura fixa", () => {
    const laneA = createLaneId();
    const nodeA = createNodeId("a");
    const nodeB = createNodeId("b");
    const flowchart: FlowchartV1 = {
      format: "flowchart_v1",
      format_version: 1,
      lanes: [{ id: laneA, label: "Comercial", height: 168, order: 0 }],
      nodes: [
        {
          id: nodeA,
          type: "start",
          label: "Início A",
          position: { x: 200, y: 40 },
          lane_id: laneA,
        },
        {
          id: nodeB,
          type: "start",
          label: "Início B",
          position: { x: 420, y: 40 },
          lane_id: laneA,
        },
      ],
      edges: [],
    };

    const laidOut = autoLayoutFlowchart(flowchart);
    const laneAHeight = laidOut.lanes?.find((lane) => lane.id === laneA)?.height ?? 0;

    expect(laneAHeight).toBeGreaterThan(168);

    const ys = laidOut.nodes.map((node) => node.position.y);
    expect(Math.max(...ys) - Math.min(...ys)).toBeGreaterThan(48);
  });
});

describe("fitLaneHeightsToContent", () => {
  it("aumenta altura da faixa e desloca faixas inferiores", () => {
    const laneA = createLaneId();
    const laneB = createLaneId();
    const nodeA = createNodeId("a");
    const nodeB = createNodeId("b");
    const flowchart: FlowchartV1 = {
      format: "flowchart_v1",
      format_version: 1,
      lanes: [
        { id: laneA, label: "Topo", height: 168, order: 0 },
        { id: laneB, label: "Baixo", height: 168, order: 1 },
      ],
      nodes: [
        {
          id: nodeA,
          type: "process",
          label: "Alto",
          position: { x: 220, y: 140 },
          lane_id: laneA,
        },
        {
          id: nodeB,
          type: "process",
          label: "Baixo",
          position: { x: 220, y: 190 },
          lane_id: laneB,
        },
      ],
      edges: [],
    };

    const fitted = fitLaneHeightsToContent(flowchart);
    const laneAHeight = fitted.lanes?.find((lane) => lane.id === laneA)?.height ?? 0;
    const nodeBAfter = fitted.nodes.find((node) => node.id === nodeB);

    expect(laneAHeight).toBeGreaterThan(168);
    expect(nodeBAfter?.position.y).toBeGreaterThan(190);
  });
});

describe("requiredLaneHeight", () => {
  it("respeita padding mínimo mesmo sem nós", () => {
    expect(requiredLaneHeight([], 0)).toBe(168);
  });
});

describe("removeLane", () => {
  it("remove a última faixa e limpa swimlanes do diagrama", () => {
    const laneId = createLaneId();
    const flowchart: FlowchartV1 = {
      format: "flowchart_v1",
      format_version: 1,
      lanes: [{ id: laneId, label: "Comercial", height: 168, order: 0 }],
      nodes: [
        {
          id: createNodeId("sta"),
          type: "start",
          label: "Início",
          position: { x: 200, y: 120 },
          lane_id: laneId,
        },
      ],
      edges: [],
    };

    const next = removeLane(flowchart, laneId);

    expect(next.lanes).toBeUndefined();
    expect(next.nodes[0]?.lane_id).toBeUndefined();
  });
});

describe("reorderLanes", () => {
  it("reordena faixas ao arrastar verticalmente", () => {
    const laneA = createLaneId();
    const laneB = createLaneId();
    const flowchart: FlowchartV1 = {
      format: "flowchart_v1",
      format_version: 1,
      lanes: [
        { id: laneA, label: "Comercial", height: 168, order: 0 },
        { id: laneB, label: "Engenharia", height: 168, order: 1 },
      ],
      nodes: [
        {
          id: createNodeId("sta"),
          type: "start",
          label: "Início",
          position: { x: 200, y: 84 },
          lane_id: laneA,
        },
        {
          id: createNodeId("proc"),
          type: "process",
          label: "Validar",
          position: { x: 420, y: 252 },
          lane_id: laneB,
        },
      ],
      edges: [],
    };

    const targetIndex = laneIndexFromDragY(normalizeLanes(flowchart.lanes), laneB, 40);
    expect(targetIndex).toBe(0);

    const next = reorderLanes(flowchart, laneB, targetIndex);
    expect(next.lanes?.map((lane) => lane.id)).toEqual([laneB, laneA]);
    expect(next.nodes.find((node) => node.label === "Validar")?.lane_id).toBe(laneB);
  });
});

describe("nextPaletteNodePosition", () => {
  it("distribui novos nós em grade sem sobrepor", () => {
    const first = nextPaletteNodePosition(0);
    const second = nextPaletteNodePosition(1);
    const fifth = nextPaletteNodePosition(4);

    expect(second.x).toBeGreaterThan(first.x);
    expect(fifth.y).toBeGreaterThan(first.y);
  });
});
