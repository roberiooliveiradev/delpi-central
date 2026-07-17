import { describe, expect, it } from "vitest";

import type { ComunicadoTableViewBlock } from "./comunicadoTypes";
import {
  distributeTableProjectionColumnWidths,
  resizeTableProjectionColumn,
  resizeTableProjectionColumns,
  resolveEditableTableProjectionColumns,
  selectedTableProjectionColumnKeys,
} from "./tableProjectionEditing";

const block = {
  type: "table_view",
  tableProjection: {
    columns: [
      { key: "code", label: "Código", visible: true },
      { key: "description", label: "Descrição", visible: true, widthPct: 60 },
    ],
  },
} as ComunicadoTableViewBlock;

describe("tableProjectionEditing", () => {
  it("preserva as colunas e altera somente a largura selecionada", () => {
    const projection = resizeTableProjectionColumn(block, "code", 35.26);

    expect(projection.columns).toEqual([
      { key: "code", label: "Código", visible: true, widthPct: 35.3 },
      { key: "description", label: "Descrição", visible: true, widthPct: 60 },
    ]);
  });

  it("aplica a mesma largura a várias colunas selecionadas", () => {
    const projection = resizeTableProjectionColumns(block, ["code", "description"], 25);

    expect(projection.columns).toEqual([
      { key: "code", label: "Código", visible: true, widthPct: 25 },
      { key: "description", label: "Descrição", visible: true, widthPct: 25 },
    ]);
  });

  it("mapeia partes headerCell para chaves das colunas visíveis", () => {
    const withHidden = {
      type: "table_view",
      tableProjection: {
        columns: [
          { key: "internal", label: "Interno", visible: false },
          { key: "code", label: "Código", visible: true },
          { key: "description", label: "Descrição", visible: true },
        ],
      },
    } as ComunicadoTableViewBlock;

    const keys = selectedTableProjectionColumnKeys(withHidden, [
      { kind: "headerCell", colIndex: 0 },
      { kind: "headerCell", colIndex: 1 },
      { kind: "frame" },
    ]);

    expect(keys).toEqual(["code", "description"]);
  });

  it("distribui a largura igualmente entre colunas visíveis", () => {
    const withHidden = {
      type: "table_view",
      tableProjection: {
        columns: [
          { key: "code", label: "Código", visible: true, widthPct: 80 },
          { key: "description", label: "Descrição", visible: true },
          { key: "internal", label: "Interno", visible: false, widthPct: 20 },
        ],
      },
    } as ComunicadoTableViewBlock;

    const projection = distributeTableProjectionColumnWidths(withHidden);

    expect(projection.columns).toEqual([
      { key: "code", label: "Código", visible: true, widthPct: 50 },
      { key: "description", label: "Descrição", visible: true, widthPct: 50 },
      { key: "internal", label: "Interno", visible: false },
    ]);
  });

  it("materializa colunas resolvidas quando ainda não há projeção", () => {
    const withoutProjection = {
      type: "table_view",
      resolved: {
        table: {
          columns: [{ key: "total", label: "Total" }],
          rows: [{ total: 10 }],
        },
      },
    } as unknown as ComunicadoTableViewBlock;

    expect(resolveEditableTableProjectionColumns(withoutProjection)).toEqual([
      { key: "total", label: "Total", visible: true },
    ]);
  });
});
