import { describe, expect, it } from "vitest";

import { applySwimlaneBpmnTemplate, createLaneId, createNodeId, type FlowchartV1 } from "../types/diagram";
import { autoLayoutFlowchart, normalizeLanes, removeLane } from "./diagramSwimlanes";

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
