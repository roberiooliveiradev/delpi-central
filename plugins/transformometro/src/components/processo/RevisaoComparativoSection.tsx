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
import { HelpTooltip } from "@delpi/plugin-ui/index";
import { SegmentToggle } from "../SegmentToggle";
import { CollapsiblePanel } from "../CollapsiblePanel";
import { BeneficioCalculoChip } from "../BeneficioCalculoChip";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { ProcessoComparativoItem } from "../../data/api/transformometroApi";
import { formatCurrency, formatHours } from "../../utils/format";
import {
  COMPARATIVO_HOURS_SERIES,
  COMPARATIVO_MONEY_SERIES,
  collectComparativoAvisos,
  collectComparativoCategorias,
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
  const avisos = useMemo(() => collectComparativoAvisos(items), [items]);
  const categorias = useMemo(() => collectComparativoCategorias(items), [items]);
  const moneySeries = useMemo(() => {
    const hasCapacidade = chartRows.some((row) => row.ganhoCapacidade > 0);
    if (hasCapacidade) return COMPARATIVO_MONEY_SERIES;
    return COMPARATIVO_MONEY_SERIES.filter((entry) => entry.key !== "ganhoCapacidade");
  }, [chartRows]);
  const series = view === "money" ? moneySeries : COMPARATIVO_HOURS_SERIES;

  const formatValue = view === "money" ? formatCurrency : formatHours;
  const formatAxis = view === "money" ? formatAxisMoney : (value: number) => formatHours(value);

  return (
    <section className="tm-comparativo-section">
      {categorias.length > 0 ? (
        <p
          className="ds-hint"
          style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}
        >
          <span>Categorias neste comparativo:</span>
          {categorias.map((categoria) => (
            <BeneficioCalculoChip key={categoria} value={categoria} />
          ))}
        </p>
      ) : null}
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

      {avisos.length > 0 ? (
        <div className="ds-card" role="status">
          <p className="ds-section-title" style={{ marginBottom: 8 }}>
            Avisos de volume
            <HelpTooltip
              content={TM_HELP_TOOLTIPS.revisao.comparativoAvisos}
              ariaLabel="Ajuda: avisos de volume no comparativo"
            />
          </p>
          <ul className="ds-hint" style={{ margin: 0, paddingLeft: "1.25rem" }}>
            {avisos.map((aviso, index) => (
              <li key={`${aviso.revisaoLabel}-${index}`}>
                <strong>{aviso.revisaoLabel}:</strong> {aviso.message}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

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
          columnPreferencesKey="transformometro:RevisaoComparativoSection:revisaocomparativosection:v3"
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
