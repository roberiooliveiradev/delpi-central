import { describe, expect, it } from "vitest";

import type { DecompositionNode } from "../types/decomposition";
import {
  canAcceptDecompositionDrop,
  moveDecompositionNode,
  resolveDecompositionDropPosition,
} from "./decompositionReorder";

const nodes: DecompositionNode[] = [
  {
    id: "pk-1",
    level: "processo_chave",
    ordem: 1,
    label: "Coleta",
    parent_id: null,
    descricao: null,
  },
  {
    id: "pk-2",
    level: "processo_chave",
    ordem: 2,
    label: "Cálculo",
    parent_id: null,
    descricao: null,
  },
  {
    id: "ta-1",
    level: "tarefa",
    ordem: 1,
    label: "ERP",
    parent_id: "pk-1",
    descricao: null,
  },
  {
    id: "ta-2",
    level: "tarefa",
    ordem: 2,
    label: "Limpeza",
    parent_id: "pk-1",
    descricao: null,
  },
  {
    id: "ta-3",
    level: "tarefa",
    ordem: 1,
    label: "Consolidar",
    parent_id: "pk-2",
    descricao: null,
  },
  {
    id: "st-1",
    level: "sub_tarefa",
    ordem: 1,
    label: "Validar",
    parent_id: "ta-3",
    descricao: null,
  },
];

function ordem(nodesList: DecompositionNode[], nodeId: string): number {
  return nodesList.find((node) => node.id === nodeId)?.ordem ?? -1;
}

function parentId(nodesList: DecompositionNode[], nodeId: string): string | null {
  return nodesList.find((node) => node.id === nodeId)?.parent_id ?? null;
}

describe("moveDecompositionNode", () => {
  it("reordena tarefas dentro do mesmo processo-chave", () => {
    const next = moveDecompositionNode(nodes, "ta-2", "ta-1", "before");
    expect(ordem(next, "ta-2")).toBe(1);
    expect(ordem(next, "ta-1")).toBe(2);
    expect(parentId(next, "ta-2")).toBe("pk-1");
  });

  it("migra tarefa para outro processo-chave", () => {
    const next = moveDecompositionNode(nodes, "ta-1", "pk-2", "inside");
    expect(parentId(next, "ta-1")).toBe("pk-2");
    expect(ordem(next, "ta-1")).toBe(2);
    expect(ordem(next, "ta-2")).toBe(1);
  });

  it("reordena processos-chave", () => {
    const next = moveDecompositionNode(nodes, "pk-2", "pk-1", "before");
    expect(ordem(next, "pk-2")).toBe(1);
    expect(ordem(next, "pk-1")).toBe(2);
  });

  it("move sub-tarefa para outra tarefa", () => {
    const next = moveDecompositionNode(nodes, "st-1", "ta-1", "inside");
    expect(parentId(next, "st-1")).toBe("ta-1");
    expect(ordem(next, "st-1")).toBe(1);
  });

  it("rejeita soltar processo-chave dentro de tarefa", () => {
    expect(canAcceptDecompositionDrop(nodes, "pk-1", "ta-1", "inside")).toBe(false);
    expect(moveDecompositionNode(nodes, "pk-1", "ta-1", "inside")).toEqual(nodes);
  });

  it("rejeita soltar nó dentro do próprio descendente", () => {
    expect(canAcceptDecompositionDrop(nodes, "pk-2", "st-1", "inside")).toBe(false);
  });
});

describe("resolveDecompositionDropPosition", () => {
  it("prioriza inside na faixa central quando permitido", () => {
    expect(resolveDecompositionDropPosition(20, 40, true)).toBe("inside");
  });

  it("usa before/after nas bordas", () => {
    expect(resolveDecompositionDropPosition(5, 40, true)).toBe("before");
    expect(resolveDecompositionDropPosition(35, 40, false)).toBe("after");
  });
});
