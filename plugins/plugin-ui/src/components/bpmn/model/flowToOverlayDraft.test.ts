import { describe, expect, it } from "vitest";
import {
  emptyFlowchart,
  flowToOverlayDraft,
  type FlowchartV1,
} from "./diagram";

function flow(partial: Partial<FlowchartV1> & Pick<FlowchartV1, "nodes" | "edges">): FlowchartV1 {
  return {
    format: "flowchart_v1",
    format_version: 1,
    ...partial,
  };
}

describe("flowToOverlayDraft", () => {
  const base = flow({
    lanes: [{ id: "lane_a", label: "A", height: 168, order: 0 }],
    nodes: [
      { id: "n1", type: "start", label: "Início", position: { x: 0, y: 0 }, lane_id: "lane_a" },
      { id: "n2", type: "process", label: "Atividade", position: { x: 200, y: 0 }, lane_id: "lane_a" },
      { id: "n3", type: "end", label: "Fim", position: { x: 400, y: 0 }, lane_id: "lane_a" },
    ],
    edges: [
      { id: "e1", from: "n1", to: "n2", label: null },
      { id: "e2", from: "n2", to: "n3", label: null },
    ],
  });

  it("grava remoções, extras e lanes — sem overrides órfãos", () => {
    const edited = flow({
      lanes: [
        { id: "lane_a", label: "Coleta", height: 168, order: 0 },
        { id: "lane_b", label: "Gestão", height: 168, order: 1 },
      ],
      nodes: [
        { id: "n1", type: "start", label: "Início", position: { x: 0, y: 0 }, lane_id: "lane_a" },
        {
          id: "pro_novo",
          type: "process",
          label: "Acessar a plataforma",
          position: { x: 200, y: 0 },
          lane_id: "lane_a",
        },
        {
          id: "n_keep_end",
          type: "end",
          label: "Fim",
          position: { x: 400, y: 80 },
          lane_id: "lane_b",
        },
      ],
      edges: [
        { id: "e_new1", from: "n1", to: "pro_novo", label: null },
        { id: "e_new2", from: "pro_novo", to: "n_keep_end", label: null },
      ],
    });

    const overlay = flowToOverlayDraft(base, edited);

    expect(overlay.removed_node_ids).toEqual(expect.arrayContaining(["n2", "n3"]));
    expect(overlay.removed_edge_ids).toEqual(expect.arrayContaining(["e1", "e2"]));
    expect(overlay.extra_nodes?.map((n) => n.id)).toEqual(
      expect.arrayContaining(["pro_novo", "n_keep_end"]),
    );
    expect(overlay.extra_edges?.map((e) => e.id)).toEqual(
      expect.arrayContaining(["e_new1", "e_new2"]),
    );
    expect(overlay.node_overrides?.pro_novo).toBeUndefined();
    expect(overlay.extra_nodes?.find((n) => n.id === "pro_novo")?.highlight).toBe("tobe");
    expect(overlay.lanes?.map((l) => l.id)).toEqual(["lane_a", "lane_b"]);
  });

  it("só override quando nó da base muda label", () => {
    const edited = flow({
      ...base,
      nodes: base.nodes.map((node) =>
        node.id === "n2" ? { ...node, label: "Atividade revisada" } : node,
      ),
    });
    const overlay = flowToOverlayDraft(base, edited);
    expect(overlay.removed_node_ids).toEqual([]);
    expect(overlay.extra_nodes).toEqual([]);
    expect(overlay.node_overrides?.n2?.label).toBe("Atividade revisada");
    expect(overlay.node_overrides?.n2?.highlight).toBe("tobe");
  });

  it("base vazia e edited populado vira só extras", () => {
    const overlay = flowToOverlayDraft(emptyFlowchart(), base);
    expect(overlay.extra_nodes).toHaveLength(3);
    expect(overlay.removed_node_ids).toEqual([]);
  });
});
