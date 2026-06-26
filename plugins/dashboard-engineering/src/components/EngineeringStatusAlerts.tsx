import { LoadingActivityCard } from "./LoadingActivityCard";
import {
  EMPTY_REQUEST_PROGRESS,
  useLoadingProgress,
  type RequestProgress,
} from "../hooks/useSimulatedLoadingProgress";

type EngineeringStatusAlertsProps = {
  error: string | null;
  loading: boolean;
  refreshing?: boolean;
  hasData: boolean;
  requestProgress?: RequestProgress;
  onRetry: () => void;
  refreshTitle?: string;
  refreshDescription?: string;
};

export function EngineeringStatusAlerts({
  error,
  loading,
  refreshing = false,
  hasData,
  requestProgress = EMPTY_REQUEST_PROGRESS,
  onRetry,
  refreshTitle = "Atualizando indicadores",
  refreshDescription = "Recalculando dados de engenharia com os filtros selecionados.",
}: EngineeringStatusAlertsProps) {
  const loadingProgress = useLoadingProgress(
    loading && !hasData,
    requestProgress
  );
  const refreshProgress = useLoadingProgress(
    refreshing && hasData,
    requestProgress
  );

  return (
    <>
      {error ? (
        <div className="ds-state ds-state--error" role="alert">
          <p>{error}</p>
          <button className="ds-primary-btn" type="button" onClick={onRetry}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      {refreshing && hasData ? (
        <LoadingActivityCard
          title={refreshTitle}
          description={refreshDescription}
          variant="compact"
          sticky
          progressPercent={refreshProgress}
        />
      ) : null}

      {loading && !hasData ? (
        <LoadingActivityCard
          title="Carregando indicadores"
          description="Buscando dados de engenharia para o período e unidade selecionados."
          progressPercent={loadingProgress}
        />
      ) : null}
    </>
  );
}
