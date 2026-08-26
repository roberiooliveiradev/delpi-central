import { ExternalLink, Hammer, Package, PlusCircle } from "lucide-react";
import { useMemo } from "react";
import {
  ChartTypeSegmentToggle,
  ChartViewShell,
  MultiTypeSeriesChart,
  RANKING_TYPES,
  TIME_MULTI_SERIES_TYPES,
  usePersistedChartPreferences,
  type MultiTypeSeriesSpec,
} from "@delpi/plugin-ui/index";

import { MaintenanceActionButton, MaintenanceSectionHintLabel } from "../app/maintenanceUi";
import { DM_HELP } from "../content/helpTooltips";
import { MaintenanceTableLoading } from "./MaintenanceLoadingState";
import { StateBox, StatusBadge } from "./data";
import { MAINTENANCE_ROUTES } from "../constants/routes";
import type { FerramentaItem, PreventivaAlerta, PreventivaHistoricoItem } from "../data/api/maintenanceApi";

export type PreventivaDetailData = {
  alerta: PreventivaAlerta | null;
  ferramenta: FerramentaItem | null;
  pecaDescricao: string | null;
  estoqueLocal01: number | null;
  historico: PreventivaHistoricoItem[];
};

type PreventivaDetailPanelProps = {
  codigoFerramenta: string;
  codigoPeca: string;
  data: PreventivaDetailData | null;
  loading: boolean;
  layout?: "sidebar" | "page";
  onNavigate: (path: string) => void;
  onClose: () => void;
};

const USO_CHART_STORAGE_KEY = "maintenance:preventiva-uso:chart:v1";
const HISTORICO_CHART_STORAGE_KEY = "maintenance:preventiva-historico:chart:v1";
const USO_CHART_HEIGHT = 240;
const HISTORICO_CHART_HEIGHT = 280;

function formatDate(value: string | undefined): string {
  if (!value) return "—";
  return new Date(value).toLocaleString("pt-BR");
}

function formatNumber(value: number | undefined | null): string {
  if (value === undefined || value === null || Number.isNaN(value)) return "—";
  return value.toLocaleString("pt-BR");
}

function statusAccent(status: string | undefined): string {
  if (status === "CRÍTICO") return "#ef4444";
  if (status === "ATENÇÃO") return "#f59e0b";
  if (status === "OK") return "#22c55e";
  return "var(--dm-accent, #089bdb)";
}

