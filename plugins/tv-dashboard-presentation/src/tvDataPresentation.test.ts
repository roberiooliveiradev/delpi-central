import { describe, expect, it } from "vitest";

import type { ComunicadoDataBlock } from "./comunicadoTypes";
import {
  resolveChartType,
  resolveEffectiveDisplayMode,
  resolveTableColumns,
} from "./tvDataPresentation";

describe("tvDataPresentation", () => {
  const baseBlock: ComunicadoDataBlock = {
    id: "b1",
    type: "data_kpi",
    frame: { x: 0, y: 0, w: 20, h: 20 },
    dataBinding: { operationId: "get_oee" },
  };

  it("prioriza displayMode do binding sobre block.type", () => {
    const block: ComunicadoDataBlock = {
      ...baseBlock,
      type: "data_kpi",
      dataBinding: { operationId: "get_oee", displayMode: "table" },
    };
    expect(resolveEffectiveDisplayMode(block)).toBe("table");
  });

  it("monta colunas a partir de meta.fields", () => {
    const columns = resolveTableColumns(
      {
        meta: {
          fields: [
            { key: "code", label: "Código" },
            { key: "value", label: "Valor" },
          ],
        },
        table: { rows: [{ code: "A", value: 10 }] },
      },
      [{ code: "A", value: 10 }],
    );
    expect(columns).toEqual([
      { key: "code", label: "Código" },
      { key: "value", label: "Valor" },
    ]);
  });

  it("resolve chartType a partir do displayMode", () => {
    expect(resolveChartType("bar_chart", undefined)).toBe("bar");
    expect(resolveChartType("line_chart", undefined)).toBe("line");
  });
});
