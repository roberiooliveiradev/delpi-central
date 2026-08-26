import { useMemo, useState } from "react";
import { Maximize2 } from "lucide-react";
import {
  ChartTypeSegmentToggle,
  ChartViewShell,
  MultiTypeSeriesChart,
  TIME_MULTI_SERIES_TYPES,
  runTabularExport,
  usePersistedChartPreferences,
  type MultiTypeSeriesSpec,
} from "@delpi/plugin-ui/index";

import {
  MaintenanceActionButton,
  MaintenanceSectionHintLabel,
  MaintenanceTabularExportButtons,
} from "../app/maintenanceUi";
import { DM_HELP } from "../content/helpTooltips";
import type { ReposicaoItem } from "../data/api/maintenanceApi";
import { buildReposicoesGolpesExportPayload } from "../utils/buildReposicoesGolpesExportPayload";
import { formatCodigoDescricao } from "../utils/pecaOptions";
import { MaintenanceTableLoading } from "./MaintenanceLoadingState";
import { ChartExpandModal } from "./data/ChartExpandModal";

type ReposicoesGolpesChartProps = {
  reposicoes: ReposicaoItem[];
  pecaLabels?: Record<string, string>;
  loading?: boolean;
};

const PECA_LINE_COLORS = [
  "#089bdb",
  "#22c55e",
  "#f59e0b",
  "#a855f7",
  "#ef4444",
  "#06b6d4",
  "#eab308",
  "#ec4899",
];

const CHART_STORAGE_KEY = "maintenance:reposicoes-golpes:chart:v1";
const INLINE_CHART_HEIGHT = 320;
const EXPANDED_CHART_HEIGHT = 560;

function formatEventLabel(value: string): string {
  return new Date(value).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatGolpes(value: number): string {
  return value.toLocaleString("pt-BR");
}

export function ReposicoesGolpesChart({
  reposicoes,
  pecaLabels = {},
  loading = false,
}: ReposicoesGolpesChartProps) {
  const [expanded, setExpanded] = useState(false);
  const { chartType, setChartType } = usePersistedChartPreferences({
    storageKey: CHART_STORAGE_KEY,
    defaults: { chartType: "line" },
    allowedChartTypes: TIME_MULTI_SERIES_TYPES,
  });

  const { chartData, series } = useMemo(() => {
    const sorted = [...reposicoes].sort(
      (first, second) =>
        new Date(first.data_reposicao).getTime() - new Date(second.data_reposicao).getTime(),
    );
    const pecas = [...new Set(sorted.map((item) => item.codigo_peca))].sort((a, b) =>
      a.localeCompare(b, "pt-BR"),
    );

    const chartData = sorted.map((item) => {
      const row: Record<string, string | number | null> = {
        label: formatEventLabel(item.data_reposicao),
        eventId: item.reposicao_id,
      };
      for (const peca of pecas) {
        row[peca] = item.codigo_peca === peca ? item.golpes : null;
      }
      return row;
    });

    const series: MultiTypeSeriesSpec[] = pecas.map((codigo, index) => ({
      dataKey: codigo,
      name: pecaLabels[codigo] ? formatCodigoDescricao(codigo, pecaLabels[codigo]) : codigo,
      fill: PECA_LINE_COLORS[index % PECA_LINE_COLORS.length],
    }));

    return { chartData, series };
  }, [pecaLabels, reposicoes]);

  const hasChart = !loading && chartData.length > 0 && series.length > 0;

  const exportPayload = useMemo(
    () => buildReposicoesGolpesExportPayload(reposicoes, pecaLabels),
    [pecaLabels, reposicoes],
  );

  const chartShell = (height: number) => (
    <ChartViewShell
      prefix="dm"
      typeToggleLabel="Tipo de gráfico"
      typeToggle={
        <ChartTypeSegmentToggle
          family="time_multi_series"
          value={chartType}
          onChange={setChartType}
          idPrefix="reposicoes-golpes-type"
          prefix="dm"
          portalScopeClassName="dashboard-maintenance"
        />
      }
      exportActions={
        <MaintenanceTabularExportButtons
          compact
          disabled={!hasChart}
          onExport={(format) => {
            runTabularExport({
              kind: "table",
              format,
              payload: exportPayload,
            });
          }}
        />
      }
    >
      {loading ? (
        <MaintenanceTableLoading titleKey="grafico" variant="compact" />
      ) : hasChart ? (
        <MultiTypeSeriesChart
          data={chartData}
          categoryKey="label"
          series={series}
          chartType={chartType}
          height={height}
          formatY={formatGolpes}
          formatTooltipValue={formatGolpes}
        />
      ) : null}
    </ChartViewShell>
  );

  const expandAction = hasChart ? (
    <MaintenanceActionButton
      variant="ghost"
      className="dm-chart-section__expand"
      onClick={() => setExpanded(true)}
      aria-label="Expandir gráfico: Golpes por reposição"
    >
      <Maximize2 size={16} aria-hidden="true" />
      Expandir
    </MaintenanceActionButton>
  ) : null;

  return (
    <>
      <section className="dm-card dm-chart-section">
        <div className="dm-section-header">
          <div className="dm-section-header__title-group">
            <h3 className="dm-section-header__title">
              <MaintenanceSectionHintLabel
                label="Golpes por reposição"
                hint={DM_HELP.miniAplicadores.chartGolpes}
              />
            </h3>
          </div>
          <div className="dm-section-header__meta">{expandAction}</div>
        </div>

        {chartShell(INLINE_CHART_HEIGHT)}
      </section>

      {hasChart ? (
        <ChartExpandModal
          open={expanded}
          title="Golpes por reposição"
          onClose={() => setExpanded(false)}
        >
          {chartShell(EXPANDED_CHART_HEIGHT)}
        </ChartExpandModal>
      ) : null}
    </>
  );
}
