import {
  ClearFiltersButton,
  DataTable,
  DrawerShell,
  EmptyState,
  HelpTooltip,
  LoadingState,
  StatusBadge,
  createCompactPagination,
  dataTableBemClasses,
  drawerShellBemClasses,
  emptyStatePanelBemClasses,
  loadingStatePanelBemClasses,
  statusBadgeBemClasses,
} from "@delpi/plugin-ui/index";
import { RefreshCw } from "lucide-react";
import { useMemo, useState } from "react";

import { DowntimeAnalyticsSection } from "../components/downtimes/DowntimeAnalyticsSection";
import type { BranchCode } from "../constants/routes";
import { DELPI_MES_COPY } from "../content/copy";
import type { DowntimesRouteParams } from "../hooks/useDelpiMesRoute";
import { useDowntimeAnalytics } from "../hooks/useDowntimeAnalytics";
import { useDowntimeFilterOptions } from "../hooks/useDowntimeFilterOptions";
import { useDowntimesData } from "../hooks/useDowntimesData";
import { useSelectedDowntime } from "../hooks/useSelectedDowntime";
import { useServerClock } from "../hooks/useServerClock";
import { useWorkCenterTimeline } from "../hooks/useWorkCenterTimeline";
import type { DowntimeAnalyticsReasonGroup, DowntimeItem } from "../types/mes";
import {
  MES_BUSINESS_TIMEZONE,
  businessDayKey,
  formatBusinessClock,
  presentDayEvent,
} from "../utils/dayTimeline";
import {
  PENDING_REASON_GROUP_KEY,
  buildDowntimeAnalyticsQuery,
} from "../utils/downtimeAnalyticsPresentation";
import {
  DOWNTIME_PERIOD_PRESETS,
  buildDowntimesQuery,
  downtimeDurationSeconds,
  downtimeSourceLabel,
  downtimeStatusLabel,
  formatDateTime,
  hasActiveDowntimeFilters,
} from "../utils/downtimesPresentation";
import { formatDuration } from "../utils/duration";

const loadingClasses = loadingStatePanelBemClasses("delpi-mes");
const emptyClasses = emptyStatePanelBemClasses("delpi-mes");
const tableClasses = dataTableBemClasses("delpi-mes");
const drawerClasses = drawerShellBemClasses("delpi-mes");
const badgeClasses = statusBadgeBemClasses("delpi-mes");

const Pagination = createCompactPagination({
  prefix: "delpi-mes",
  layout: "flat",
  labels: {
    info: ({ page, totalPages, total }) =>
      "Página " + page + " de " + Math.max(1, totalPages) + " · " + total.toLocaleString("pt-BR") + " parada(s)",
    previous: "Anterior",
    next: "Próxima",
    navigationAriaLabel: "Paginação de paradas",
  },
});

function describeError(error: string | null): string {
  return error ?? "Não foi possível concluir a consulta.";
}

