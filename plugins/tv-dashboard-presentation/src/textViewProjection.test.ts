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
import { discoverResolvedFieldOptions } from "./viewProjection";

const resolved: ComunicadoDataResolved = {
  kpi: { value: 42.5, label: "OEE" },
  kpiMetrics: [{ field: "oee", value: 42.5, label: "OEE" }],
  table: {
    columns: [{ key: "branch", label: "Filial" }],
    rows: [{ branch: "01", oee: 42.5 }],
  },
};

describe("textViewProjection", () => {
  it("resolveTextDisplayValue pinta displayText do enrich com affixes já compostos", () => {
    const withServer: ComunicadoDataResolved = {
      ...resolved,
      serverDisplayApplied: true,
      displayText: "Meta: 42,5% hoje",
    };
    expect(
      resolveTextDisplayValue(withServer, {
        field: "oee",
        format: "percent",
        prefix: "Meta: ",
        suffix: " hoje",
      }).text,
    ).toBe("Meta: 42,5% hoje");
  });

  it("patchTextProjectionFromEditedDisplay atualiza prefixo/sufixo sem perder o campo", () => {
    const projection = { field: "oee", format: "number" as const, prefix: "Meta R$ " };
    const baked: ComunicadoDataResolved = {
      ...resolved,
      serverDisplayApplied: true,
      displayText: "42,5",
    };
    const next = patchTextProjectionFromEditedDisplay(projection, "Alvo 42,5 un", baked);
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

  it("resolveTextBlockDisplayRuns usa displayText do enrich quando o 2º arg omite", () => {
    const runs = resolveTextBlockDisplayRuns({
      content: "",
      textProjection: { field: "oee", format: "number", prefix: "Meta: " },
      resolved: {
        ...resolved,
        serverDisplayApplied: true,
        displayText: "Meta: 42,5",
      },
    });
    expect(runs[0]?.text).toBe("Meta: 42,5");
  });

  it("resolveTextBlockDisplayRuns com displayRuns do enrich", () => {
    const runs = resolveTextBlockDisplayRuns(
      {
        content: "",
        contentRuns: [
          { text: "OEE: ", style: { fontWeight: "bold" } },
          { text: "?", dataRef: { field: "oee", format: "number" } },
        ],
      },
      {
        ...resolved,
        serverDisplayApplied: true,
        displayRuns: [
          { text: "OEE: ", style: { fontWeight: "bold" } },
          { text: "42,5", dataRef: { field: "oee", format: "number" } },
        ],
      },
    );
    expect(runs[0]?.text).toBe("OEE: ");
    expect(runs[1]?.text).toBe("42,5");
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
    const display = resolveTextDisplayValue(
      {
        ...resolved,
        serverDisplayApplied: true,
        displayText: "Realizado 42,5",
      },
      patch.textProjection,
    );
    expect(display.text).toBe("Realizado 42,5");
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

  it("sem dataSourceId: projeção órfã não pinta travessão (só prefixo)", () => {
    expect(
      resolveTextDisplayValue(
        undefined,
        { field: "revenue", prefix: "ACUM. 2026 ", format: "currency" },
        { linkedDataSource: false },
      ).text,
    ).toBe("ACUM. 2026 ");
    expect(
      resolveTextBlockDisplayRuns({
        content: "",
        textProjection: { field: "revenue", prefix: "ACUM. 2026 " },
      })
        .map((run) => run.text)
        .join(""),
    ).toBe("ACUM. 2026 ");
    expect(
      resolveTextBlockDisplayRuns({
        content: "",
        dataSourceId: "src-1",
        textProjection: { field: "missing", prefix: "ACUM. 2026 " },
        resolved: { kpi: { value: null, label: "x" } },
      })
        .map((run) => run.text)
        .join(""),
    ).toBe("ACUM. 2026 —");
  });

  it("formatTextProjectionValue date usa calendário UTC", () => {
    expect(formatTextProjectionValue("2026-08-03", "date")).toBe("03/08/2026");
  });

  it("formatTextProjectionValue percent usa vírgula; currency formata BRL", () => {
    expect(formatTextProjectionValue(80, "percent")).toBe("80,0%");
    expect(formatTextProjectionValue(4005.33, "currency")).toMatch(/R\$\s*4\.005,33/);
  });

  it("formatTextProjectionValue respeita decimalPlaces com arredondamento", () => {
    expect(formatTextProjectionValue(1.235, "number", { decimalPlaces: 2 })).toBe("1,24");
    expect(formatTextProjectionValue(12.56, "percent", { decimalPlaces: 0 })).toBe("13%");
    expect(formatTextProjectionValue(10.556, "currency", { decimalPlaces: 2 })).toMatch(
      /R\$\s*10,56/,
    );
  });

  it("formatTextProjectionValue: displayFormat canônico vence enum legado", () => {
    expect(
      formatTextProjectionValue(12.345, "number", {
        decimalPlaces: 0,
        displayFormat: { category: "currency", currency: "BRL", decimalPlaces: 2 },
      }),
    ).toMatch(/R\$\s*12,35/);
  });

  it("campo value do KPI: paint usa displayText do enrich (não format client)", () => {
    const siResolved: ComunicadoDataResolved = {
      kpi: { value: 1100, label: "value" },
      kpiMetrics: [{ field: "value", value: 1100, label: "value" }],
      serverDisplayApplied: true,
      displayText: "1.100",
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
    ).toBe("1.100");
  });

  it("série OEE: paint usa displayText materializado (avg/list)", () => {
    const seriesAvg: ComunicadoDataResolved = {
      kpi: { value: 90, label: "value" },
      kpiMetrics: [{ field: "value", value: 90, label: "value" }],
      serverDisplayApplied: true,
      displayText: "80",
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
      resolveTextDisplayValue(seriesAvg, { field: "value", aggregation: "avg", format: "number" })
        .text,
    ).toBe("80");
    const seriesList: ComunicadoDataResolved = {
      ...seriesAvg,
      displayText: "70\n80\n90",
    };
    expect(
      resolveTextDisplayValue(seriesList, {
        field: "value",
        aggregation: "list",
        format: "number",
      }).text,
    ).toBe("70\n80\n90");
    expect(
      resolveTextDisplayValue(
        { ...seriesAvg, displayText: undefined, serverDisplayApplied: true },
        {
          field: "periodo",
          aggregation: "avg",
          format: "number",
          fallback: "—",
        },
      ).text,
    ).toBe("—");
  });

  it("resolveTextBlockDisplayRuns pinta filter dates via displayRuns do enrich", () => {
    const withContext: ComunicadoDataResolved = {
      ...resolved,
      serverDisplayApplied: true,
      displayRuns: [
        { text: "Novos Negócios · semana " },
        { text: "21/09/2026", dataRef: { field: "filter.start_date", format: "date" } },
        { text: " – " },
        { text: "27/09/2026", dataRef: { field: "filter.end_date", format: "date" } },
      ],
      contextFields: [
        { name: "filter.start_date", type: "date", projectable: true, origin: "effective_filter" },
        { name: "filter.end_date", type: "date", projectable: true, origin: "effective_filter" },
      ],
      contextValues: {
        "filter.start_date": "2026-09-21",
        "filter.end_date": "2026-09-27",
        "filter.date_range_label": "21/09/2026 – 27/09/2026",
      },
    };
    const runs = resolveTextBlockDisplayRuns({
      content: "",
      contentRuns: [
        { text: "Novos Negócios · semana " },
        { dataRef: { field: "filter.start_date", format: "date" } },
        { text: " – " },
        { dataRef: { field: "filter.end_date", format: "date" } },
      ],
      resolved: withContext,
    });
    expect(runs.map((run) => run.text).join("")).toBe(
      "Novos Negócios · semana 21/09/2026 – 27/09/2026",
    );
  });

  it("discoverResolvedFieldOptions inclui fields e contextFields declarados sem amostra", () => {
    const options = discoverResolvedFieldOptions({
      fields: [{ name: "forecast_value", projectable: true, label: "Previsto" }],
      contextFields: [
        { name: "filter.start_date", projectable: true, label: "Início do filtro" },
      ],
      contextValues: { "filter.start_date": "2026-09-21" },
    });
    expect(options.map((item) => item.field)).toEqual(
      expect.arrayContaining(["forecast_value", "filter.start_date"]),
    );
  });

  it("prefere displayText do enrich mesmo quando formatDisplayValue divergiria", () => {
    const withServer: ComunicadoDataResolved = {
      ...resolved,
      serverDisplayApplied: true,
      displayText: "SERVER-PAINT-99%",
      kpi: { value: 42.5, label: "OEE" },
    };
    expect(
      resolveTextDisplayValue(withServer, {
        field: "oee",
        format: "number",
        prefix: "Meta: ",
      }).text,
    ).toBe("SERVER-PAINT-99%");
    expect(
      resolveTextBlockDisplayRuns({
        content: "",
        textProjection: { field: "oee", format: "percent" },
        resolved: withServer,
      })[0]?.text,
    ).toBe("SERVER-PAINT-99%");
  });

  it("prefere displayRuns do enrich sem reformatar dataRef", () => {
    const withServer: ComunicadoDataResolved = {
      ...resolved,
      serverDisplayApplied: true,
      displayRuns: [
        { text: "ACUMULADO " },
        { text: "01/01/2099", dataRef: { field: "filter.start_date", format: "raw" } },
      ],
      displayText: "ACUMULADO 01/01/2099",
      contextValues: { "filter.start_date": "2026-01-01" },
    };
    const painted = resolveTextBlockDisplayRuns(
      {
        content: "",
        contentRuns: [
          { text: "ACUMULADO " },
          { text: "?", dataRef: { field: "filter.start_date", format: "date" } },
        ],
      },
      withServer,
    );
    expect(painted.map((run) => run.text).join("")).toBe("ACUMULADO 01/01/2099");
  });

  it("sem displayText o paint nao formata no cliente (FE-BE-002)", () => {
    expect(
      resolveTextDisplayValue(resolved, { field: "oee", format: "percent" }).text,
    ).toBe("—");
    const runs = resolveTextBlockDisplayRuns({
      content: "",
      dataSourceId: "src-1",
      contentRuns: [{ text: "?", dataRef: { field: "oee", format: "number" } }],
      resolved,
    });
    expect(runs[0]?.text).toBe("—");
  });

  it("presentationStale impede paint de displayText antigo", () => {
    expect(
      resolveTextDisplayValue(
        {
          ...resolved,
          presentationStale: true,
          displayText: "STALE-99",
        },
        { field: "oee", fallback: "—" },
      ).text,
    ).toBe("—");
  });
});
