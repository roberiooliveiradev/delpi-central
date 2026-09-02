import { useMemo, useState } from "react";
import { Maximize2 } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { EF_GHOST_BTN } from "../ui/ghostChrome";
import { EF_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  AXIS_TICK,
  CHART_COLORS,
  CHART_EXPANDED_HEIGHT,
  CHART_HEIGHT,
  TOOLTIP_STYLE,
} from "../constants/chartTheme";
import type { UnproductiveHoursRankingItem } from "../types/unproductiveHours";
import { resolveRankingHours } from "../types/unproductiveHours";
import { formatHours } from "../utils/format";
import { ChartCard } from "./ChartCard";
import { ChartModal } from "./ChartModal";

type UnproductiveHoursChartsProps = {
  byStopReason: UnproductiveHoursRankingItem[];
  byOperator: UnproductiveHoursRankingItem[];
  byResource: UnproductiveHoursRankingItem[];
};

type ExpandedChartKey = "stopReason" | "operator" | "resource";

function shortLabel(value: string, max = 18): string {
  const trimmed = value.trim();
  if (!trimmed) return "—";
  if (trimmed.length <= max) return trimmed;
  return `${trimmed.slice(0, max - 1)}…`;
}

function stopReasonLabel(item: UnproductiveHoursRankingItem): string {
  const code = item.stop_reason ?? item.motivo ?? "";
  const description = item.stop_reason_description ?? item.motivoDescricao ?? "";
  if (code && description) return `${code} — ${description}`;
  return code || description || "—";
}

function operatorLabel(item: UnproductiveHoursRankingItem): string {
  return item.operator_name ?? item.nomeOperador ?? item.operator_code ?? item.codigoOperador ?? "—";
}

function resourceLabel(item: UnproductiveHoursRankingItem): string {
  return item.resource ?? item.recurso ?? "—";
}

function toChartRows(
  items: UnproductiveHoursRankingItem[],
  labelFn: (item: UnproductiveHoursRankingItem) => string,
) {
  return items.map((item) => {
    const fullLabel = labelFn(item);
    return {
      label: shortLabel(fullLabel),
      fullLabel,
      hours: resolveRankingHours(item),
    };
  });
}

function ExpandChartButton({ onClick }: { onClick: () => void }) {
  return (
    <button type="button" className={EF_GHOST_BTN} onClick={onClick} aria-label="Expandir gráfico">
      <Maximize2 size={16} aria-hidden />
    </button>
  );
}

function RankingBarChart({
  rows,
  height,
}: {
  rows: Array<{ label: string; fullLabel: string; hours: number }>;
  height: number;
}) {
  if (rows.length === 0) {
    return <p className="ef-chart-empty">Sem dados para o período.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={rows} layout="vertical" margin={{ top: 8, right: 24, left: 8, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" tick={AXIS_TICK} />
        <YAxis type="category" dataKey="label" width={120} tick={AXIS_TICK} />
        <Tooltip
          contentStyle={TOOLTIP_STYLE}
          formatter={(value) => formatHours(typeof value === "number" ? value : Number(value))}
          labelFormatter={(_, payload) => {
            const row = payload?.[0]?.payload as { fullLabel?: string } | undefined;
            return row?.fullLabel ?? "";
          }}
        />
        <Bar dataKey="hours" name="Horas" fill={CHART_COLORS.primary} radius={[0, 6, 6, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function UnproductiveHoursCharts({
  byStopReason,
  byOperator,
  byResource,
}: UnproductiveHoursChartsProps) {
  const [expanded, setExpanded] = useState<ExpandedChartKey | null>(null);

  const stopReasonRows = useMemo(
    () => toChartRows(byStopReason, stopReasonLabel),
    [byStopReason],
  );
  const operatorRows = useMemo(() => toChartRows(byOperator, operatorLabel), [byOperator]);
  const resourceRows = useMemo(() => toChartRows(byResource, resourceLabel), [byResource]);

  const expandedTitle =
    expanded === "stopReason"
      ? "Horas por motivo de parada"
      : expanded === "operator"
        ? "Horas por operador"
        : expanded === "resource"
          ? "Horas por recurso"
          : "";

  const expandedRows =
    expanded === "stopReason"
      ? stopReasonRows
      : expanded === "operator"
        ? operatorRows
        : expanded === "resource"
          ? resourceRows
          : [];

  return (
    <section className="ef-charts-grid" aria-label="Rankings de horas improdutivas">
      <div className="ef-charts-grid__row ef-charts-grid__row--3">
        <ChartCard
          title="Por motivo"
          titleHint={EF_HELP_TOOLTIPS.unproductiveHours.charts.byStopReason}
          actions={<ExpandChartButton onClick={() => setExpanded("stopReason")} />}
        >
          <RankingBarChart rows={stopReasonRows} height={CHART_HEIGHT} />
        </ChartCard>
        <ChartCard
          title="Por operador"
          titleHint={EF_HELP_TOOLTIPS.unproductiveHours.charts.byOperator}
          actions={<ExpandChartButton onClick={() => setExpanded("operator")} />}
        >
          <RankingBarChart rows={operatorRows} height={CHART_HEIGHT} />
        </ChartCard>
        <ChartCard
          title="Por recurso"
          titleHint={EF_HELP_TOOLTIPS.unproductiveHours.charts.byResource}
          actions={<ExpandChartButton onClick={() => setExpanded("resource")} />}
        >
          <RankingBarChart rows={resourceRows} height={CHART_HEIGHT} />
        </ChartCard>
      </div>

      <ChartModal
        open={expanded !== null}
        title={expandedTitle}
        onClose={() => setExpanded(null)}
      >
        <RankingBarChart rows={expandedRows} height={CHART_EXPANDED_HEIGHT} />
      </ChartModal>
    </section>
  );
}
