import { describe, expect, it } from "vitest";

import { nextSortDirection, resolvePreviewSort } from "./resolvePreviewSort";

describe("resolvePreviewSort", () => {
  it("extrai a última Table.Sort do script compilado", () => {
    expect(
      resolvePreviewSort([
        {
          name: "A",
          operation: "Table.SelectColumns",
          label: "A",
          formula: 'Table.SelectColumns(Fonte, {"a"})',
        },
        {
          name: "B",
          operation: "Table.Sort",
          label: "B",
          formula: 'Table.Sort(A, {{"periodo", Order.Ascending}})',
        },
        {
          name: "C",
          operation: "Table.Sort",
          label: "C",
          formula: 'Table.Sort(B, {{"value", Order.Descending}})',
        },
      ]),
    ).toEqual({ key: "value", direction: "desc" });
  });

  it("ignora ordenações posteriores à etapa selecionada", () => {
    const steps = [
      {
        name: "B",
        operation: "Table.Sort",
        label: "B",
        formula: 'Table.Sort(Fonte, {{"periodo", Order.Ascending}})',
      },
      {
        name: "C",
        operation: "Table.Sort",
        label: "C",
        formula: 'Table.Sort(B, {{"value", Order.Descending}})',
      },
    ];
    expect(resolvePreviewSort(steps, "B")).toEqual({
      key: "periodo",
      direction: "asc",
    });
    expect(resolvePreviewSort(steps, "Fonte")).toBeNull();
  });

  it("alterna direção na mesma coluna", () => {
    expect(nextSortDirection({ key: "a", direction: "asc" }, "a")).toBe("desc");
    expect(nextSortDirection({ key: "a", direction: "desc" }, "a")).toBe("asc");
    expect(nextSortDirection({ key: "a", direction: "asc" }, "b")).toBe("asc");
  });
});
