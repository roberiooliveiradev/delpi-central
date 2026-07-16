export type DataRouteDisplayKind = "kpi" | "series" | "table";

export type DataRoutePreviewMetric = { label: string; value: string };

export type DataRoutePreviewPayload = {
  kind: DataRouteDisplayKind;
  title?: string;
  kpi?: DataRoutePreviewMetric;
  /** Resumo com várias métricas (rotas `*_summary` / valueFields). */
  metrics?: DataRoutePreviewMetric[];
  table?: {
    columns: Array<{ key: string; label: string }>;
    rows: Array<Record<string, string | number>>;
  };
  series?: { points: Array<{ label: string; value: number }> };
  /**
   * Fatias extras do mesmo resolved (KPI/tabela/série) para preview triplo.
   * Não inclui a fatia já refletida em kind + campos principais.
   */
  extraSlices?: Array<{
    kind: DataRouteDisplayKind;
    kpi?: DataRoutePreviewMetric;
    metrics?: DataRoutePreviewMetric[];
    table?: DataRoutePreviewPayload["table"];
    series?: DataRoutePreviewPayload["series"];
  }>;
  error?: string;
  source: "sample" | "live";
};

const SAMPLE_MAX_ROWS = 4;
const LIVE_MAX_ROWS = 5;
const LIVE_MAX_METRICS = 6;

/** Exemplo estático tipado — sem chamada HTTP. */
export function buildSampleDataRoutePreview(input: {
  id: string;
  label: string;
  kind: DataRouteDisplayKind;
  /** When true (or metaShape scalar/summary), shows multi-metric summary sample. */
  kpiSummary?: boolean;
}): DataRoutePreviewPayload {
  const title = input.label || input.id;
  const { kind } = input;

  if (kind === "kpi") {
    if (input.kpiSummary) {
      return {
        kind: "kpi",
        title,
        source: "sample",
        metrics: [
          { label: "Total", value: "128" },
          { label: "% no prazo", value: "87,4%" },
          { label: "Lead time", value: "3,2" },
        ],
        kpi: { label: "Total", value: "128" },
      };
    }
    return {
      kind: "kpi",
      title,
      source: "sample",
      kpi: { label: title, value: "87,4%" },
    };
  }

  if (kind === "series") {
    return {
      kind: "series",
      title,
      source: "sample",
      series: {
        points: [
          { label: "Seg", value: 72 },
          { label: "Ter", value: 78 },
          { label: "Qua", value: 81 },
          { label: "Qui", value: 76 },
          { label: "Sex", value: 88 },
        ],
      },
    };
  }

  return {
    kind: "table",
    title,
    source: "sample",
    table: {
      columns: [
        { key: "code", label: "Código" },
        { key: "name", label: "Descrição" },
        { key: "value", label: "Valor" },
      ],
      rows: [
        { code: "A-01", name: "Exemplo Alfa", value: 12 },
        { code: "B-02", name: "Exemplo Beta", value: 8 },
        { code: "C-03", name: "Exemplo Gama", value: 21 },
        { code: "D-04", name: "Exemplo Delta", value: 5 },
      ].slice(0, SAMPLE_MAX_ROWS),
    },
  };
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function formatCell(value: unknown): string | number {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "boolean") return value ? "sim" : "não";
  if (value == null) return "—";
  if (typeof value === "object") {
    try {
      return JSON.stringify(value);
    } catch {
      return "—";
    }
  }
  return String(value);
}

function formatKpiValue(value: unknown): string {
  if (typeof value === "number" && Number.isFinite(value)) {
    return new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 }).format(value);
  }
  if (value == null || value === "") return "—";
  return String(value);
}

function mapSeriesPoints(chartPoints: unknown[]): DataRoutePreviewPayload["series"] {
  const points = chartPoints.slice(0, LIVE_MAX_ROWS).map((point, index) => {
    const row = asRecord(point) ?? {};
    const label = String(row.label ?? row.x ?? row.date ?? `P${index + 1}`);
    const value = Number(row.value ?? row.y ?? 0);
    return { label, value: Number.isFinite(value) ? value : 0 };
  });
  return { points };
}

function mapTableRows(
  table: Record<string, unknown> | null,
  rowsRaw: unknown[],
): DataRoutePreviewPayload["table"] | null {
  if (rowsRaw.length === 0) return null;
  const columnsExplicit = Array.isArray(table?.columns) ? table.columns : [];
  const first = asRecord(rowsRaw[0]) ?? {};
  const columns =
    columnsExplicit.length > 0
      ? (columnsExplicit
          .map((column) => {
            const row = asRecord(column) ?? {};
            const key = String(row.key ?? row.field ?? "").trim();
            return key ? { key, label: String(row.label ?? key) } : null;
          })
          .filter(Boolean) as Array<{ key: string; label: string }>)
      : Object.keys(first)
          .slice(0, 4)
          .map((key) => ({ key, label: key }));

  if (columns.length === 0) return null;

  const rows = rowsRaw.slice(0, LIVE_MAX_ROWS).map((row) => {
    const record = asRecord(row) ?? {};
    const next: Record<string, string | number> = {};
    for (const column of columns) {
      next[column.key] = formatCell(record[column.key]);
    }
    return next;
  });

  return { columns, rows };
}

