import { LoadingActivityCard } from "./LoadingActivityCard";
import { useSimulatedLoadingProgress } from "../hooks/useSimulatedLoadingProgress";

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
          description="Buscando dados de suprimentos para o período e filial selecionados."
          progressPercent={loadingProgress}
        />
      ) : null}
    </>
  );
}
