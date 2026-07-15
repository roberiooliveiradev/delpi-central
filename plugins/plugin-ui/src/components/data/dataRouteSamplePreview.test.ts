import { describe, expect, it } from "vitest";

import {
  buildSampleDataRoutePreview,
  mapEnrichedBlockToDataRoutePreview,
} from "./dataRouteSamplePreview";

describe("buildSampleDataRoutePreview", () => {
  it("monta KPI, tabela e série com poucos dados", () => {
    expect(buildSampleDataRoutePreview({ id: "a", label: "OEE", kind: "kpi" })).toMatchObject({
      kind: "kpi",
      source: "sample",
      kpi: { label: "OEE", value: "87,4%" },
    });

    const table = buildSampleDataRoutePreview({ id: "b", label: "Lista", kind: "table" });
    expect(table.table?.rows).toHaveLength(4);
    expect(table.table?.columns[0]?.key).toBe("code");

    const series = buildSampleDataRoutePreview({ id: "c", label: "Série", kind: "series" });
    expect(series.series?.points).toHaveLength(5);
  });
});

describe("mapEnrichedBlockToDataRoutePreview", () => {
  it("mapeia resolved.kpi / table / chart", () => {
    expect(
      mapEnrichedBlockToDataRoutePreview(
        { resolved: { kpi: { label: "OEE", value: 0.912 } } },
        "kpi",
      ),
    ).toMatchObject({
      kind: "kpi",
      source: "live",
      kpi: { label: "OEE", value: "0,91" },
    });

    const table = mapEnrichedBlockToDataRoutePreview(
      {
        resolved: {
          table: {
            columns: [{ key: "code", label: "Código" }],
            rows: [{ code: "A1" }, { code: "B2" }, { code: "C3" }, { code: "D4" }, { code: "E5" }, { code: "F6" }],
          },
        },
      },
      "table",
    );
    expect(table.table?.rows).toHaveLength(5);

    const series = mapEnrichedBlockToDataRoutePreview(
      {
        resolved: {
          chart: {
            points: [
              { label: "Jan", value: 10 },
              { label: "Fev", value: 12 },
            ],
          },
        },
      },
      "series",
    );
    expect(series.series?.points).toEqual([
      { label: "Jan", value: 10 },
      { label: "Fev", value: 12 },
    ]);
  });
});
