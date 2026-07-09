import { describe, expect, it } from "vitest";

import type { DecompositionTreeV1 } from "../types/decomposition";
import { buildDecompositionRichTree } from "./decompositionRichTree";

const tree: DecompositionTreeV1 = {
  format: "decomposition_tree_v1",
  format_version: 1,
  nodes: [
    {
      id: "pk-1",
      level: "processo_chave",
      ordem: 1,
      label: "",
      parent_id: null,
      descricao: null,
    },
    {
      id: "ta-1",
      level: "tarefa",
      ordem: 1,
      label: "Minha tarefa",
      parent_id: "pk-1",
      descricao: null,
    },
  ],
};

describe("buildDecompositionRichTree", () => {
  it("preserva rótulo vazio em vez de repor Tarefa/Processo-chave", () => {
    const root = buildDecompositionRichTree(tree);
    expect(root?.label).toBe("");
  });

  it("usa fallback só quando label não foi definido no nó", () => {
    const legacyTree: DecompositionTreeV1 = {
      ...tree,
      nodes: [
        {
          id: "pk-legacy",
          level: "processo_chave",
          ordem: 1,
          label: undefined as unknown as string,
          parent_id: null,
          descricao: null,
        },
      ],
    };
    const root = buildDecompositionRichTree(legacyTree);
    expect(root?.label).toBe("Processo-chave");
  });

  it("preserva override vazio no overlay da revisão", () => {
    const root = buildDecompositionRichTree(tree, {
      overlay: {
        format: "decomposition_overlay_v1",
        format_version: 1,
        node_overrides: {
          "pk-1": { label: "" },
        },
      },
    });
    expect(root?.label).toBe("");
  });
});
