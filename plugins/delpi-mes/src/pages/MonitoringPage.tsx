import { EmptyState, LoadingState, MetricStrip, emptyStatePanelBemClasses, loadingStatePanelBemClasses, metricStripBemClasses } from "@delpi/plugin-ui/index";
import { useMemo, useState } from "react";
import type { BranchCode } from "../constants/routes";
import { useMonitoringData } from "../hooks/useMonitoringData";
import { useServerClock } from "../hooks/useServerClock";
import type { MonitoringFilters, SortMode, StatusFilter } from "../utils/monitoringFilters";
import { filterMonitoringItems } from "../utils/monitoringFilters";
import { elapsedSeconds } from "../utils/duration";
import { WorkCenterCard } from "../components/monitoring/WorkCenterCard";
import { RunDetailDrawer } from "../components/monitoring/RunDetailDrawer";

const metricClasses = metricStripBemClasses("delpi-mes");
const loadingClasses = loadingStatePanelBemClasses("delpi-mes");
const emptyClasses = emptyStatePanelBemClasses("delpi-mes");
const initialFilters: MonitoringFilters = { search: "", status: "all", reason: "", sort: "attention" };

export function MonitoringPage({ branch, canViewHistory }: { branch: BranchCode; canViewHistory: boolean }) {
  const monitoring = useMonitoringData(branch);
  const nowMs = useServerClock(monitoring.data?.referenceAt);
  const [filters, setFilters] = useState(initialFilters);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const selected = monitoring.data?.items.find((item) => item.runId === selectedRunId) ?? null;
  const reasons = useMemo(() => Array.from(new Set((monitoring.data?.items ?? []).map((item) => item.downtime?.reasonLabel).filter((value): value is string => Boolean(value)))).sort(), [monitoring.data]);
  const items = useMemo(() => filterMonitoringItems(monitoring.data?.items ?? [], filters, nowMs), [monitoring.data, filters, nowMs]);
  const hasFilters = filters.search !== "" || filters.status !== "all" || filters.reason !== "";
  const summary = monitoring.data?.summary;
  const updatedAgo = monitoring.data ? elapsedSeconds(monitoring.data.referenceAt, nowMs) : 0;

  if (monitoring.loading && !monitoring.data) return <LoadingState classNames={loadingClasses} defaultMessage="Carregando monitoramento industrial…" />;
  if (!monitoring.data && monitoring.error) return <section className="delpi-mes-monitoring-error" role="alert"><h2>Não foi possível carregar o monitoramento</h2><p>{monitoring.error}</p><button type="button" onClick={() => void monitoring.refresh()}>Tentar novamente</button></section>;
  if (!monitoring.data || !summary) return null;

  return <section className="delpi-mes-monitoring" aria-labelledby="monitoring-title">
    <header className="delpi-mes-monitoring__head"><div><p className="delpi-mes-eyebrow">Supervisão gerencial</p><h2 id="monitoring-title">Monitoramento Industrial</h2><p>Runs MES ativos na filial {branch === "01" ? "SC" : "ES"}.</p></div><div className="delpi-mes-monitoring__refresh" aria-live="polite"><span>{monitoring.refreshing ? "Atualizando…" : `Atualizado há ${updatedAgo} s`}</span><button type="button" onClick={() => void monitoring.refresh()} disabled={monitoring.refreshing}>Atualizar</button></div></header>
    {monitoring.error ? <p className="delpi-mes-monitoring__stale" role="status">Último snapshot mantido. A atualização falhou: {monitoring.error}</p> : null}
    <MetricStrip classNames={metricClasses} aria-label="Resumo dos runs ativos" items={[
      { id: "active", label: "Runs ativos", value: summary.activeRuns },
      { id: "producing", label: "Produzindo", value: summary.producing, tone: "success" },
      { id: "stopped", label: "Estado parado", value: summary.stopped, tone: "warning", description: "Inclui pausas manuais" },
      { id: "paused", label: "Pausas manuais", value: summary.paused, tone: "warning" },
      { id: "pending", label: "Motivos pendentes", value: summary.unclassifiedDowntimes, tone: "danger" },
    ]} />
    <div className="delpi-mes-monitoring__filters" aria-label="Filtros do monitoramento">
      <label>Busca<input type="search" value={filters.search} placeholder="CT, OP, operação, operador ou motivo" onChange={(event) => setFilters((current) => ({ ...current, search: event.target.value }))} /></label>
      <label>Estado<select value={filters.status} onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value as StatusFilter }))}><option value="all">Todos</option><option value="producing">Produzindo</option><option value="stopped">Parada</option><option value="paused">Pausa manual</option><option value="pending">Motivo pendente</option><option value="incomplete">Dados incompletos</option></select></label>
      <label>Motivo<select value={filters.reason} onChange={(event) => setFilters((current) => ({ ...current, reason: event.target.value }))}><option value="">Todos</option>{reasons.map((reason) => <option key={reason}>{reason}</option>)}</select></label>
      <label>Ordenação<select value={filters.sort} onChange={(event) => setFilters((current) => ({ ...current, sort: event.target.value as SortMode }))}><option value="attention">Atenção primeiro</option><option value="workCenter">Centro de trabalho</option><option value="duration">Maior tempo no estado</option><option value="productionOrder">OP</option></select></label>
      {hasFilters ? <button type="button" onClick={() => setFilters(initialFilters)}>Limpar filtros</button> : null}
    </div>
    {monitoring.data.items.length === 0 ? <EmptyState title="Nenhuma produção ativa nesta filial" defaultMessage="Os centros aparecem aqui quando possuem um Production Run ativo." classNames={emptyClasses} /> : items.length === 0 ? <EmptyState title="Nenhum centro corresponde aos filtros atuais" defaultMessage="Ajuste ou limpe os filtros para voltar a visualizar os runs ativos." classNames={emptyClasses}><button type="button" onClick={() => setFilters(initialFilters)}>Limpar filtros</button></EmptyState> : <div className="delpi-mes-work-center-grid">{items.map((item) => <WorkCenterCard key={item.runId} item={item} nowMs={nowMs} onOpen={() => setSelectedRunId(item.runId)} />)}</div>}
    <RunDetailDrawer item={selected} branch={branch} nowMs={nowMs} canViewHistory={canViewHistory} onClose={() => setSelectedRunId(null)} />
  </section>;
}
