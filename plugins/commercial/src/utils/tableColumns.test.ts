import { describe, expect, it } from "vitest";

import {
  createDefaultColumnVisibility,
  DEFAULT_VISIBLE_COLUMN_KEYS,
  TABLE_COLUMNS,
  tableColumnLabel,
} from "./tableColumns";

describe("tableColumns", () => {
  it("liga data de despacho no seletor default e usa rótulos em caixa de sentença", () => {
    expect(DEFAULT_VISIBLE_COLUMN_KEYS).toContain("data_despacho");
    expect(TABLE_COLUMNS.find((column) => column.key === "data_entrega")?.label).toBe(
      "Data de entrega",
    );
    expect(tableColumnLabel("data_entrega")).toBe("Data de entrega");
    expect(TABLE_COLUMNS.find((column) => column.key === "data_despacho")?.label).toBe(
      "Data de despacho",
    );
    expect(TABLE_COLUMNS.find((column) => column.key === "no_estoque")?.label).toBe(
      "Estoque alocado",
    );
    expect(TABLE_COLUMNS.every((column) => column.label !== column.label.toUpperCase())).toBe(
      true,
    );

    const visibility = createDefaultColumnVisibility();
    expect(visibility.data_despacho).toBe(true);
    expect(visibility.no_estoque).toBe(false);
  });
});
