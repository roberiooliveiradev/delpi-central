import { useStrategicIndicatorsFilters } from "../../state/hooks/useStrategicIndicatorsFilters";
import { useLoadingProgress } from "../hooks/useSimulatedLoadingProgress";
import { Card } from "../components/Card";
import { ClassificationBand } from "../components/ClassificationBand";
import { ContributionRanking } from "../components/ContributionRanking";
import { DepartmentSummaryGrid } from "../components/DepartmentSummaryGrid";
import { ExecutiveMethodCard } from "../components/ExecutiveMethodCard";
import { IgdHeroCard } from "../components/IgdHeroCard";
import { StrategicIndicatorsPageError } from "../components/StrategicIndicatorsPageError";
import { PageHeader } from "../components/PageHeader";
import { SectionBlock } from "../components/SectionBlock";
import { StatusBadge } from "../components/StatusBadge";
import { LastUpdateBadge } from "../components/LastUpdateBadge";
import { LoadingActivityBadge } from "../components/LoadingActivityBadge";
import { LoadingActivityInline } from "../components/LoadingActivityInline";
import { RefreshSnapshotButton } from "../components/RefreshSnapshotButton";
import { StrategicIndicatorsReferenceFilters } from "../components/StrategicIndicatorsReferenceFilters";
import { useStrategicIndicatorsExecutiveSummary } from "../../state/hooks/useStrategicIndicatorsExecutiveSummary";
import "./ExecutiveDashboardPage.css";

type ExecutiveDashboardPageProps = {
  getAccessToken?: () => string | undefined;
};