export function DowntimesPage({
  branch,
  params,
  onParamsChange,
  canViewHistory,
  canViewMonitoring,
  onOpenMonitoring,
}: {
  branch: BranchCode;
  params: DowntimesRouteParams;
  onParamsChange: (next: DowntimesRouteParams) => void;
  canViewHistory: boolean;
  canViewMonitoring: boolean;
  onOpenMonitoring: (workCenter: string) => void;
}) {
  const query = useMemo(() => buildDowntimesQuery(branch, params), [branch, params]);
  const downtimes = useDowntimesData(query);
  // Análise gerencial (Etapa 2): mesmo universo elegível da listagem —
  // página, ordenação e downtimeId nunca alteram os agregados.
  const analyticsQuery = useMemo(
    () => buildDowntimeAnalyticsQuery(branch, params),
    [branch, params],
  );
  const analytics = useDowntimeAnalytics(analyticsQuery);
  const options = useDowntimeFilterOptions(branch);
  const selected = useSelectedDowntime(branch, params.downtimeId);
  const nowMs = useServerClock(downtimes.data?.referenceAt);
  const [timelineOpen, setTimelineOpen] = useState(false);

  const detailDayKey = selected.item?.startedAt ? businessDayKey(new Date(selected.item.startedAt)) : null;
  const timeline = useWorkCenterTimeline(
    branch,
    timelineOpen ? selected.item?.workCenter ?? null : null,
    "downtimes-detail",
    canViewHistory && timelineOpen,
    detailDayKey,
    MES_BUSINESS_TIMEZONE,
  );

  const apply = (partial: Partial<DowntimesRouteParams>) => {
    onParamsChange({ ...params, ...partial, page: partial.page ?? 1, downtimeId: null });
  };
  const clearFilters = () => {
    onParamsChange({
      ...params,
      period: "7d",
      from: null,
      to: null,
      workCenter: null,
      reasonCode: null,
      source: null,
      classification: null,
      sort: "recent",
      downtimeId: null,
      page: 1,
    });
  };
  const openDetail = (item: DowntimeItem) => {
    setTimelineOpen(false);
    onParamsChange({ ...params, downtimeId: item.id });
  };
  const closeDetail = () => {
    setTimelineOpen(false);
    onParamsChange({ ...params, downtimeId: null });
  };
  const selectReasonGroup = (group: DowntimeAnalyticsReasonGroup) => {
    if (group.key === PENDING_REASON_GROUP_KEY) {
      apply({ reasonCode: null, classification: "pending" });
    } else if (group.reasonCode) {
      apply({ reasonCode: group.reasonCode, classification: null });
    }
    // "Motivo não informado" (confirmada sem código) não possui filtro
    // equivalente — sem ação de drill-down.
  };

  const items = downtimes.data?.items ?? [];
  const filteredEmpty = items.length === 0 && hasActiveDowntimeFilters(params);

  if (downtimes.loading && !downtimes.data) {
    return (
      <section className="delpi-mes-downtimes" aria-labelledby="downtimes-title">
        <LoadingState classNames={loadingClasses} defaultMessage="Carregando o histórico de paradas…" />
      </section>
    );
  }

  if (!downtimes.data && downtimes.error) {
    return (
      <section className="delpi-mes-downtimes" role="alert">
        <div className="delpi-mes-downtimes__error">
          <h2>Não foi possível carregar as paradas</h2>
          <p>{describeError(downtimes.error)}</p>
          <button type="button" onClick={() => void downtimes.refresh()}>Tentar novamente</button>
        </div>
      </section>
    );
  }

  return (
    <section className="delpi-mes-downtimes" aria-labelledby="downtimes-title">
      <header className="delpi-mes-downtimes__head">
        <div>
          <p className="delpi-mes-eyebrow">Gestão de paradas</p>
          <h2 id="downtimes-title">Paradas</h2>
          <p>
            Eventos reais de parada do MES na filial {branch === "01" ? "SC" : "ES"}.
            Parada encerrada e motivo classificado são condições independentes:
            uma parada pode estar encerrada e ainda aguardar classificação.
          </p>
        </div>
        <div className="delpi-mes-downtimes__refresh" aria-live="polite">
          <button
            type="button"
            className="delpi-mes-refresh-btn"
            onClick={() => void downtimes.refresh()}
            disabled={downtimes.refreshing}
          >
            <RefreshCw aria-hidden="true" />
            {downtimes.refreshing ? "Atualizando…" : "Atualizar"}
          </button>
        </div>
      </header>

      {downtimes.error && downtimes.data ? (
        <p className="delpi-mes-monitoring__stale" role="status">
          Última consulta mantida. A atualização falhou: {downtimes.error}
        </p>
      ) : null}

      <div className="delpi-mes-downtimes__filters" aria-label="Filtros de paradas">
        <label>
          Período
          <span className="delpi-mes-downtimes__label-with-help">
            <select
              value={params.period}
              onChange={(event) => {
                const period = event.target.value as DowntimesRouteParams["period"];
                apply(period === "custom" ? { period } : { period, from: null, to: null });
              }}
            >
              {DOWNTIME_PERIOD_PRESETS.map((preset) => (
                <option key={preset.id} value={preset.id}>{preset.label}</option>
              ))}
            </select>
            <HelpTooltip
              content={DELPI_MES_COPY.help.downtimesPeriod}
              ariaLabel="Ajuda: período"
            />
          </span>
        </label>
        {params.period === "custom" ? (
          <>
            <label>
              De
              <input
                type="date"
                value={params.from ?? ""}
                onChange={(event) => apply({ from: event.target.value || null })}
              />
            </label>
            <label>
              Até
              <input
                type="date"
                value={params.to ?? ""}
                onChange={(event) => apply({ to: event.target.value || null })}
              />
            </label>
          </>
        ) : null}
        <label>
          Centro de trabalho
          <input
            type="search"
            value={params.workCenter ?? ""}
            placeholder="Ex.: CT-35"
            onChange={(event) => apply({ workCenter: event.target.value || null })}
          />
        </label>
        <label>
          Motivo
          <select
            value={params.reasonCode ?? ""}
            onChange={(event) => apply({ reasonCode: event.target.value || null })}
            disabled={options.loading}
          >
            <option value="">Todos</option>
            {(options.data?.reasons ?? []).map((reason) => (
              <option key={reason.code} value={reason.code}>
                {reason.label}{reason.active ? "" : " (inativo)"}
              </option>
            ))}
          </select>
        </label>
        <label>
          Origem
          <select
            value={params.source ?? ""}
            onChange={(event) => apply({ source: event.target.value || null })}
            disabled={options.loading}
          >
            <option value="">Todas</option>
            {(options.data?.sources ?? []).map((source) => (
              <option key={source.code} value={source.code}>{downtimeSourceLabel(source.code)}</option>
            ))}
          </select>
        </label>
        <label>
          Situação
          <span className="delpi-mes-downtimes__label-with-help">
            <select
              value={params.classification ?? ""}
              onChange={(event) =>
                apply({
                  classification: (event.target.value || null) as DowntimesRouteParams["classification"],
                })
              }
            >
              <option value="">Todas</option>
              <option value="pending">Pendente de classificação</option>
              <option value="confirmed">Confirmada</option>
            </select>
            <HelpTooltip
              content={DELPI_MES_COPY.help.downtimesClassification}
              ariaLabel="Ajuda: situação da classificação"
            />
          </span>
        </label>
        <label>
          Ordenação
          <select
            value={params.sort}
            onChange={(event) => apply({ sort: event.target.value === "oldest" ? "oldest" : "recent" })}
          >
            <option value="recent">Mais recentes</option>
            <option value="oldest">Mais antigas</option>
          </select>
        </label>
        {hasActiveDowntimeFilters(params) ? (
          <ClearFiltersButton onClick={clearFilters} />
        ) : null}
      </div>
      {options.error ? (
        <p className="delpi-mes-downtimes__options-warning" role="status">
          Não foi possível carregar as opções de motivo e origem.
          <button type="button" onClick={options.retry}>Tentar novamente</button>
        </p>
      ) : null}

      <DowntimeAnalyticsSection
        analytics={analytics}
        onSelectReasonGroup={selectReasonGroup}
        onSelectWorkCenter={(workCenter) => apply({ workCenter })}
        onSelectDay={(dayKey) =>
          apply({ period: "custom", from: dayKey, to: dayKey })
        }
      />

      {items.length === 0 ? (
        <EmptyState
          title={filteredEmpty ? "Nenhuma parada corresponde aos filtros" : "Nenhuma parada registrada no período"}
          defaultMessage={
            filteredEmpty
              ? "Ajuste ou limpe os filtros para ampliar a consulta."
              : "Paradas manuais, automáticas e autônomas aparecem aqui conforme ocorrem."
          }
          classNames={emptyClasses}
        >
          {filteredEmpty ? <ClearFiltersButton onClick={clearFilters} /> : null}
        </EmptyState>
      ) : (
        <>
          <DataTable<DowntimeItem>
            columns={[
              {
                key: "started",
                header: "Início",
                render: (row) => formatDateTime(row.startedAt),
              },
              {
                key: "ended",
                header: "Término",
                render: (row) => (row.endedAt ? formatDateTime(row.endedAt) : "Em aberto"),
              },
              {
                key: "duration",
                header: "Duração",
                headerHint: DELPI_MES_COPY.help.downtimesDuration,
                align: "right",
                render: (row) => {
                  const seconds = downtimeDurationSeconds(row, nowMs);
                  return seconds === null ? "—" : formatDuration(seconds);
                },
              },
              { key: "workCenter", header: "CT", render: (row) => row.workCenter },
              {
                key: "productionOrder",
                header: "OP / Operação",
                render: (row) =>
                  row.productionOrder
                    ? row.productionOrder + (row.operationCode ? " / " + row.operationCode : "")
                    : "Sem OP vinculada",
              },
              {
                key: "source",
                header: "Origem",
                render: (row) => downtimeSourceLabel(row.source),
              },
              {
                key: "reason",
                header: "Motivo",
                render: (row) => row.reasonLabel ?? "Não informado",
              },
              {
                key: "status",
                header: "Situação",
                render: (row) => {
                  const status = downtimeStatusLabel(row);
                  return (
                    <span className="delpi-mes-downtimes__badges">
                      <StatusBadge
                        label={status.state}
                        variant={row.endedAt ? "neutral" : "danger"}
                        classNames={badgeClasses}
                      />
                      <StatusBadge
                        label={status.classification}
                        variant={row.confirmed ? "success" : "warning"}
                        classNames={badgeClasses}
                      />
                    </span>
                  );
                },
              },
            ]}
            rows={items}
            rowKey={(row) => row.id}
            classNames={tableClasses}
            labels={{
              emptyMessage: "Nenhuma parada encontrada.",
              loadingMessage: "Carregando paradas…",
              headerHelpAriaLabel: (header) => "Ajuda sobre a coluna " + header,
              sortByAriaLabel: (header) => "Ordenar pela coluna " + header,
            }}
            loading={downtimes.refreshing && !downtimes.data}
            layout="embedded"
            onRowClick={openDetail}
            rowClickRole="button"
          />
          <Pagination
            page={params.page}
            pageSize={params.pageSize}
            total={downtimes.data?.total ?? 0}
            pageSizeOptions={[25, 50, 100]}
            onPageChange={(page) => onParamsChange({ ...params, page })}
            onPageSizeChange={(pageSize) => onParamsChange({ ...params, pageSize, page: 1 })}
          />
        </>
      )}

      <DrawerShell
        open={Boolean(params.downtimeId)}
        title="Detalhe da parada"
        onClose={closeDetail}
        classNames={drawerClasses}
      >
        {selected.loading ? (
          <LoadingState classNames={loadingClasses} defaultMessage="Carregando a parada…" />
        ) : selected.error ? (
          <div role="alert">
            <p>{selected.error}</p>
          </div>
        ) : selected.item ? (
          <DowntimeDetail
            item={selected.item}
            nowMs={nowMs}
            canViewHistory={canViewHistory}
            canViewMonitoring={canViewMonitoring}
            timelineOpen={timelineOpen}
            onToggleTimeline={() => setTimelineOpen((open) => !open)}
            timeline={timeline}
            onOpenMonitoring={onOpenMonitoring}
          />
        ) : (
          <p role="status">Esta parada não foi encontrada na filial selecionada.</p>
        )}
      </DrawerShell>
    </section>
  );
}

