import { LoadingActivityCard } from "./LoadingActivityCard";
import { useSimulatedLoadingProgress } from "../hooks/useSimulatedLoadingProgress";

type StatusAlertsProps = {
  error: string | null;
  loading: boolean;
  hasData: boolean;
  onRetry: () => void;
};

export function StatusAlerts({ error, loading, hasData, onRetry }: StatusAlertsProps) {
  const loadingProgress = useSimulatedLoadingProgress(loading && !hasData);

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
          description="Buscando economia, evolução mensal e ranking de processos."
          progressPercent={loadingProgress}
        />
      ) : null}
    </>
  );
}
