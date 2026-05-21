import { LoadingActivityCard } from "./LoadingActivityCard";
import {
  EMPTY_REQUEST_PROGRESS,
  useLoadingProgress,
  type RequestProgress,
} from "../hooks/useSimulatedLoadingProgress";

type EngineeringStatusAlertsProps = {
  error: string | null;
  loading: boolean;
  hasData: boolean;
  requestProgress?: RequestProgress;
  onRetry: () => void;
};

export function EngineeringStatusAlerts({
  error,
  loading,
  hasData,
  requestProgress = EMPTY_REQUEST_PROGRESS,
  onRetry,
}: EngineeringStatusAlertsProps) {
  const loadingProgress = useLoadingProgress(
    loading && !hasData,
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

      {loading && !hasData ? (
        <LoadingActivityCard
          title="Carregando indicadores"
          description="Buscando dados de engenharia para o período e filial selecionados."
          progressPercent={loadingProgress}
        />
      ) : null}
    </>
  );
}
