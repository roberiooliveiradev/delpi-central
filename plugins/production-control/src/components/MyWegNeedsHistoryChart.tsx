import { CHART_COLORS_DEPARTMENTAL, MultiTypeSeriesChart } from "@delpi/plugin-ui/index";
import { useMemo } from "react";

import { ChartCard } from "./ChartCard";
import { copy } from "../content/copy";
import type { MyWegNeedsBatchSummary } from "../types";
import { formatDecimalString } from "../utils/formatDecimalString";

type Props = {
  items: MyWegNeedsBatchSummary[];
  selectedBatchId: string | null;
  latestBatchId: string | null;
  onSelectBatch: (batchId: string) => void;
};

const texts = copy.mywegNeeds;
const CHART_HEIGHT = 220;
const MAX_BARS = 8;
const ACTIVE_FILL = "var(--ppc-title, #003866)";
const IDLE_FILL =
  CHART_COLORS_DEPARTMENTAL[5] ??
  "color-mix(in srgb, var(--ppc-accent, #089bdb) 42%, white)";

function formatAxisDate(value: string | null | undefined): string {
  const text = (value ?? "").trim();
  if (/^\d{4}-\d{2}-\d{2}/.test(text)) {
    const [, m, d] = text.slice(0, 10).split("-");
    return `${d}/${m}`;
  }
  return text || "—";
}

function parseTotalUn(value: string | null | undefined): number {
  const raw = (value ?? "").trim();
  if (!raw) return 0;
  const n = Number(raw);
  return Number.isFinite(n) ? n : 0;
}

export function MyWegNeedsHistoryChart({
  items,
  selectedBatchId,
  latestBatchId,
  onSelectBatch,
}: Props) {
  const chronological = useMemo(() => {
    return [...items]
      .sort((a, b) => {
        const aKey = a.collectedAt || a.collectionDate || "";
        const bKey = b.collectedAt || b.collectionDate || "";
        return aKey < bKey ? -1 : aKey > bKey ? 1 : 0;
      })
      .slice(-MAX_BARS);
  }, [items]);

  const chartRows = useMemo(() => {
    return chronological.map((batch, index) => {
      const labelBase = formatAxisDate(batch.collectionDate || batch.collectedAt);
      const duplicate =
        chronological.filter(
          (other) =>
            formatAxisDate(other.collectionDate || other.collectedAt) === labelBase,
        ).length > 1;
      const label = duplicate ? `${labelBase}·${index + 1}` : labelBase;
      const selected = batch.id === selectedBatchId;
      return {
        label,
        batchId: batch.id,
        totalUn: parseTotalUn(batch.totals?.quantidade_original_un),
        fill: selected ? ACTIVE_FILL : IDLE_FILL,
      };
    });
  }, [chronological, selectedBatchId]);

  const labelToBatchId = useMemo(() => {
    const map = new Map<string, string>();
    for (const row of chartRows) map.set(row.label, row.batchId);
    return map;
  }, [chartRows]);

  return (
    <ChartCard
      title={texts.historyLabel}
      hint={texts.historyHint}
      className="ppc-myweg-needs__history-card"
    >
      {chartRows.length === 0 ? (
        <p className="ppc-myweg-needs__history-empty" role="status">
          {texts.historyEmpty}
        </p>
      ) : (
        <>
          <div className="ppc-myweg-needs__history-chart" aria-hidden="true">
            <MultiTypeSeriesChart
              data={chartRows}
              categoryKey="label"
              categoryFillKey="fill"
              series={[
                {
                  dataKey: "totalUn",
                  name: texts.historySeries,
                  fill: IDLE_FILL,
                },
              ]}
              chartType="column"
              height={CHART_HEIGHT}
              showLegend={false}
              showValueLabels
              formatY={(value) => formatDecimalString(String(Math.round(value)))}
              formatTooltipValue={(value) =>
                `${formatDecimalString(String(Math.round(value)))} UN`
              }
              onCategoryClick={(category) => {
                const batchId = labelToBatchId.get(category);
                if (batchId) onSelectBatch(batchId);
              }}
              margin={{ top: 28, right: 8, left: 0, bottom: 4 }}
            />
          </div>
          <label className="ppc-myweg-needs__history-select">
            <span className="ppc-sr-only">{texts.historyAria}</span>
            <select
              value={selectedBatchId ?? ""}
              onChange={(event) => {
                if (event.target.value) onSelectBatch(event.target.value);
              }}
              aria-label={texts.historyAria}
            >
              {chronological.map((batch) => (
                <option key={batch.id} value={batch.id}>
                  {formatAxisDate(batch.collectionDate || batch.collectedAt)}
                  {latestBatchId === batch.id ? ` — ${texts.latestBadge}` : ""}
                  {` (${batch.recordCount.toLocaleString("pt-BR")})`}
                </option>
              ))}
            </select>
          </label>
        </>
      )}
    </ChartCard>
  );
}
