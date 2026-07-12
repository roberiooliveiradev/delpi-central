import { describe, expect, it } from "vitest";

import {
  TABLE_VIEW_MAX_COLS_CAP,
  TABLE_VIEW_MAX_ROWS_CAP,
  applyTableViewDisplayLimits,
  normalizeTableViewLimit,
} from "./tableViewLimits";

describe("tableViewLimits", () => {
  it("normalizeTableViewLimit ignora vazio e limita ao cap", () => {
    expect(normalizeTableViewLimit(undefined, TABLE_VIEW_MAX_ROWS_CAP)).toBeUndefined();
    expect(normalizeTableViewLimit("", TABLE_VIEW_MAX_ROWS_CAP)).toBeUndefined();
    expect(normalizeTableViewLimit(0, TABLE_VIEW_MAX_ROWS_CAP)).toBeUndefined();
    expect(normalizeTableViewLimit(5, TABLE_VIEW_MAX_ROWS_CAP)).toBe(5);
    expect(normalizeTableViewLimit(999, TABLE_VIEW_MAX_ROWS_CAP)).toBe(TABLE_VIEW_MAX_ROWS_CAP);
    expect(normalizeTableViewLimit(30, TABLE_VIEW_MAX_COLS_CAP)).toBe(TABLE_VIEW_MAX_COLS_CAP);
  });

  it("aplica truncamento de linhas e colunas na exibição", () => {
    const columns = [
      { key: "a", label: "A" },
      { key: "b", label: "B" },
      { key: "c", label: "C" },
    ];
    const rows = [
      { a: 1, b: 2, c: 3 },
      { a: 4, b: 5, c: 6 },
      { a: 7, b: 8, c: 9 },
    ];
    const limited = applyTableViewDisplayLimits(rows, columns, { maxRows: 2, maxCols: 2 });
    expect(limited.columns.map((c) => c.key)).toEqual(["a", "b"]);
    expect(limited.rows).toHaveLength(2);
    expect(limited.rows[0]).toEqual({ a: 1, b: 2 });
  });

  it("sem limites devolve os dados intactos", () => {
    const columns = [{ key: "a", label: "A" }];
    const rows = [{ a: 1 }, { a: 2 }];
    expect(applyTableViewDisplayLimits(rows, columns, {})).toEqual({ rows, columns });
  });
});
