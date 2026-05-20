import { LoadingActivityCard } from "./LoadingActivityCard";

type FinancialStatusAlertsProps = {
  error: string | null;
  loading: boolean;
  hasData: boolean;
  onRetry: () => void;
};

export function FinancialStatusAlerts({
  error,
  loading,
  hasData,
  onRetry,
}: FinancialStatusAlertsProps) {
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
          description="Buscando dados financeiros para o período e filial selecionados."
        />
      ) : null}
    </>
  );
}
