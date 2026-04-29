import { useMemo, useState } from "react";
import { DepartmentDetailHero } from "../components/DepartmentDetailHero";
import { IndicatorDetailGrid } from "../components/IndicatorDetailGrid";
import { InfoState } from "../components/InfoState";
import { PageHeader } from "../components/PageHeader";
import { SectionBlock } from "../components/SectionBlock";
import { StatusBadge } from "../components/StatusBadge";
import { LoadingActivityBadge } from "../components/LoadingActivityBadge";
import { LoadingActivityInline } from "../components/LoadingActivityInline";
import { StrategicIndicatorsReferenceFilters } from "../components/StrategicIndicatorsReferenceFilters";
import { useStrategicIndicatorsDepartmentDetails } from "../../state/hooks/useStrategicIndicatorsDepartmentDetails";
import {
  buildStrategicIndicatorsMonthRange,
  getCurrentStrategicIndicatorsMonthValue,
  resolveStrategicIndicatorsBranch,
  type StrategicIndicatorsViewMode,
} from "../shared/strategicIndicatorsFilters";
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
  const [referenceMonth, setReferenceMonth] = useState(
    getCurrentStrategicIndicatorsMonthValue(),
  );
  const [viewMode, setViewMode] =
    useState<StrategicIndicatorsViewMode>("consolidated");
  const [branch, setBranch] = useState("01");

  const { startDate, endDate } = useMemo(
    () => buildStrategicIndicatorsMonthRange(referenceMonth),
    [referenceMonth],
  );

  const effectiveBranch = useMemo(
    () => resolveStrategicIndicatorsBranch(viewMode, branch),
    [viewMode, branch],
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
        />
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="si-department-details-page">
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

        <InfoState
          title="Área não localizada"
          description={
            error ??
            "Verifique a rota informada ou retorne para a visão de departamentos."
          }
          actionLabel="Tentar novamente"
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
        />
      ) : null}

      {error && data ? (
        <InfoState
          title="Falha ao atualizar departamento"
          description={error}
          actionLabel="Tentar novamente"
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