export function ExecutiveDashboardPage({
  getAccessToken,
}: ExecutiveDashboardPageProps) {
  const {
    referenceMonth,
    viewMode,
    branch,
    setReferenceMonth,
    setViewMode,
    setBranch,
    startDate,
    endDate,
    effectiveBranch,
  } = useStrategicIndicatorsFilters();

  const { data, loading, refreshing, requestProgress, error, reload } =
    useStrategicIndicatorsExecutiveSummary({
      branch: effectiveBranch,
      competence: referenceMonth,
      startDate,
      endDate,
      getAccessToken,
    });

  const loadingProgress = useLoadingProgress(loading && !data, requestProgress);
  const refreshingProgress = useLoadingProgress(Boolean(refreshing && data), requestProgress);

  const refreshButton = (
    <RefreshSnapshotButton
      getAccessToken={getAccessToken}
      competence={referenceMonth}
      onRefreshed={() => void reload()}
      disabled={loading || refreshing}
    />
  );

  const filterBlock = (
    <StrategicIndicatorsReferenceFilters
      referenceMonth={referenceMonth}
      viewMode={viewMode}
      branch={branch}
      onReferenceMonthChange={setReferenceMonth}
      onViewModeChange={setViewMode}
      onBranchChange={setBranch}
    />
  );

  if (loading && !data) {
    return (
      <div className="si-executive-dashboard-page">
        <PageHeader
          eyebrow="MinhaDelpi"
          title="Indicadores Estratégicos"
          description="Carregando visão executiva do IGD e dos IDDs departamentais."
          badge={<LoadingActivityBadge label="Carregando" tone="neutral" />}
          actions={refreshButton}
        />

        <SectionBlock
          title="Filtro de referência"
          description="Selecione o mês de referência e a visão analítica desejada."
        >
          {filterBlock}
        </SectionBlock>

        <LoadingActivityInline
          title="Carregando painel executivo"
          description="Aguarde enquanto o resumo executivo é carregado."
          variant="panel"
          tone="info"
          progressPercent={loadingProgress}
        />
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="si-executive-dashboard-page">
        <PageHeader
          eyebrow="MinhaDelpi"
          title="Indicadores Estratégicos"
          description="Não foi possível carregar a visão executiva do painel."
          badge={<StatusBadge label="Erro" variant="warning" />}
          actions={refreshButton}
        />

        <SectionBlock
          title="Filtro de referência"
          description="Selecione o mês de referência e a visão analítica desejada."
        >
          {filterBlock}
        </SectionBlock>

        <StrategicIndicatorsPageError
          error={error}
          onAction={() => void reload()}
        />
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const strongestDepartment = [...data.departments].sort(
    (a, b) => b.score - a.score,
  )[0];

  const watchDepartment = [...data.departments].sort(
    (a, b) => a.score - b.score,
  )[0];

  const totalContribution = data.departments.reduce(
    (sum, department) => sum + department.contribution,
    0,
  );

  return (
    <div className="si-executive-dashboard-page">
      <PageHeader
        eyebrow="MinhaDelpi"
        title="Indicadores Estratégicos"
        description={`Painel executivo do IGD e dos IDDs departamentais. Competência ${data.competence}.`}
        badge={
          loading || refreshing ? (
            <LoadingActivityBadge label="Atualizando" tone="info" />
          ) : (
            <>
              <StatusBadge label="API Real" variant="success" />
              <LastUpdateBadge getAccessToken={getAccessToken} />
            </>
          )
        }
        actions={refreshButton}
      />

      <SectionBlock
        title="Filtro de referência"
        description="Selecione o mês de referência e a visão analítica desejada."
      >
        {filterBlock}
      </SectionBlock>

      {refreshing ? (
        <LoadingActivityInline
          title="Atualizando resumo executivo"
          description="Os dados exibidos estão sendo atualizados para o novo período."
          variant="compact"
          tone="info"
          progressPercent={refreshingProgress}
        />
      ) : null}

      {error && data ? (
        <StrategicIndicatorsPageError
          error={error}
          mode="refresh"
          onAction={() => void reload()}
        />
      ) : null}

      <div className="si-executive-grid">
        <IgdHeroCard
          igd={data.igd}
          igdExact={data.igdExact}
          classification={data.classification}
          strongestDepartment={`${strongestDepartment.name} (${strongestDepartment.score.toFixed(1)})`}
          watchDepartment={`${watchDepartment.name} (${watchDepartment.score.toFixed(1)})`}
        />

        <Card
          title="Leitura executiva"
          description="O índice resume, em uma nota única, a performance integrada das áreas estratégicas da empresa."
          headerRight={<StatusBadge label="Mensal" variant="neutral" />}
        >
          <p className="si-muted">
            A visão executiva agora é servida por API real do módulo,
            considerando o período e a visão selecionados no filtro.
          </p>

          <div className="si-executive-note">
            <div className="si-executive-note__item">
              <span className="si-executive-note__label">Faixa atual</span>
              <strong className="si-executive-note__value">
                {data.classification}
              </strong>
            </div>

            <div className="si-executive-note__item">
              <span className="si-executive-note__label">Melhor IDD</span>
              <strong className="si-executive-note__value">
                {strongestDepartment.name}
              </strong>
            </div>

            <div className="si-executive-note__item">
              <span className="si-executive-note__label">
                Atenção prioritária
              </span>
              <strong className="si-executive-note__value">
                {watchDepartment.name}
              </strong>
            </div>

            <div className="si-executive-note__item">
              <span className="si-executive-note__label">Soma ponderada</span>
              <strong className="si-executive-note__value">
                {totalContribution.toFixed(3)}
              </strong>
            </div>

            <div className="si-executive-note__item">
              <span className="si-executive-note__label">Variação</span>
              <strong className="si-executive-note__value">
                {data.variation.value > 0 ? "+" : ""}
                {data.variation.value.toFixed(1)} {data.variation.vsLabel}
              </strong>
            </div>
          </div>
        </Card>
      </div>

      <SectionBlock
        title="Faixa interpretativa do IGD"
        description="A régua abaixo traduz a nota do índice em leitura gerencial objetiva."
      >
        <ClassificationBand value={data.igd} />
      </SectionBlock>

      <SectionBlock
        title="Metodologia do índice"
        description="Resumo visual de como o índice global é consolidado no painel estratégico."
      >
        <ExecutiveMethodCard igd={data.igd} igdExact={data.igdExact} />
      </SectionBlock>

      <SectionBlock
        title="Contribuição por departamentos"
        description="O ranking abaixo mostra como cada área participa da composição ponderada do IGD."
      >
        <ContributionRanking departments={data.departments} />
      </SectionBlock>

      <SectionBlock
        title="Composição por departamentos"
        description="Os cards abaixo mostram os departamentos que compõem o IGD, com seus pesos oficiais, nota resumida, foco estratégico e metas de referência do modelo 2026."
      >
        <DepartmentSummaryGrid departments={data.departments} />
      </SectionBlock>
    </div>
  );
}