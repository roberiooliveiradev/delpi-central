import { useStrategicIndicatorsFilters } from "../../state/hooks/useStrategicIndicatorsFilters";
import { DepartmentOverviewTable } from "../components/DepartmentOverviewTable";
import { StrategicIndicatorsErrorState } from "../components/StrategicIndicatorsErrorState";
import { PageHeader } from "../components/PageHeader";
import { SectionBlock } from "../components/SectionBlock";
import { StatusBadge } from "../components/StatusBadge";
import { LoadingActivityBadge } from "../components/LoadingActivityBadge";
import { LoadingActivityInline } from "../components/LoadingActivityInline";
import { StrategicIndicatorsReferenceFilters } from "../components/StrategicIndicatorsReferenceFilters";
import { useStrategicIndicatorsDepartments } from "../../state/hooks/useStrategicIndicatorsDepartments";
import "./DepartmentsPage.css";

type DepartmentsPageProps = {
  getAccessToken?: () => string | undefined;
};

export function DepartmentsPage({ getAccessToken }: DepartmentsPageProps) {
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

  const { items, loading, refreshing, error, reload } =
    useStrategicIndicatorsDepartments({
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

  return (
    <div className="si-departments-page">
      <PageHeader
        eyebrow="MinhaDelpi"
        title="Departamentos"
        description="Visão comparativa dos departamentos que compõem o IGD, com peso oficial, nota resumida e acesso ao drill-down por área."
        badge={
          loading || refreshing ? (
            <LoadingActivityBadge label="Atualizando" tone="info" />
          ) : (
            <StatusBadge label="API Real" variant="success" />
          )
        }
      />

      <SectionBlock
        title="Filtro de referência"
        description="Selecione o mês de referência e a visão analítica desejada para consultar a composição departamental do período."
      >
        {filters}
      </SectionBlock>

      <SectionBlock
        title="Comparativo departamental"
        description="Cada linha representa um departamento oficial do IGD, com acesso à visão específica do seu IDD."
      >
        {loading && items.length === 0 ? (
          <LoadingActivityInline
            title="Carregando departamentos"
            description="Aguarde enquanto a visão comparativa é carregada."
            variant="panel"
            tone="info"
          />
        ) : error && items.length === 0 ? (
          <StrategicIndicatorsErrorState
            error={error}
            actionLabel="Tentar novamente"
            onAction={() => void reload()}
          />
        ) : (
          <>
            {refreshing ? (
              <LoadingActivityInline
                title="Atualizando departamentos"
                description="Os dados exibidos estão sendo atualizados para o novo período."
                variant="compact"
                tone="info"
              />
            ) : null}

            {error && items.length > 0 ? (
              <StrategicIndicatorsErrorState
                error={{ ...error, title: "Falha ao atualizar departamentos" }}
                actionLabel="Tentar novamente"
                onAction={() => void reload()}
              />
            ) : null}

            <DepartmentOverviewTable departments={items} />
          </>
        )}
      </SectionBlock>
    </div>
  );
}