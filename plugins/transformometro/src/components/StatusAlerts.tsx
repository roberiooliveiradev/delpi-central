import { useEffect, useState } from "react";

import { InlineErrorState } from "./ErrorStateBox";
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
  /** Limpa o erro no estado do pai ao fechar (recomendado). */
  onDismissError?: () => void;
  /** Título do painel de erro (kit StateBoxPanel). */
  errorTitle?: string;
  /** Título do loading inicial (quando ainda não há dados). */
  loadingTitle?: string;
  loadingDescription?: string;
};

/**
 * Erros permanecem até o usuário fechar (X) ou tentar novamente —
 * não há auto-dismiss por tempo.
 */
export function StatusAlerts({
  error,
  loading,
  hasData,
  requestProgress = EMPTY_REQUEST_PROGRESS,
  onRetry,
  onDismissError,
  errorTitle = "Não foi possível carregar",
  loadingTitle = "Carregando indicadores",
  loadingDescription = "Buscando economia, evolução mensal e ranking de processos.",
}: StatusAlertsProps) {
  const loadingProgress = useLoadingProgress(loading && !hasData, requestProgress);
  const [dismissedError, setDismissedError] = useState<string | null>(null);

  useEffect(() => {
    if (error == null) {
      setDismissedError(null);
    }
  }, [error]);

  const visibleError = error && error !== dismissedError ? error : null;

  return (
    <>
      {visibleError ? (
        <InlineErrorState
          title={errorTitle}
          message={visibleError}
          onAction={() => {
            setDismissedError(null);
            onRetry();
          }}
          onDismiss={() => {
            setDismissedError(visibleError);
            onDismissError?.();
          }}
        />
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
