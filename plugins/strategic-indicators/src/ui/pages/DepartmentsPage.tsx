import { useCallback } from "react";
import { useSimulatedLoadingProgress } from "../hooks/useSimulatedLoadingProgress";
import {
  applyTreeScopeSelection,
  resolveActiveTreeScopeKey,
} from "../../data/departmentTreeScopes";
import type { DepartmentTreeScopeKey } from "../../data/types/departmentTree";
import { useStrategicIndicatorsFilters } from "../../state/hooks/useStrategicIndicatorsFilters";
import { DepartmentIgdTree } from "../components/DepartmentIgdTree";
import { StrategicIndicatorsPageError } from "../components/StrategicIndicatorsPageError";
import { StatusBadge } from "../components/StatusBadge";
import { LoadingActivityBadge } from "../components/LoadingActivityBadge";
import { LoadingActivityInline } from "../components/LoadingActivityInline";
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
    monthsToCompare,
    setReferenceMonth,
    setViewMode,
    setBranch,
    setMonthsToCompare,
    startDate,
    endDate,
    filterState,
  } = useStrategicIndicatorsFilters();

  const treeScope = resolveActiveTreeScopeKey(viewMode, branch);

  const handleTreeScopeChange = useCallback(
    (scope: DepartmentTreeScopeKey) => {
      const next = applyTreeScopeSelection(scope);
      setViewMode(next.viewMode);
      setBranch(next.branch);
    },
    [setViewMode, setBranch],
  );

  const { model, loading, refreshing, error, reload } =
    useStrategicIndicatorsDepartmentTree({
      viewMode,
      branch,
      competence: referenceMonth,
      startDate,
      endDate,
      months: monthsToCompare,
      getAccessToken,
    });

  const loadingProgress = useSimulatedLoadingProgress(loading && !model);
  const refreshingProgress = useSimulatedLoadingProgress(Boolean(refreshing && model));

  const statusBadge =
    loading || refreshing ? (
      <LoadingActivityBadge label="Atualizando" tone="info" />
    ) : (
      <StatusBadge label="API Real" variant="success" />
    );

  return (
    <div className="si-departments-page si-departments-page--immersive">
      {loading && !model ? (
        <div className="si-departments-page__overlay">
          <LoadingActivityInline
            title="Carregando mapa departamental"
            description="Montando IGD, IDDs e indicadores com série dos últimos meses."
            variant="panel"
            tone="info"
            progressPercent={loadingProgress}
          />
        </div>
      ) : error && !model ? (
        <div className="si-departments-page__overlay">
          <StrategicIndicatorsPageError
            error={error}
            onAction={() => void reload()}
          />
        </div>
      ) : model ? (
        <>
          {refreshing ? (
            <div className="si-departments-page__refresh-banner">
              <LoadingActivityInline
                title="Atualizando mapa"
                description="Recalculando escopos para o novo filtro."
                variant="compact"
                tone="info"
                progressPercent={refreshingProgress}
              />
            </div>
          ) : null}

          {error ? (
            <div className="si-departments-page__refresh-banner">
              <StrategicIndicatorsPageError
                error={error}
                mode="refresh"
                onAction={() => void reload()}
              />
            </div>
          ) : null}

          <DepartmentIgdTree
            model={model}
            filterState={filterState}
            filterControls={{
              referenceMonth,
              viewMode,
              branch,
              treeScope,
              monthsToCompare,
              onReferenceMonthChange: setReferenceMonth,
              onViewModeChange: setViewMode,
              onBranchChange: setBranch,
              onTreeScopeChange: handleTreeScopeChange,
              onMonthsToCompareChange: setMonthsToCompare,
              status: statusBadge,
            }}
          />
        </>
      ) : null}
    </div>
  );
}