function DowntimeDetail({
  item,
  nowMs,
  canViewHistory,
  canViewMonitoring,
  timelineOpen,
  onToggleTimeline,
  timeline,
  onOpenMonitoring,
}: {
  item: DowntimeItem;
  nowMs: number;
  canViewHistory: boolean;
  canViewMonitoring: boolean;
  timelineOpen: boolean;
  onToggleTimeline: () => void;
  timeline: ReturnType<typeof useWorkCenterTimeline>;
  onOpenMonitoring: (workCenter: string) => void;
}) {
  const status = downtimeStatusLabel(item);
  const seconds = downtimeDurationSeconds(item, nowMs);
  return (
    <div className="delpi-mes-downtimes__detail">
      <dl>
        <div><dt>Identificador</dt><dd>{item.id}</dd></div>
        <div><dt>Centro de trabalho</dt><dd>{item.workCenter}</dd></div>
        <div><dt>Ordem de produção</dt><dd>{item.productionOrder ?? "Sem OP vinculada"}</dd></div>
        <div><dt>Operação</dt><dd>{item.operationCode ?? "Não informado"}</dd></div>
        <div><dt>Início</dt><dd>{formatDateTime(item.startedAt)}</dd></div>
        <div><dt>Término</dt><dd>{item.endedAt ? formatDateTime(item.endedAt) : "Em aberto"}</dd></div>
        <div><dt>Duração</dt><dd>{seconds === null ? "—" : formatDuration(seconds)}</dd></div>
        <div><dt>Origem</dt><dd>{downtimeSourceLabel(item.source)}</dd></div>
        <div>
          <dt>Motivo</dt>
          <dd>{item.reasonLabel ?? "Não informado"}{item.category ? " · " + item.category : ""}</dd>
        </div>
        <div>
          <dt>Situação</dt>
          <dd>{status.state} · {status.classification}</dd>
        </div>
        <div><dt>Observação</dt><dd>{item.note ?? "—"}</dd></div>
      </dl>
      <div className="delpi-mes-downtimes__detail-actions">
        {canViewHistory ? (
          <button type="button" onClick={onToggleTimeline}>
            {timelineOpen ? "Ocultar linha do tempo do dia" : "Ver linha do tempo do dia"}
          </button>
        ) : null}
        {canViewMonitoring ? (
          <button type="button" onClick={() => onOpenMonitoring(item.workCenter)}>
            Abrir no monitoramento
          </button>
        ) : null}
      </div>
      {timelineOpen && canViewHistory ? (
        <div className="delpi-mes-downtimes__timeline">
          {timeline.loading ? (
            <LoadingState classNames={loadingClasses} defaultMessage="Carregando o dia do centro…" />
          ) : timeline.error ? (
            <p role="alert">
              {timeline.error}
              <button type="button" onClick={timeline.retry}>Tentar novamente</button>
            </p>
          ) : timeline.data && timeline.data.items.length > 0 ? (
            <ul>
              {timeline.data.items.map((entry) => {
                const presentation = presentDayEvent(entry);
                return (
                  <li key={entry.stateEventId}>
                    <strong>{presentation.label}</strong>
                    <span>
                      {formatBusinessClock(Date.parse(entry.startedAt))}
                      {" – "}
                      {entry.endedAt ? formatBusinessClock(Date.parse(entry.endedAt)) : "agora"}
                      {presentation.pendingReason ? " · motivo pendente" : ""}
                      {entry.productionOrder ? " · OP " + entry.productionOrder : ""}
                    </span>
                  </li>
                );
              })}
            </ul>
          ) : (
            <p>Nenhum estado registrado neste dia.</p>
          )}
        </div>
      ) : null}
      {!canViewHistory ? (
        <p className="delpi-mes-downtimes__hint">
          A linha do tempo do dia exige a permissão de Histórico.
        </p>
      ) : null}
    </div>
  );
}
