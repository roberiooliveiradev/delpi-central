import { describe, expect, it } from "vitest";
import {
  applyDiffHighlightsToRichTree,
  formatDiffSummary,
  mergeRemovedNodesIntoTreeForDiff,
} from "./diffHighlightDisplay";
import type { DecompositionTreeV1 } from "../types/decomposition";
import type { RichTreeNode } from "../types/richTree";

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
