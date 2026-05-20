import { LoadingActivityCard } from "./LoadingActivityCard";

type SuppliesStatusAlertsProps = {
  error: string | null;
  loading: boolean;
  hasData: boolean;
  onRetry: () => void;
};

export function SuppliesStatusAlerts({
  error,
  loading,
  hasData,
  onRetry,
}: SuppliesStatusAlertsProps) {
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
          description="Buscando dados de suprimentos para o período e filial selecionados."
        />
      ) : null}
    </>
  );
}
