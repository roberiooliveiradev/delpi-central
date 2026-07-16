import { describe, expect, it } from "vitest";

import type { ComunicadoTableViewBlock } from "./comunicadoTypes";
import {
  resizeTableProjectionColumn,
  resolveEditableTableProjectionColumns,
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

  it("materializa colunas resolvidas quando ainda não há projeção", () => {
    const withoutProjection = {
      type: "table_view",
      resolved: {
        table: {
          columns: [{ key: "total", label: "Total" }],
          rows: [{ total: 10 }],
        },
      },
    } as ComunicadoTableViewBlock;

    expect(resolveEditableTableProjectionColumns(withoutProjection)).toEqual([
      { key: "total", label: "Total", visible: true },
    ]);
  });
});
