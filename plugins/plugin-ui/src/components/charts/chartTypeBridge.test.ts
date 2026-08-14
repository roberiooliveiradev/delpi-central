import { describe, expect, it } from "vitest";

import {
  delpiChartTypeToPersisted,
  persistedChartTypeToDelpi,
  persistedChartTypesToDelpi,
} from "./chartTypeBridge";

describe("chartTypeBridge", () => {
  it("mapeia column ↔ bar (Colunas do catálogo)", () => {
    expect(persistedChartTypeToDelpi("column")).toBe("bar");
    expect(delpiChartTypeToPersisted("bar", ["column", "line", "area"])).toBe("column");
    expect(delpiChartTypeToPersisted("bar", ["horizontal_bar", "bar", "pie"])).toBe("bar");
  });

  it("deduplica column+bar ao listar tipos Delpi", () => {
    expect(persistedChartTypesToDelpi(["column", "line", "area"])).toEqual([
      "bar",
      "line",
      "area",
    ]);
  });

  it("rejeita tipo fora do allowed", () => {
    expect(delpiChartTypeToPersisted("pie", ["column", "line"])).toBeNull();
  });
});
