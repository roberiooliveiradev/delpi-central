import {
  ClipboardCheck,
  FlaskConical,
  Package,
  Percent,
  UserRound,
  Wrench,
  XCircle,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { EmptyState } from "../components/EmptyState";
import { IndicadorEnsaiadorSection } from "../components/IndicadorEnsaiadorSection";
import { KpiCard } from "../components/KpiCard";
import { PageShell } from "../components/PageShell";
import { PeriodFilters } from "../components/PeriodFilters";
import { RankingProdutoSection } from "../components/RankingProdutoSection";
import { branchLabel } from "../constants/branch";
import { useInspecoesProcessoPorEnsaiador } from "../hooks/useInspecoesProcessoPorEnsaiador";
import { useInspecoesProcessoPorProduto } from "../hooks/useInspecoesProcessoPorProduto";
import { useInspecoesProcessoResumo } from "../hooks/useInspecoesProcessoResumo";
import { validatePeriodRange } from "../utils/dateRange";
import { formatIsoDatePt, formatNumber, formatPercent } from "../utils/format";
import {
  periodFromSearch,
  syncPeriodInUrl,
  type DashboardPeriod,
} from "../utils/periodQuery";

type DashboardPageProps = {
  branch: string;
  search?: string;
  active?: boolean;
  refreshToken?: number;
  onLoadingChange?: (loading: boolean) => void;
  onLastUpdated?: (date: Date) => void;
};

export function DashboardPage({
  branch,
  search,
  active = true,
  refreshToken = 0,
  onLoadingChange,
  onLastUpdated,
}: DashboardPageProps) {
  const [period, setPeriod] = useState<DashboardPeriod>(() => periodFromSearch(search));
  const [trackedSearch, setTrackedSearch] = useState(search);
  if (search !== trackedSearch) {
    setTrackedSearch(search);
    setPeriod(periodFromSearch(search));
  }
  const rangeError =
    period.mode === "range" ? validatePeriodRange(period.startDate, period.endDate) : null;
  const kpiPeriod = {
    startDate: period.mode === "range" ? period.startDate : undefined,
    endDate: period.mode === "range" ? period.endDate : undefined,
    enabled: !rangeError,
  };

  const handlePeriodChange = useCallback((next: DashboardPeriod) => {
    setPeriod(next);
    syncPeriodInUrl(next);
  }, []);

  useEffect(() => {
    syncPeriodInUrl(period);
  }, [period]);

  const {
    data,
    loading: resumoLoading,
    error: resumoError,
    reload: reloadResumo,
  } = useInspecoesProcessoResumo(branch, refreshToken, kpiPeriod);
  const {
    items: produtoItems,
    loading: produtoLoading,
    error: produtoError,
    reload: reloadProduto,
  } = useInspecoesProcessoPorProduto(branch, refreshToken, kpiPeriod);
  const {
    items: ensaiadorItems,
    loading: ensaiadorLoading,
    error: ensaiadorError,
    reload: reloadEnsaiador,
  } = useInspecoesProcessoPorEnsaiador(branch, refreshToken, kpiPeriod);

  const refreshing = resumoLoading || produtoLoading || ensaiadorLoading;

  useEffect(() => {
    if (!active) return;
    onLoadingChange?.(refreshing);
  }, [active, onLoadingChange, refreshing]);

  useEffect(() => {
    if (!active || refreshing || !data) return;
    onLastUpdated?.(new Date());
  }, [active, refreshing, data, refreshToken, onLastUpdated]);

  const unidade = data?.unidade?.trim() || branchLabel(branch);
  const selectedPeriodLabel =
    period.mode === "all"
      ? "Todo o histórico"
      : `${formatIsoDatePt(period.startDate)} até ${formatIsoDatePt(period.endDate)}`;
  const measuredPeriod =
    data?.primeira_data_medicao || data?.ultima_data_medicao
      ? `${formatIsoDatePt(data.primeira_data_medicao)} até ${formatIsoDatePt(data.ultima_data_medicao)}`
      : null;

  const description = resumoLoading
    ? `Carregando resumo de ${branchLabel(branch)}…`
    : resumoError
      ? `Não foi possível carregar o resumo de ${branchLabel(branch)}.`
      : data
        ? `${unidade} · Filial ${data.filial || branch} · Período: ${selectedPeriodLabel}${
            measuredPeriod && period.mode === "all" ? ` (${measuredPeriod})` : ""
          }`
        : `Resumo de ${branchLabel(branch)}.`;

  return (
    <PageShell title="Dashboard" description={description}>
      <PeriodFilters
        period={period}
        loading={refreshing}
        onChange={handlePeriodChange}
      />
      {resumoLoading && !data ? (
        <div className="ip-alert ip-alert--info" role="status" aria-live="polite">
          <p>Carregando resumo da filial…</p>
        </div>
      ) : null}

      {resumoError ? (
        <div className="ip-alert ip-alert--error" role="alert">
          <p>{resumoError}</p>
          <button type="button" className="ip-button" onClick={reloadResumo}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      {!resumoLoading && !resumoError && !data ? (
        <EmptyState
          title="Sem dados de resumo"
          description="A API não retornou dados agregados para esta filial."
        />
      ) : null}

      {data ? (
        <>
          <div className="ip-kpi-grid">
            <KpiCard
              title="OPs inspecionadas"
              value={formatNumber(data.qtde_ops)}
              subtitle={`${formatNumber(data.qtde_ops_aprovadas)} aprovadas · ${formatNumber(data.qtde_ops_reprovadas)} reprovadas`}
              icon={<ClipboardCheck size={22} strokeWidth={1.75} />}
            />
            <KpiCard
              title="Ensaios executados"
              value={formatNumber(data.qtde_ensaios)}
              subtitle="Total de ensaios na filial"
              icon={<FlaskConical size={22} strokeWidth={1.75} />}
            />
            <KpiCard
              title="Ensaios aprovados"
              value={formatNumber(data.qtde_ensaios_aprovados)}
              subtitle={formatPercent(data.percentual_ensaios_aprovados)}
              icon={<FlaskConical size={22} strokeWidth={1.75} />}
            />
            <KpiCard
              title="Ensaios reprovados"
              value={formatNumber(data.qtde_ensaios_reprovados)}
              subtitle={formatPercent(data.percentual_ensaios_reprovados)}
              icon={<XCircle size={22} strokeWidth={1.75} />}
            />
            <KpiCard
              title="Produtos"
              value={formatNumber(data.qtde_produtos)}
              subtitle="Produtos distintos inspecionados"
              icon={<Package size={22} strokeWidth={1.75} />}
            />
            <KpiCard
              title="Operações"
              value={formatNumber(data.qtde_operacoes)}
              subtitle="Operações distintas"
              icon={<Wrench size={22} strokeWidth={1.75} />}
            />
            <KpiCard
              title="Ensaiadores"
              value={formatNumber(data.qtde_ensaiadores)}
              subtitle="Logins distintos"
              icon={<UserRound size={22} strokeWidth={1.75} />}
            />
            <KpiCard
              title="% ensaios aprovados"
              value={formatPercent(data.percentual_ensaios_aprovados)}
              subtitle={`OPs aprovadas: ${formatPercent(data.percentual_ops_aprovadas)}`}
              icon={<Percent size={22} strokeWidth={1.75} />}
            />
          </div>

          <p className="ip-muted-note">
            Dados agregados pela data da medição no período selecionado. Detalhes
            carregam somente sob demanda.
          </p>
        </>
      ) : null}

      <RankingProdutoSection
        items={produtoItems}
        loading={produtoLoading}
        error={produtoError}
        onRetry={reloadProduto}
      />

      <IndicadorEnsaiadorSection
        items={ensaiadorItems}
        loading={ensaiadorLoading}
        error={ensaiadorError}
        onRetry={reloadEnsaiador}
      />
    </PageShell>
  );
}
