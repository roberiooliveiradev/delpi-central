import { describe, expect, it } from "vitest";
import {
  applyDiffHighlightsToRichTree,
  formatDiffSummary,
  mergeRemovedNodesIntoFlowchartForDiff,
  mergeRemovedNodesIntoTreeForDiff,
} from "./diffHighlightDisplay";
import type { DecompositionTreeV1 } from "../types/decomposition";
import type { RichTreeNode } from "../types/richTree";
import type { FlowchartV1 } from "@delpi/plugin-ui/index";

function tree(nodes: DecompositionTreeV1["nodes"]): DecompositionTreeV1 {
  return { format: "decomposition_tree_v1", format_version: 1, nodes };
}

describe("mergeRemovedNodesIntoTreeForDiff", () => {
  const reference = tree([
    {
      id: "pk1",
      level: "processo_chave",
      ordem: 1,
      label: "PK ref",
      parent_id: null,
    },
    {
      id: "t1",
      level: "tarefa",
      ordem: 1,
      label: "Tarefa removida",
      parent_id: "pk1",
    },
    {
      id: "st1",
      level: "sub_tarefa",
      ordem: 1,
      label: "ST removida",
      parent_id: "t1",
    },
    {
      id: "t2",
      level: "tarefa",
      ordem: 2,
      label: "Tarefa mantida",
      parent_id: "pk1",
    },
  ]);

  const current = tree([
    {
      id: "pk1",
      level: "processo_chave",
      ordem: 1,
      label: "PK ref",
      parent_id: null,
    },
    {
      id: "t2",
      level: "tarefa",
      ordem: 1,
      label: "Tarefa mantida",
      parent_id: "pk1",
    },
    {
      id: "t_new",
      level: "tarefa",
      ordem: 2,
      label: "Nova",
      parent_id: "pk1",
    },
  ]);

  it("reinsere nós removidos com highlight removed sob o parent vivo", () => {
    const merged = mergeRemovedNodesIntoTreeForDiff(current, reference, ["t1", "st1"]);
    const byId = new Map(merged.nodes.map((n) => [n.id, n]));
    expect(byId.get("t1")?.highlight).toBe("removed");
    expect(byId.get("t1")?.parent_id).toBe("pk1");
    expect(byId.get("st1")?.highlight).toBe("removed");
    expect(byId.get("st1")?.parent_id).toBe("t1");
    expect(byId.has("t_new")).toBe(true);
  });

  it("sobe o parent até um ancestral presente quando o pai intermediário sumiu sem estar em removed", () => {
    const merged = mergeRemovedNodesIntoTreeForDiff(current, reference, ["st1"]);
    expect(merged.nodes.find((n) => n.id === "st1")?.parent_id).toBe("pk1");
  });

  it("não altera a árvore sem ids removidos", () => {
    expect(mergeRemovedNodesIntoTreeForDiff(current, reference, [])).toBe(current);
    expect(mergeRemovedNodesIntoTreeForDiff(current, null, ["t1"])).toBe(current);
  });
});

describe("applyDiffHighlightsToRichTree + formatDiffSummary", () => {
  it("pinta removed/added/changed", () => {
    const root: RichTreeNode = {
      id: "root",
      label: "root",
      children: [
        { id: "a", label: "a" },
        { id: "b", label: "b" },
        { id: "c", label: "c" },
      ],
    };
    const painted = applyDiffHighlightsToRichTree(root, {
      changed: ["a"],
      added: ["b"],
      removed: ["c"],
    });
    expect(painted?.children?.map((n) => n.highlight)).toEqual(["changed", "tobe", "removed"]);
  });

  it("formatDiffSummary inclui removidos", () => {
    expect(
      formatDiffSummary(
        { changed: ["a"], added: ["b", "c"], removed: ["d", "e", "f"] },
        "1.0.0",
      ),
    ).toBe("vs referência (1.0.0): 1 alterados, 2 novos, 3 removidos.");
  });
});

