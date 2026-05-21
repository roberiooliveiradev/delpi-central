import { LoadingActivityCard } from "./LoadingActivityCard";

type StatusAlertsProps = {
  error: string | null;
  loading: boolean;
  hasData: boolean;
  onRetry: () => void;
};

export function StatusAlerts({ error, loading, hasData, onRetry }: StatusAlertsProps) {
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
        />
      ) : null}
    </>
  );
}