function mapKpiMetricList(
  kpiMetrics: unknown[],
  title: string | undefined,
): DataRoutePreviewMetric[] {
  return kpiMetrics.slice(0, LIVE_MAX_METRICS).map((metric, index) => {
    const row = asRecord(metric) ?? {};
    const fallback = index === 0 && title ? title : `Métrica ${index + 1}`;
    return {
      label: String(row.label ?? row.field ?? fallback),
      value: formatKpiValue(row.value),
    };
  });
}

/**
 * Converte `block.resolved` do preview-block (tv-dashboard-api) para o payload do catálogo.
 * Prioriza `preferred`, mas anexa as demais fatias disponíveis (preview triplo).
 */
export function mapEnrichedBlockToDataRoutePreview(
  block: Record<string, unknown>,
  preferred: DataRouteDisplayKind,
): DataRoutePreviewPayload {
  const resolved = asRecord(block.resolved);
  if (!resolved) {
    return {
      kind: preferred,
      source: "live",
      error: "Resposta sem dados resolvidos.",
    };
  }

  const error =
    (typeof resolved.error === "string" && resolved.error.trim()) ||
    (typeof resolved.detail === "string" && resolved.detail.trim()) ||
    "";
  if (error) {
    return { kind: preferred, source: "live", error };
  }

  const title =
    (typeof resolved.label === "string" && resolved.label.trim()) ||
    (typeof block.dataBinding === "object" &&
      block.dataBinding &&
      typeof (block.dataBinding as { label?: unknown }).label === "string" &&
      String((block.dataBinding as { label: string }).label).trim()) ||
    undefined;

  const chart = asRecord(resolved.chart);
  const chartPoints = Array.isArray(chart?.points) ? chart.points : [];
  const table = asRecord(resolved.table);
  const rowsRaw = Array.isArray(table?.rows) ? table.rows : [];
  const kpi = asRecord(resolved.kpi);
  const kpiMetrics = Array.isArray(resolved.kpiMetrics) ? resolved.kpiMetrics : [];

  const metricsList = mapKpiMetricList(kpiMetrics, title);
  const mappedTable = mapTableRows(table, rowsRaw);
  const mappedSeries = chartPoints.length > 0 ? mapSeriesPoints(chartPoints) : undefined;

  const slices: NonNullable<DataRoutePreviewPayload["extraSlices"]> = [];
  if (metricsList.length > 1) {
    slices.push({ kind: "kpi", metrics: metricsList, kpi: metricsList[0] });
  } else if (metricsList.length === 1) {
    slices.push({ kind: "kpi", kpi: metricsList[0] });
  } else if (kpi?.value != null || typeof kpi?.label === "string") {
    slices.push({
      kind: "kpi",
      kpi: {
        label: String(kpi.label ?? title ?? "KPI"),
        value: formatKpiValue(kpi.value),
      },
    });
  }
  if (mappedTable) slices.push({ kind: "table", table: mappedTable });
  if (mappedSeries) slices.push({ kind: "series", series: mappedSeries });

  const pickPreferred = (): DataRoutePreviewPayload | null => {
    if (preferred === "series") {
      if (mappedSeries) {
        return { kind: "series", title, source: "live", series: mappedSeries };
      }
      if (mappedTable) {
        return { kind: "table", title, source: "live", table: mappedTable };
      }
      return {
        kind: "series",
        title,
        source: "live",
        error: "A rota não retornou pontos de série neste teste.",
      };
    }

    if (preferred === "table") {
      if (mappedTable) {
        return { kind: "table", title, source: "live", table: mappedTable };
      }
      if (metricsList.length > 1) {
        return {
          kind: "kpi",
          title,
          source: "live",
          metrics: metricsList,
          kpi: metricsList[0],
        };
      }
      if (metricsList.length === 1) {
        return { kind: "kpi", title, source: "live", kpi: metricsList[0] };
      }
      if (kpi?.value != null) {
        return {
          kind: "kpi",
          title,
          source: "live",
          kpi: {
            label: String(kpi.label ?? title ?? "KPI"),
            value: formatKpiValue(kpi.value),
          },
        };
      }
      return {
        kind: "table",
        title,
        source: "live",
        error: "A rota não retornou linhas neste teste.",
      };
    }

    // preferred === "kpi"
    if (metricsList.length > 1) {
      return {
        kind: "kpi",
        title,
        source: "live",
        metrics: metricsList,
        kpi: metricsList[0],
      };
    }
    if (metricsList.length === 1) {
      return { kind: "kpi", title, source: "live", kpi: metricsList[0] };
    }
    // Playbook/listagem: sem métricas de negócio, preferir tabela quando houver.
    if (mappedTable) {
      return { kind: "table", title, source: "live", table: mappedTable };
    }
    if (kpi?.value != null || typeof kpi?.label === "string") {
      return {
        kind: "kpi",
        title,
        source: "live",
        kpi: {
          label: String(kpi.label ?? title ?? "KPI"),
          value: formatKpiValue(kpi.value),
        },
      };
    }
    if (mappedSeries) {
      return { kind: "series", title, source: "live", series: mappedSeries };
    }
    return null;
  };

  const primary = pickPreferred();
  if (!primary || primary.error) {
    return (
      primary ?? {
        kind: preferred,
        title,
        source: "live",
        error: "A rota respondeu, mas sem KPI, tabela ou série reconhecíveis neste preview.",
      }
    );
  }

  const extraSlices = slices.filter((slice) => slice.kind !== primary.kind);
  return extraSlices.length > 0 ? { ...primary, extraSlices } : primary;
}