describe("mergeRemovedNodesIntoFlowchartForDiff", () => {
  function flow(partial: Partial<FlowchartV1> & Pick<FlowchartV1, "nodes" | "edges">): FlowchartV1 {
    return { format: "flowchart_v1", format_version: 1, ...partial };
  }

  it("reinsere nós e arestas removidos com highlight removed", () => {
    const reference = flow({
      lanes: [{ id: "lane_a", label: "A", height: 168 }],
      nodes: [
        { id: "n1", type: "start", label: "Início", position: { x: 0, y: 0 }, lane_id: "lane_a" },
        { id: "n2", type: "process", label: "Removido", position: { x: 200, y: 0 }, lane_id: "lane_a" },
        { id: "n3", type: "end", label: "Fim", position: { x: 400, y: 0 }, lane_id: "lane_a" },
      ],
      edges: [
        { id: "e1", from: "n1", to: "n2", label: null },
        { id: "e2", from: "n2", to: "n3", label: null },
      ],
    });
    const current = flow({
      lanes: [{ id: "lane_a", label: "A", height: 168 }],
      nodes: [
        { id: "n1", type: "start", label: "Início", position: { x: 0, y: 0 }, lane_id: "lane_a" },
        { id: "n3", type: "end", label: "Fim", position: { x: 400, y: 0 }, lane_id: "lane_a" },
      ],
      edges: [{ id: "e_direct", from: "n1", to: "n3", label: null }],
    });

    const merged = mergeRemovedNodesIntoFlowchartForDiff(current, reference, ["n2"]);
    expect(merged.nodes.map((n) => n.id)).toEqual(expect.arrayContaining(["n1", "n2", "n3"]));
    expect(merged.nodes.find((n) => n.id === "n2")?.highlight).toBe("removed");
    expect(merged.edges.map((e) => e.id)).toEqual(
      expect.arrayContaining(["e_direct", "e1", "e2"]),
    );
    // Fantasma deslocado à direita do fluxo atual (não sobrepõe n1/n3 em x=0/400).
    expect(merged.nodes.find((n) => n.id === "n2")!.position.x).toBeGreaterThan(400);
  });

  it("casa faixa da referência por rótulo (ignora prefixo numérico) e alinha Y", () => {
    const reference = flow({
      lanes: [
        { id: "lane_old", label: "Coleta", height: 168, order: 0 },
        { id: "lane_calc", label: "Cálculo e consolidação de indicadores", height: 168, order: 1 },
      ],
      nodes: [
        {
          id: "gone",
          type: "process",
          label: "Removido",
          position: { x: 100, y: 168 + 40 },
          lane_id: "lane_calc",
        },
      ],
      edges: [],
    });
    const current = flow({
      lanes: [
        { id: "lane_new", label: "1 — Coleta", height: 168, order: 0 },
        {
          id: "lane_calc_now",
          label: "3 — Cálculo e consolidação de indicadores",
          height: 168,
          order: 1,
        },
      ],
      nodes: [
        {
          id: "keep",
          type: "process",
          label: "Atual",
          position: { x: 40, y: 40 },
          lane_id: "lane_new",
        },
      ],
      edges: [],
    });
    const merged = mergeRemovedNodesIntoFlowchartForDiff(current, reference, ["gone"]);
    expect(merged.lanes?.map((l) => l.id)).toEqual(["lane_new", "lane_calc_now"]);
    const gone = merged.nodes.find((n) => n.id === "gone")!;
    expect(gone.lane_id).toBe("lane_calc_now");
    // Y dentro da 2ª faixa (topo 168).
    expect(gone.position.y).toBeGreaterThanOrEqual(168);
    expect(gone.position.y).toBeLessThan(168 + 168);
  });

  it("adiciona faixa da referência quando não há equivalente atual", () => {
    const reference = flow({
      lanes: [{ id: "lane_only_ref", label: "Publicação", height: 168 }],
      nodes: [
        {
          id: "gone",
          type: "process",
          label: "Removido",
          position: { x: 80, y: 40 },
          lane_id: "lane_only_ref",
        },
      ],
      edges: [],
    });
    const current = flow({
      lanes: [{ id: "lane_a", label: "Coleta", height: 168 }],
      nodes: [
        { id: "keep", type: "process", label: "Atual", position: { x: 40, y: 40 }, lane_id: "lane_a" },
      ],
      edges: [],
    });
    const merged = mergeRemovedNodesIntoFlowchartForDiff(current, reference, ["gone"]);
    expect(merged.lanes?.map((l) => l.id)).toEqual(["lane_a", "lane_only_ref"]);
    expect(merged.nodes.find((n) => n.id === "gone")?.lane_id).toBe("lane_only_ref");
  });
});
