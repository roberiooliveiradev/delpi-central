import {
  ClipboardCheck,
  FlaskConical,
  Package,
  Percent,
  UserRound,
  Wrench,
  XCircle,
} from "lucide-react";
import { useEffect } from "react";

import { EmptyState } from "../components/EmptyState";
import { IndicadorEnsaiadorSection } from "../components/IndicadorEnsaiadorSection";
import { KpiCard } from "../components/KpiCard";
import { PageShell } from "../components/PageShell";
import { RankingProdutoSection } from "../components/RankingProdutoSection";
import { branchLabel } from "../constants/branch";
import { useInspecoesProcessoPorEnsaiador } from "../hooks/useInspecoesProcessoPorEnsaiador";
import { useInspecoesProcessoPorProduto } from "../hooks/useInspecoesProcessoPorProduto";
import { useInspecoesProcessoResumo } from "../hooks/useInspecoesProcessoResumo";
import { formatIsoDatePt, formatNumber, formatPercent } from "../utils/format";

type DashboardPageProps = {
  branch: string;
  active?: boolean;
  refreshToken?: number;
  onLoadingChange?: (loading: boolean) => void;
  onLastUpdated?: (date: Date) => void;
};

export function DashboardPage({
  branch,
  active = true,
  refreshToken = 0,
  onLoadingChange,
  onLastUpdated,
}: DashboardPageProps) {
  const {
    data,
    loading: resumoLoading,
    error: resumoError,
    reload: reloadResumo,
  } = useInspecoesProcessoResumo(branch, refreshToken);
  const {
    items: produtoItems,
    loading: produtoLoading,
    error: produtoError,
    reload: reloadProduto,
  } = useInspecoesProcessoPorProduto(branch, refreshToken);
  const {
    items: ensaiadorItems,
    loading: ensaiadorLoading,
    error: ensaiadorError,
    reload: reloadEnsaiador,
  } = useInspecoesProcessoPorEnsaiador(branch, refreshToken);

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
  const periodo =
    data?.primeira_data_medicao || data?.ultima_data_medicao
      ? `${formatIsoDatePt(data.primeira_data_medicao)} até ${formatIsoDatePt(data.ultima_data_medicao)}`
      : null;

  const description = resumoLoading
    ? `Carregando resumo de ${branchLabel(branch)}…`
    : resumoError
      ? `Não foi possível carregar o resumo de ${branchLabel(branch)}.`
      : data
        ? `${unidade} · Filial ${data.filial || branch}${periodo ? ` · Período: ${periodo}` : ""}`
        : `Resumo de ${branchLabel(branch)}.`;

  return (
    <PageShell title="Dashboard" description={description}>
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
            Dados agregados por filial. Detalhes serão carregados somente sob demanda.
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
