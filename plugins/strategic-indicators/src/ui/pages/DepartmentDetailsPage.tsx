import { useMemo } from "react";
import { useSimulatedLoadingProgress } from "../hooks/useSimulatedLoadingProgress";
import { DepartmentDetailHero } from "../components/DepartmentDetailHero";
import { IndicatorDetailGrid } from "../components/IndicatorDetailGrid";
import { StrategicIndicatorsPageError } from "../components/StrategicIndicatorsPageError";
import { StrategicIndicatorsBackLink } from "../components/StrategicIndicatorsBackLink";
import { PageHeader } from "../components/PageHeader";
import { SectionBlock } from "../components/SectionBlock";
import { StatusBadge } from "../components/StatusBadge";
import { LoadingActivityBadge } from "../components/LoadingActivityBadge";
import { LoadingActivityInline } from "../components/LoadingActivityInline";
import { StrategicIndicatorsReferenceFilters } from "../components/StrategicIndicatorsReferenceFilters";
import { useStrategicIndicatorsDepartmentDetails } from "../../state/hooks/useStrategicIndicatorsDepartmentDetails";
import { useStrategicIndicatorsFilters } from "../../state/hooks/useStrategicIndicatorsFilters";
import "./DepartmentDetailsPage.css";

type DepartmentDetailsPageProps = {
  pathname: string;
  getAccessToken?: () => string | undefined;
};

function extractDepartmentId(pathname: string) {
  const parts = pathname.split("/").filter(Boolean);
  return parts[parts.length - 1] ?? "";
}

export function DepartmentDetailsPage({
  pathname,
  getAccessToken,
}: DepartmentDetailsPageProps) {
  const departmentId = useMemo(() => extractDepartmentId(pathname), [pathname]);
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
    filterState,
  } = useStrategicIndicatorsFilters();

  const backToDepartments = (
    <StrategicIndicatorsBackLink
      href="/apps/strategic-indicators/departments"
      label="Voltar aos departamentos"
      filterState={filterState}
    />
  );

  const { data, loading, refreshing, error, reload } =
    useStrategicIndicatorsDepartmentDetails({
      departmentId,
      branch: effectiveBranch,
      competence: referenceMonth,
      startDate,
      endDate,
      getAccessToken,
    });

  const loadingProgress = useSimulatedLoadingProgress(loading && !data);
  const refreshingProgress = useSimulatedLoadingProgress(Boolean(refreshing && data));

  const filters = (
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
      <div className="si-department-details-page">
        <nav className="si-department-details-page__nav">{backToDepartments}</nav>
        <PageHeader
          eyebrow="MinhaDelpi"
          title="Departamento"
          description="Carregando visão detalhada da área."
          badge={<LoadingActivityBadge label="Carregando" tone="neutral" />}
        />

        <SectionBlock
          title="Filtro de referência"
          description="Selecione o mês de referência e a visão analítica desejada para consultar o detalhe do departamento."
        >
          {filters}
        </SectionBlock>

        <LoadingActivityInline
          title="Carregando departamento"
          description="Aguarde enquanto a visão detalhada é carregada."
          variant="panel"
          tone="info"
          progressPercent={loadingProgress}
        />
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="si-department-details-page">
        <nav className="si-department-details-page__nav">{backToDepartments}</nav>
        <PageHeader
          eyebrow="MinhaDelpi"
          title="Departamento não encontrado"
          description="Não foi possível localizar a área solicitada."
          badge={<StatusBadge label="Indisponível" variant="warning" />}
        />

        <SectionBlock
          title="Filtro de referência"
          description="Selecione o mês de referência e a visão analítica desejada para consultar o detalhe do departamento."
        >
          {filters}
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

  return (
    <div className="si-department-details-page">
      <nav className="si-department-details-page__nav">{backToDepartments}</nav>
      <PageHeader
        eyebrow="MinhaDelpi"
        title={`Departamento — ${data.name}`}
        description={`Visão detalhada do IDD departamental no período ${referenceMonth}, com metas estruturadas por indicador e composição analítica da área.`}
        badge={
          loading || refreshing ? (
            <LoadingActivityBadge label="Atualizando" tone="info" />
          ) : (
            <StatusBadge label="Drill-down real" variant="success" />
          )
        }
      />

      <SectionBlock
        title="Filtro de referência"
        description="Selecione o mês de referência e a visão analítica desejada para consultar o detalhe do departamento."
      >
        {filters}
      </SectionBlock>

      {refreshing ? (
        <LoadingActivityInline
          title="Atualizando departamento"
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

      <DepartmentDetailHero department={data} />

      <SectionBlock
        title="Indicadores que compõem o IDD"
        description="Os cards abaixo mostram os indicadores oficiais da área com peso interno, direção de performance, meta estruturada e descrição estratégica. Indicadores com curva mensal devem refletir metas variáveis ao longo do ano."
      >
        <IndicatorDetailGrid
          indicators={data.indicators}
          competence={referenceMonth}
        />
      </SectionBlock>
    </div>
  );
}