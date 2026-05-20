import { LoadingActivityCard } from "./LoadingActivityCard";

type EngineeringStatusAlertsProps = {
  error: string | null;
  loading: boolean;
  hasData: boolean;
  onRetry: () => void;
};

export function EngineeringStatusAlerts({
  error,
  loading,
  hasData,
  onRetry,
}: EngineeringStatusAlertsProps) {
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
          description="Buscando LMPs e TRANSFORMA+ para o período e filial selecionados."
        />
      ) : null}
    </>
  );
}
