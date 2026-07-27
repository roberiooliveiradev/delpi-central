import { describe, expect, it } from "vitest";

import type { ComunicadoDataResolved } from "./comunicadoTypes";
import {
  buildTextDataLinkPatch,
  formatTextProjectionValue,
  patchTextProjectionFromEditedDisplay,
  resolveTextBlockDisplayRuns,
  resolveTextDisplayValue,
  splitEditedDisplayAroundCoreValue,
  suggestDefaultTextProjection,
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

  it("patchTextProjectionFromEditedDisplay atualiza prefixo/sufixo sem perder o campo", () => {
    const projection = { field: "oee", format: "number" as const, prefix: "Meta R$ " };
    const core = resolveTextDisplayValue(resolved, { field: "oee", format: "number" }).text;
    const next = patchTextProjectionFromEditedDisplay(
      projection,
      `Alvo ${core} un`,
      resolved,
    );
    expect(next.field).toBe("oee");
    expect(next.prefix).toBe("Alvo ");
    expect(next.suffix).toBe(" un");
  });

  it("splitEditedDisplayAroundCoreValue separa affixes pelo valor âncora", () => {
    expect(splitEditedDisplayAroundCoreValue("Meta R$ 9.000 un", "9.000")).toEqual({
      prefix: "Meta R$ ",
      suffix: " un",
    });
    expect(splitEditedDisplayAroundCoreValue("só prefixo", "9.000")).toEqual({
      prefix: "só prefixo",
      suffix: undefined,
    });
  });

  it("resolveTextBlockDisplayRuns usa resolved do bloco quando o 2º arg omite", () => {
    const runs = resolveTextBlockDisplayRuns({
      content: "",
      textProjection: { field: "oee", format: "number", prefix: "Meta: " },
      resolved,
    });
    expect(runs[0]?.text).toMatch(/^Meta: /);
    expect(runs[0]?.text).toContain("42");
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
    // KPI escalar expõe "value"; série tabular pode preferir "oee".
    expect(["value", "oee"]).toContain(patch.textProjection?.field);
  });

  it("buildTextDataLinkPatch preserva rótulo estático como prefixo (não substitui)", () => {
    const patch = buildTextDataLinkPatch({
      dataSourceId: "src-1",
      resolved,
      staticContent: "Realizado",
    });
    expect(patch.textProjection?.prefix).toBe("Realizado ");
    const display = resolveTextDisplayValue(resolved, patch.textProjection);
    expect(display.text.startsWith("Realizado ")).toBe(true);
    expect(display.text).toMatch(/42/);
  });

  it("buildTextDataLinkPatch não duplica espaço quando o rótulo já termina com :", () => {
    const patch = buildTextDataLinkPatch({
      dataSourceId: "src-1",
      resolved,
      staticContent: "Meta:",
    });
    expect(patch.textProjection?.prefix).toBe("Meta:");
  });

  it("suggestDefaultTextProjection usa primeiro campo do catálogo", () => {
    const suggested = suggestDefaultTextProjection(undefined, [
      { field: "value", label: "value" },
      { field: "meta", label: "Meta" },
    ]);
    expect(suggested?.field).toBe("value");
  });

  it("buildTextDataLinkPatch aceita catálogo sem resolved", () => {
    const patch = buildTextDataLinkPatch({
      dataSourceId: "src-2",
      catalogFields: [{ field: "value", label: "value" }],
    });
    expect(patch.textProjection?.field).toBe("value");
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

  it("formatTextProjectionValue percent usa vírgula; currency formata BRL", () => {
    expect(formatTextProjectionValue(80, "percent")).toBe("80,0%");
    expect(formatTextProjectionValue(4005.33, "currency")).toMatch(/R\$\s*4\.005,33/);
  });

  it("campo value do KPI não é sombreado por tabela campo/valor (SI escalar)", () => {
    const siResolved: ComunicadoDataResolved = {
      kpi: { value: 1100, label: "value" },
      kpiMetrics: [{ field: "value", value: 1100, label: "value" }],
      table: {
        columns: [
          { key: "campo", label: "Campo" },
          { key: "valor", label: "Valor" },
        ],
        rows: [
          { campo: "name", valor: "PPM Externo" },
          { campo: "value", valor: 1100 },
        ],
      },
    };
    expect(
      resolveTextDisplayValue(siResolved, {
        field: "value",
        aggregation: "first",
        format: "number",
        fallback: "—",
      }).text,
    ).toMatch(/1[.‎]?100|1\.100|1100/);
  });

  it("série OEE: média agrega todas as linhas; lista mostra cada valor", () => {
    const series: ComunicadoDataResolved = {
      kpi: { value: 90, label: "value" },
      kpiMetrics: [{ field: "value", value: 90, label: "value" }],
      table: {
        columns: [
          { key: "periodo", label: "Período" },
          { key: "value", label: "OEE — série temporal" },
        ],
        rows: [
          { periodo: "01/07/26", value: 70 },
          { periodo: "02/07/26", value: 80 },
          { periodo: "03/07/26", value: 90 },
        ],
      },
    };
    expect(
      resolveTextDisplayValue(series, { field: "value", aggregation: "avg", format: "number" }).text,
    ).toMatch(/80/);
    expect(
      resolveTextDisplayValue(series, { field: "value", aggregation: "list", format: "number" }).text,
    ).toBe("70\n80\n90");
    expect(
      resolveTextDisplayValue(series, {
        field: "periodo",
        aggregation: "avg",
        format: "number",
        fallback: "—",
      }).text,
    ).toBe("—");
  });
});
