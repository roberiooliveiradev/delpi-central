import { describe, expect, it } from "vitest";

import type { ChatTreeNode } from "../../data/api/chatTypes";

import {
  collectTreeBlockSections,
  expandTreeSegmentsToBlockTables,
  formatTreeNodeMeta,
  treePresentationToBlockTables,
} from "./treePresentationUtils";

function buildSampleTree(): ChatTreeNode {
  return {
    id: "90260015",
    label: "90260015",
    subtitle: "CHICOTE DE LIGACAO",
    badge: "PA",
    meta: { quantity: 1, unit: "MI" },
    children: [
      {
        id: "50210372",
        label: "50210372",
        subtitle: "CA18AZUL",
        badge: "PI",
        meta: { quantity: 1, unit: "MI" },
        children: [
          {
            id: "10420040",
            label: "10420040",
            subtitle: "CABO PVC",
            badge: "MP",
            meta: { quantity: 142, unit: "MT" },
          },
        ],
      },
      {
        id: "50230219",
        label: "50230219",
        subtitle: "CA18BRAN",
        badge: "PI",
        meta: { quantity: 1, unit: "MI" },
        children: [
          {
            id: "10080006",
            label: "10080006",
            subtitle: "TERM. FASTON",
            badge: "MP",
            meta: { quantity: 64, unit: "PC" },
          },
          {
            id: "10090352",
            label: "10090352",
            subtitle: "ISOLADOR NYLON",
            badge: "MP",
            meta: { quantity: 46, unit: "PC" },
          },
        ],
      },
    ],
  };
}

describe("treePresentationUtils blocks", () => {
  it("formata meta de estoque com quantidades disponível/atual/empenhado", () => {
    expect(
      formatTreeNodeMeta({
        available_quantity: 455000,
        current_quantity: 455000,
        committed_quantity: 0,
        unit: "un.",
      }),
    ).toBe("Disponível: 455.000 · Saldo atual: 455.000 · Empenhado: 0 un.");
  });

  it("formata meta BOM com quantity e unit", () => {
    expect(formatTreeNodeMeta({ quantity: 142, unit: "MT" })).toBe("142 MT");
  });

  it("gera bloco para cada nível com filhos", () => {
    const blocks = collectTreeBlockSections(buildSampleTree());

    expect(blocks).toHaveLength(3);
    expect(blocks[0].heading).toContain("90260015");
    expect(blocks[0].rows.map((row) => row.codigo)).toEqual(["50210372", "50230219"]);
    expect(blocks[1].heading).toContain("50210372");
    expect(blocks[1].rows.map((row) => row.codigo)).toEqual(["10420040"]);
    expect(blocks[2].heading).toContain("50230219");
    expect(blocks[2].rows.map((row) => row.codigo)).toEqual(["10080006", "10090352"]);
  });

  it("não inclui coluna caminho nas linhas", () => {
    const tables = treePresentationToBlockTables({
      type: "tree",
      title: "Estrutura do produto 90260015",
      root: buildSampleTree(),
    });

    for (const table of tables) {
      expect(table.columns.map((column) => column.key)).not.toContain("caminho");

      for (const row of table.rows) {
        expect(row).not.toHaveProperty("caminho");
      }
    }
  });

  it("expande segmento tree em múltiplas tabelas", () => {
    const expanded = expandTreeSegmentsToBlockTables([
      {
        kind: "tree",
        presentation: {
          type: "tree",
          title: "Estrutura do produto 90260015",
          root: buildSampleTree(),
        },
      },
    ]);

    expect(expanded).toHaveLength(3);
    expect(expanded.every((segment) => segment.kind === "table")).toBe(true);
  });
});
