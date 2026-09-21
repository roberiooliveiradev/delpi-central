import { describe, expect, it } from "vitest";

import {
  createDefaultColumnVisibility,
  DEFAULT_VISIBLE_COLUMN_KEYS,
  TABLE_COLUMNS,
  tableColumnLabel,
} from "./tableColumns";

describe("tableColumns", () => {
  it("liga data de despacho e centro do cliente no seletor default", () => {
    expect(DEFAULT_VISIBLE_COLUMN_KEYS).toContain("data_despacho");
    expect(DEFAULT_VISIBLE_COLUMN_KEYS).toContain("customer_center");
    expect(TABLE_COLUMNS.find((column) => column.key === "data_entrega")?.label).toBe(
      "Data de entrega",
    );
    expect(tableColumnLabel("data_entrega")).toBe("Data de entrega");
    expect(TABLE_COLUMNS.find((column) => column.key === "data_despacho")?.label).toBe(
      "Data de despacho",
    );
    expect(TABLE_COLUMNS.find((column) => column.key === "customer_center")?.label).toBe(
      "Centro",
    );
    expect(TABLE_COLUMNS.find((column) => column.key === "no_estoque")?.label).toBe(
      "Estoque alocado",
    );
    expect(TABLE_COLUMNS.every((column) => column.label !== column.label.toUpperCase())).toBe(
      true,
    );

    const visibility = createDefaultColumnVisibility();
    expect(visibility.data_despacho).toBe(true);
    expect(visibility.customer_center).toBe(true);
    expect(visibility.no_estoque).toBe(false);
  });
});
