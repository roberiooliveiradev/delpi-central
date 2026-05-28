import { useCallback } from "react";
import { Minus, Plus, Maximize2, RotateCcw } from "lucide-react";
import { useLoadingProgress } from "../hooks/useSimulatedLoadingProgress";
import {
  applyTreeScopeSelection,
  resolveActiveTreeScopeKey,
} from "../../data/departmentTreeScopes";
import type { DepartmentTreeScopeKey } from "../../data/types/departmentTree";
import { useStrategicIndicatorsFilters } from "../../state/hooks/useStrategicIndicatorsFilters";
import { DepartmentIgdTree } from "../components/DepartmentIgdTree";
import { StrategicIndicatorsPageError } from "../components/StrategicIndicatorsPageError";
import { InfoState } from "../components/InfoState";
import { StatusBadge } from "../components/StatusBadge";
import { LoadingActivityBadge } from "../components/LoadingActivityBadge";
import { LoadingActivityInline } from "../components/LoadingActivityInline";
import { RefreshSnapshotButton } from "../components/RefreshSnapshotButton";
import { TreeMapFloatingControls } from "../components/TreeMapFloatingControls";
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

  const { model, loading, refreshing, requestProgress, error, loadWarning, reload } =
    useStrategicIndicatorsDepartmentTree({
      viewMode,
      branch,
      competence: referenceMonth,
      startDate,
      endDate,
      months: monthsToCompare,
      getAccessToken,
    });

  const loadingProgress = useLoadingProgress(loading && !model, requestProgress);
  const refreshingProgress = useLoadingProgress(Boolean(refreshing && model), requestProgress);

  const statusBadge =
    loading || refreshing ? (
      <LoadingActivityBadge label="Atualizando" tone="info" />
    ) : (
      <StatusBadge label="API Real" variant="success" />
    );

  const disabledNav = (
    <div className="si-pan-zoom__nav" aria-label="Navegação do mapa">
      <button type="button" className="si-pan-zoom__nav-btn" disabled title="Diminuir zoom" aria-label="Diminuir zoom">
        <Minus size={16} />
      </button>
      <span className="si-pan-zoom__zoom-label">100%</span>
      <button type="button" className="si-pan-zoom__nav-btn" disabled title="Aumentar zoom" aria-label="Aumentar zoom">
        <Plus size={16} />
      </button>
      <button type="button" className="si-pan-zoom__nav-btn" disabled title="Tela cheia" aria-label="Entrar em tela cheia">
        <Maximize2 size={16} />
      </button>
      <button type="button" className="si-pan-zoom__nav-btn" disabled title="Ajustar à tela" aria-label="Ajustar à tela">
        <RotateCcw size={16} />
      </button>
      <button type="button" className="si-pan-zoom__nav-btn" disabled title="Zoom 100% e posição inicial" aria-label="Restaurar visualização">
        <span className="si-pan-zoom__reset-label">100%</span>
      </button>
    </div>
  );

  const disabledMapActions = (
    <div className="si-tree-view-toggle" role="group" aria-label="Expandir ou recolher organograma">
      <button type="button" className="si-tree-view-toggle__btn" disabled>
        Expandir tudo
      </button>
      <button type="button" className="si-tree-view-toggle__btn" disabled>
        Recolher tudo
      </button>
    </div>
  );

  const floatingControls = (
    <TreeMapFloatingControls
      referenceMonth={referenceMonth}
      viewMode={viewMode}
      branch={branch}
      treeScope={treeScope}
      monthsToCompare={monthsToCompare}
      onReferenceMonthChange={setReferenceMonth}
      onViewModeChange={setViewMode}
      onBranchChange={setBranch}
      onTreeScopeChange={handleTreeScopeChange}
      onMonthsToCompareChange={setMonthsToCompare}
      status={statusBadge}
      actions={!model ? disabledMapActions : undefined}
      headerActions={
        <RefreshSnapshotButton
          getAccessToken={getAccessToken}
          onRefreshed={() => void reload()}
          disabled={loading || refreshing}
        />
      }
      viewportNav={!model ? disabledNav : undefined}
    />
  );

  return (
    <div className="si-departments-page si-departments-page--immersive">
      {loading && !model ? (
        <>
          {floatingControls}
          <div className="si-departments-page__overlay">
            <LoadingActivityInline
              title="Carregando mapa departamental"
              description="Carregando estrutura (IGD e departamentos). Em seguida, séries históricas…"
              variant="panel"
              tone="info"
              progressPercent={loadingProgress}
            />
          </div>
        </>
      ) : error && !model ? (
        <>
          {floatingControls}
          <div className="si-departments-page__overlay">
            <StrategicIndicatorsPageError
              error={error}
              onAction={() => void reload()}
            />
          </div>
        </>
      ) : model ? (
        <>
          {refreshing ? (
            <div className="si-departments-page__refresh-banner">
              <LoadingActivityInline
                title="Atualizando mapa"
                description={
                  requestProgress.completed < requestProgress.total
                    ? "Carregando séries históricas (sparklines)…"
                    : "Recalculando escopos para o novo filtro."
                }
                variant="compact"
                tone="info"
                progressPercent={refreshingProgress}
              />
            </div>
          ) : null}

          {loadWarning ? (
            <div className="si-departments-page__refresh-banner">
              <InfoState
                title="Sparklines indisponíveis — estrutura do período carregada"
                description={`${loadWarning.summary}\n\n${loadWarning.suggestions.join(" ")}`}
                actionLabel="Tentar carregar séries"
                onAction={() => void reload()}
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
            extraActions={
              <RefreshSnapshotButton
                getAccessToken={getAccessToken}
                onRefreshed={() => void reload()}
                disabled={loading || refreshing}
              />
            }
          />
        </>
      ) : null}
    </div>
  );
}
