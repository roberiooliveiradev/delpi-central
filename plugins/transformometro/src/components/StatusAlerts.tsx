import { StateBox } from "./StateBox";
import { LoadingActivityCard } from "./LoadingActivityCard";
import {
  EMPTY_REQUEST_PROGRESS,
  useLoadingProgress,
  type RequestProgress,
} from "../hooks/useSimulatedLoadingProgress";

type StatusAlertsProps = {
  error: string | null;
  loading: boolean;
  hasData: boolean;
  requestProgress?: RequestProgress;
  onRetry: () => void;
  /** Título do loading inicial (quando ainda não há dados). */
  loadingTitle?: string;
  loadingDescription?: string;
};

export function StatusAlerts({
  error,
  loading,
  hasData,
  requestProgress = EMPTY_REQUEST_PROGRESS,
  onRetry,
  loadingTitle = "Carregando indicadores",
  loadingDescription = "Buscando economia, evolução mensal e ranking de processos.",
}: StatusAlertsProps) {
  const loadingProgress = useLoadingProgress(loading && !hasData, requestProgress);

  return (
    <>
      {error ? (
        <StateBox variant="error" dismissible={false}>
          <p>{error}</p>
          <button className="ds-primary-btn" type="button" onClick={onRetry}>
            Tentar novamente
          </button>
        </StateBox>
      ) : null}

      {loading && !hasData ? (
        <LoadingActivityCard
          title={loadingTitle}
          description={loadingDescription}
          progressPercent={loadingProgress}
        />
      ) : null}
    </>
  );
}
