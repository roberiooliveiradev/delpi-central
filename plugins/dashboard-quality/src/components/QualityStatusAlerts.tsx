import { LoadingActivityCard } from "./LoadingActivityCard";
import {
  EMPTY_REQUEST_PROGRESS,
  useLoadingProgress,
  type RequestProgress,
} from "../hooks/useSimulatedLoadingProgress";

type QualityStatusAlertsProps = {
  error?: string | null;
  loading: boolean;
  refreshing?: boolean;
  hasData: boolean;
  requestProgress?: RequestProgress;
  onRetry?: () => void;
  refreshTitle?: string;
  refreshDescription?: string;
  initialTitle?: string;
  initialDescription?: string;
};

export function QualityStatusAlerts({
  error = null,
  loading,
  refreshing = false,
  hasData,
  requestProgress = EMPTY_REQUEST_PROGRESS,
  onRetry,
  refreshTitle = "Atualizando indicadores",
  refreshDescription = "Recalculando dados de qualidade com os filtros selecionados.",
  initialTitle = "Carregando indicadores",
  initialDescription = "Buscando dados de qualidade para o período selecionado.",
}: QualityStatusAlertsProps) {
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
        <div className="dq-state dq-state--error" role="alert">
          <p>{error}</p>
          {onRetry ? (
            <button className="dq-primary-btn" type="button" onClick={onRetry}>
              Tentar novamente
            </button>
          ) : null}
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
          title={initialTitle}
          description={initialDescription}
          progressPercent={loadingProgress}
        />
      ) : null}
    </>
  );
}
