import { describe, expect, it } from "vitest";

import type { ComunicadoDataResolved } from "./comunicadoTypes";
import {
  buildTextDataLinkPatch,
  formatTextProjectionValue,
  resolveTextBlockDisplayRuns,
  resolveTextDisplayValue,
  textBlockHasDataBinding,
} from "./textViewProjection";

const resolved: ComunicadoDataResolved = {
  kpi: { value: 42.5, label: "OEE" },
  kpiMetrics: [{ field: "oee", value: 42.5, label: "OEE" }],
  table: {
    columns: [{ key: "branch", label: "Filial" }],
    rows: [{ branch: "01", oee: 42.5 }],
  },
};

describe("textViewProjection", () => {
  it("resolveTextDisplayValue aplica prefixo, formato e suffixo", () => {
    expect(
      resolveTextDisplayValue(resolved, {
        field: "oee",
        format: "percent",
        prefix: "Meta: ",
        suffix: " hoje",
      }).text,
    ).toMatch(/Meta: 42[,.]5% hoje/);
  });

  it("resolveTextBlockDisplayRuns com dataRef dinâmico", () => {
    const runs = resolveTextBlockDisplayRuns(
      {
        content: "",
        contentRuns: [
          { text: "OEE: ", style: { fontWeight: "bold" } },
          { text: "?", dataRef: { field: "oee", format: "number" } },
        ],
      },
      resolved,
    );
    expect(runs[0]?.text).toBe("OEE: ");
    expect(runs[1]?.text).toContain("42");
  });

  it("buildTextDataLinkPatch sugere campo default", () => {
    const patch = buildTextDataLinkPatch({
      dataSourceId: "src-1",
      resolved,
    });
    expect(patch.dataSourceId).toBe("src-1");
    expect(patch.textProjection?.field).toBe("oee");
  });

  it("textBlockHasDataBinding detecta projeção ou dataRef", () => {
    expect(textBlockHasDataBinding({ textProjection: { field: "oee" } })).toBe(true);
    expect(
      textBlockHasDataBinding({
        contentRuns: [{ text: "x", dataRef: { field: "oee" } }],
      }),
    ).toBe(true);
    expect(textBlockHasDataBinding({ content: "estático" })).toBe(false);
  });

  it("formatTextProjectionValue compact", () => {
    expect(formatTextProjectionValue(12500, "compact")).toMatch(/12/);
  });
});
