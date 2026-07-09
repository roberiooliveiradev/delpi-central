import { describe, expect, it } from "vitest";

import type { DecompositionTreeV1 } from "../types/decomposition";
import {
  decompositionNodePath,
  humanizeDecompositionApiError,
  validateDecompositionTreeForSave,
} from "./decompositionValidation";

const tree: DecompositionTreeV1 = {
  format: "decomposition_tree_v1",
  format_version: 1,
  nodes: [
    {
      id: "pk-1",
      level: "processo_chave",
      ordem: 1,
      label: "Coleta de dados operacionais",
      parent_id: null,
      descricao: null,
    },
    {
      id: "pk-2",
      level: "processo_chave",
      ordem: 2,
      label: "Cálculo e consolidação de indicadores",
      parent_id: null,
      descricao: null,
    },
    {
      id: "ta-empty",
      level: "tarefa",
      ordem: 1,
      label: "",
      parent_id: "pk-2",
      descricao: null,
    },
  ],
};

describe("validateDecompositionTreeForSave", () => {
  it("detecta rótulo vazio com caminho amigável", () => {
    const report = validateDecompositionTreeForSave(tree);
    expect(report.valid).toBe(false);
    expect(report.issues).toHaveLength(1);
    expect(report.issues[0]?.nodeId).toBe("ta-empty");
    expect(report.issues[0]?.message).toContain("Cálculo e consolidação de indicadores");
    expect(report.issues[0]?.message).toContain("Tarefa (ordem 1)");
  });

  it("retorna válido quando todos os rótulos estão preenchidos", () => {
    const validTree: DecompositionTreeV1 = {
      ...tree,
      nodes: tree.nodes.map((node) =>
        node.id === "ta-empty" ? { ...node, label: "Consolidar indicadores" } : node
      ),
    };
    expect(validateDecompositionTreeForSave(validTree).valid).toBe(true);
  });
});

describe("decompositionNodePath", () => {
  it("monta breadcrumb com fallback de ordem para rótulo vazio", () => {
    expect(decompositionNodePath(tree.nodes, "ta-empty")).toBe(
      "Cálculo e consolidação de indicadores → Tarefa (ordem 1)"
    );
  });
});

describe("humanizeDecompositionApiError", () => {
  it("traduz erro técnico da API usando a árvore local", () => {
    const report = humanizeDecompositionApiError("nodes[2].label obrigatório.", tree);
    expect(report.valid).toBe(false);
    expect(report.issues[0]?.nodeId).toBe("ta-empty");
    expect(report.issues[0]?.message).toMatch(/Informe o nome da tarefa/);
  });

  it("usa mensagem genérica quando não há árvore", () => {
    const report = humanizeDecompositionApiError("nodes[2].label obrigatório.");
    expect(report.issues[0]?.message).toContain("item sem nome");
  });
});
