import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { DataTableColumn } from "../DataTable";
import { DataTableSection } from "../DataTableSection";
import { ChartCard } from "../ChartCard";
import { HelpTooltip } from "@delpi/plugin-ui";
import { SegmentToggle } from "../SegmentToggle";
import { CollapsiblePanel } from "../CollapsiblePanel";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { ProcessoComparativoItem } from "../../data/api/transformometroApi";
import { formatCurrency, formatHours } from "../../utils/format";
import {
  COMPARATIVO_HOURS_SERIES,
  COMPARATIVO_MONEY_SERIES,
  toComparativoChartRows,
  type ComparativoChartView,
} from "../../utils/revisaoComparativoChart";

type Props = {
  items: ProcessoComparativoItem[];
  columns: DataTableColumn<ProcessoComparativoItem>[];
};

const CHART_HEIGHT = 320;

function formatAxisMoney(value: number): string {
  if (Math.abs(value) >= 1_000_000) {
    return `R$ ${(value / 1_000_000).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}M`;
  }
  if (Math.abs(value) >= 1_000) {
    return `R$ ${(value / 1_000).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}k`;
  }
  return formatCurrency(value);
}

export function RevisaoComparativoSection({ items, columns }: Props) {
  const [view, setView] = useState<ComparativoChartView>("money");
  const chartRows = useMemo(() => toComparativoChartRows(items), [items]);
  const series = view === "money" ? COMPARATIVO_MONEY_SERIES : COMPARATIVO_HOURS_SERIES;

  const formatValue = view === "money" ? formatCurrency : formatHours;
  const formatAxis = view === "money" ? formatAxisMoney : (value: number) => formatHours(value);

  return (
    <section className="tm-comparativo-section">
      <ChartCard
        title="Comparativo de revisões"
        hint={TM_HELP_TOOLTIPS.revisao.comparativoChart}
        toolbar={
          <SegmentToggle
            ariaLabel="Visão do comparativo de revisões"
            idPrefix="tm-comparativo-view"
            value={view}
            onChange={setView}
            options={[
              {
                value: "money",
                label: "Valores (R$)",
              },
              {
                value: "hours",
                label: "Horas",
              },
            ]}
          />
        }
      >
        <div className="tm-comparativo-chart">
          <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
            <BarChart
              data={chartRows}
              margin={{ top: 8, right: 12, left: 4, bottom: 8 }}
              barCategoryGap={view === "money" ? "18%" : "28%"}
              barGap={4}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="var(--ds-card-border)" />
              <XAxis
                dataKey="label"
                tick={{ fill: "var(--ds-text)", fontSize: 12 }}
                interval={0}
              />
              <YAxis tick={{ fill: "var(--ds-text-muted)", fontSize: 12 }} tickFormatter={formatAxis} />
              <Tooltip
                formatter={(value, name) => [formatValue(Number(value)), String(name)]}
                contentStyle={{
                  background: "var(--ds-card-bg)",
                  border: "1px solid var(--ds-card-border)",
                  borderRadius: 10,
                  color: "var(--ds-text)",
                }}
                labelStyle={{ color: "var(--ds-text)", fontWeight: 600 }}
              />
              <Legend
                wrapperStyle={{ color: "var(--ds-text-muted)", fontSize: 12, paddingTop: 8 }}
              />
              {series.map((entry) => (
                <Bar
                  key={entry.key}
                  dataKey={entry.key}
                  name={entry.label}
                  fill={entry.color}
                  radius={[6, 6, 0, 0]}
                  maxBarSize={view === "money" ? 42 : 56}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </ChartCard>

      <CollapsiblePanel
        className="tm-comparativo-table"
        defaultOpen={false}
        header={
          <span className="tm-comparativo-table__trigger">
            Ver tabela detalhada
            <HelpTooltip
              content={TM_HELP_TOOLTIPS.revisao.comparativoTable}
              ariaLabel="Ajuda: tabela detalhada do comparativo"
            />
            <span className="ds-muted tm-comparativo-table__count">{items.length} registro(s)</span>
          </span>
        }
        bodyClassName="tm-comparativo-table__body"
      >
        <DataTableSection
          title=""
          columns={columns}
          rows={items}
          rowKey={(row) => row.revisao_id}
          hideSearch
          pageSize={10}
          emptyMessage=""
          embedded
        />
      </CollapsiblePanel>
    </section>
  );
}
