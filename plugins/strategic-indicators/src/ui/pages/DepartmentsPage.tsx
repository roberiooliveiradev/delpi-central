import { useStrategicIndicatorsFilters } from "../../state/hooks/useStrategicIndicatorsFilters";
import { DepartmentIgdTree } from "../components/DepartmentIgdTree";
import { StrategicIndicatorsPageError } from "../components/StrategicIndicatorsPageError";
import { PageHeader } from "../components/PageHeader";
import { SectionBlock } from "../components/SectionBlock";
import { StatusBadge } from "../components/StatusBadge";
import { LoadingActivityBadge } from "../components/LoadingActivityBadge";
import { LoadingActivityInline } from "../components/LoadingActivityInline";
import { StrategicIndicatorsReferenceFilters } from "../components/StrategicIndicatorsReferenceFilters";
import { useStrategicIndicatorsDepartmentTree } from "../../state/hooks/useStrategicIndicatorsDepartmentTree";
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
    filterState,
  } = useStrategicIndicatorsFilters();

  const { model, loading, refreshing, error, reload, isMultiColumn } =
    useStrategicIndicatorsDepartmentTree({
      viewMode,
      branch,
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
        description="Mapa interativo do IGD Delpi com pan, zoom e drill-down por departamento."
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
        description="Selecione o mês de referência e a visão analítica. No consolidado, a árvore exibe três colunas (Consolidado, Filial 01 e Filial 02)."
      >
        {filters}
      </SectionBlock>

      <SectionBlock
        title="Árvore departamental do IGD"
        description="Mapa navegável com cards clicáveis, gráficos de evolução (6 meses), anel de nota e drill-down para painel, tendências e departamentos."
      >
        {loading && !model ? (
          <LoadingActivityInline
            title="Carregando árvore departamental"
            description="Aguarde enquanto os escopos, departamentos e indicadores são carregados."
            variant="panel"
            tone="info"
          />
        ) : error && !model ? (
          <StrategicIndicatorsPageError
            error={error}
            onAction={() => void reload()}
          />
        ) : model ? (
          <>
            {refreshing ? (
              <LoadingActivityInline
                title="Atualizando árvore departamental"
                description="Os dados exibidos estão sendo atualizados para o novo período."
                variant="compact"
                tone="info"
              />
            ) : null}

            {error ? (
              <StrategicIndicatorsPageError
                error={error}
                mode="refresh"
                onAction={() => void reload()}
              />
            ) : null}

            <DepartmentIgdTree
              model={model}
              filterState={filterState}
              isMultiColumn={isMultiColumn}
            />
          </>
        ) : null}
      </SectionBlock>
    </div>
  );
}