export function PreventivaDetailPanel({
  codigoFerramenta,
  codigoPeca,
  data,
  loading,
  layout = "sidebar",
  onNavigate,
  onClose,
}: PreventivaDetailPanelProps) {
  const isPage = layout === "page";
  const hasSelection = Boolean(codigoFerramenta && codigoPeca);
  const alerta = data?.alerta;
  const ferramenta = data?.ferramenta;

  const { chartType: usoChartType, setChartType: setUsoChartType } = usePersistedChartPreferences({
    storageKey: USO_CHART_STORAGE_KEY,
    defaults: { chartType: "bar" },
    allowedChartTypes: RANKING_TYPES,
  });

  const { chartType: historicoChartType, setChartType: setHistoricoChartType } =
    usePersistedChartPreferences({
      storageKey: HISTORICO_CHART_STORAGE_KEY,
      defaults: { chartType: "line" },
      allowedChartTypes: TIME_MULTI_SERIES_TYPES,
    });

  const historicoChart = useMemo(
    () =>
      (data?.historico ?? []).map((row) => ({
        label: new Date(row.data_reposicao).toLocaleDateString("pt-BR", {
          day: "2-digit",
          month: "short",
          year: "2-digit",
        }),
        golpes: row.golpes,
      })),
    [data?.historico],
  );

  const usageChart = useMemo(
    () =>
      alerta && alerta.media_golpes > 0
        ? [
            {
              name: "Golpes atuais",
              value: alerta.golpes_atuais,
              fill: statusAccent(alerta.status),
            },
            {
              name: "Média histórica",
              value: Math.round(alerta.media_golpes),
              fill: "color-mix(in srgb, var(--dm-accent) 55%, #94a3b8)",
            },
          ]
        : [],
    [alerta],
  );

  const historicoSeries = useMemo<MultiTypeSeriesSpec[]>(
    () => [
      {
        dataKey: "golpes",
        name: "Golpes por ciclo",
        fill: "var(--dm-accent, #089bdb)",
        trendSource: true,
      },
    ],
    [],
  );

  const usoSeries = useMemo<MultiTypeSeriesSpec[]>(
    () => [
      {
        dataKey: "value",
        name: "Golpes",
        fill: "var(--dm-accent, #089bdb)",
      },
    ],
    [],
  );

  const RootTag = isPage ? "section" : "aside";

  return (
    <RootTag
      className={`dm-detail-panel${hasSelection ? " is-active" : ""}${isPage ? " dm-detail-panel--page" : ""}`}
      aria-live="polite"
    >
      {hasSelection ? (
        <div className="dm-detail-panel__header">
          <div>
            {!isPage ? <p className="dm-eyebrow">Detalhe preventivo</p> : null}
            <h3 className="dm-detail-panel__title">
              {codigoFerramenta} / {codigoPeca}
            </h3>
          </div>
          <MaintenanceActionButton
            variant="ghost"
            className="dm-detail-panel__close"
            onClick={onClose}
          >
            {isPage ? "Voltar à lista" : "Fechar"}
          </MaintenanceActionButton>
        </div>
      ) : (
        <div className="dm-detail-panel__header">
          <div>
            {!isPage ? <p className="dm-eyebrow">Painel de detalhes</p> : null}
            <h3 className="dm-detail-panel__title">Selecione um item</h3>
          </div>
        </div>
      )}

      {!hasSelection ? (
        <StateBox>
          Selecione um alerta ou reposição nas abas anteriores para ver detalhes, gráficos e
          estoque.
        </StateBox>
      ) : null}

      {hasSelection && loading ? (
        <div className="dm-detail-panel__loading">
          <MaintenanceTableLoading titleKey="detalhe" variant="panel" />
        </div>
      ) : null}

      {hasSelection && !loading && data ? (
        <div className="dm-detail-panel__body dm-content-transition">
          <div className="dm-detail-panel__identity">
            <button
              type="button"
              className="dm-detail-panel__link"
              onClick={() => onNavigate(MAINTENANCE_ROUTES.miniAplicadorDetail(codigoFerramenta))}
            >
              <Hammer size={16} aria-hidden="true" />
              <span>
                {ferramenta
                  ? `${ferramenta.codigo} — ${ferramenta.descricao}`
                  : codigoFerramenta}
              </span>
              <ExternalLink size={14} aria-hidden="true" />
            </button>
            <p className="dm-detail-panel__meta">
              <Package size={14} aria-hidden="true" />
              Peça: {codigoPeca}
              {data.pecaDescricao ? ` — ${data.pecaDescricao}` : ""}
            </p>
          </div>

          {alerta ? (
            <div className="dm-detail-metrics">
              <div className="dm-detail-metric">
                <span>Status</span>
                <StatusBadge status={alerta.status} />
              </div>
              <div className="dm-detail-metric">
                <span>% de uso</span>
                <strong>{alerta.percentual_uso.toLocaleString("pt-BR")}%</strong>
              </div>
              <div className="dm-detail-metric">
                <span>Golpes atuais</span>
                <strong>{formatNumber(alerta.golpes_atuais)}</strong>
              </div>
              <div className="dm-detail-metric">
                <span>Média histórica</span>
                <strong>{formatNumber(alerta.media_golpes)}</strong>
              </div>
              <div className="dm-detail-metric">
                <span>Última reposição</span>
                <strong>{formatDate(alerta.data_ultima_reposicao)}</strong>
              </div>
              <div className="dm-detail-metric">
                <span>Estoque peça (01)</span>
                <strong>{formatNumber(data.estoqueLocal01)}</strong>
              </div>
            </div>
          ) : (
            <StateBox>Sem dados preventivos para este par — registre reposições para calcular alertas.</StateBox>
          )}

          {usageChart.length > 0 ? (
            <section className="dm-card dm-chart-section">
              <div className="dm-section-header">
                <div className="dm-section-header__title-group">
                  <h3 className="dm-section-header__title">
                    <MaintenanceSectionHintLabel
                      label="Uso vs. média"
                      hint={DM_HELP.preventivaDetalhe.comparativo}
                    />
                  </h3>
                </div>
              </div>
              <ChartViewShell
                prefix="dm"
                typeToggleLabel="Tipo de gráfico"
                typeToggle={
                  <ChartTypeSegmentToggle
                    family="ranking"
                    value={usoChartType}
                    onChange={setUsoChartType}
                    idPrefix="preventiva-uso-type"
                    prefix="dm"
                    portalScopeClassName="dashboard-maintenance"
                  />
                }
              >
                <MultiTypeSeriesChart
                  data={usageChart}
                  categoryKey="name"
                  series={usoSeries}
                  chartType={usoChartType}
                  height={USO_CHART_HEIGHT}
                  formatY={formatNumber}
                  formatTooltipValue={formatNumber}
                  categoryFillKey="fill"
                />
              </ChartViewShell>
            </section>
          ) : null}

          <section className="dm-card dm-chart-section">
            <div className="dm-section-header">
              <div className="dm-section-header__title-group">
                <h3 className="dm-section-header__title">
                  <MaintenanceSectionHintLabel
                    label="Histórico de golpes entre reposições"
                    hint={DM_HELP.preventivaDetalhe.historicoGolpes}
                  />
                </h3>
              </div>
              {historicoChart.length > 0 ? (
                <div className="dm-section-header__meta">
                  <span className="dm-badge">{historicoChart.length} trocas</span>
                </div>
              ) : null}
            </div>
            {historicoChart.length > 0 ? (
              <ChartViewShell
                prefix="dm"
                typeToggleLabel="Tipo de gráfico"
                typeToggle={
                  <ChartTypeSegmentToggle
                    family="time_multi_series"
                    value={historicoChartType}
                    onChange={setHistoricoChartType}
                    idPrefix="preventiva-historico-type"
                    prefix="dm"
                    portalScopeClassName="dashboard-maintenance"
                  />
                }
              >
                <MultiTypeSeriesChart
                  data={historicoChart}
                  categoryKey="label"
                  series={historicoSeries}
                  chartType={historicoChartType}
                  height={HISTORICO_CHART_HEIGHT}
                  showTrend
                  formatY={formatNumber}
                  formatTooltipValue={formatNumber}
                />
              </ChartViewShell>
            ) : (
              <StateBox>Nenhuma reposição registrada para este par.</StateBox>
            )}
          </section>

          <div className="dm-detail-panel__actions">
            <MaintenanceActionButton
              variant="primary"
              onClick={() => onNavigate(MAINTENANCE_ROUTES.miniAplicadorDetail(codigoFerramenta))}
            >
              <ExternalLink size={16} />
              Abrir ferramenta
            </MaintenanceActionButton>
            <MaintenanceActionButton
              variant="ghost"
              onClick={() => onNavigate(MAINTENANCE_ROUTES.miniAplicadorDetail(codigoFerramenta))}
            >
              <PlusCircle size={16} />
              Nova reposição
            </MaintenanceActionButton>
          </div>
        </div>
      ) : null}
    </RootTag>
  );
}
