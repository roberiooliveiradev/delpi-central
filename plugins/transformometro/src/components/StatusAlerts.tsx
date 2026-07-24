import { useEffect, useRef } from "react";

import { LoadingActivityCard } from "./LoadingActivityCard";
import {
  EMPTY_REQUEST_PROGRESS,
  useLoadingProgress,
  type RequestProgress,
} from "../hooks/useSimulatedLoadingProgress";
import {
  PAGE_ERROR_NOTICE_ID,
  useFloatingNotice,
} from "./ui/FloatingNoticeProvider";

type StatusAlertsProps = {
  error: string | null;
  loading: boolean;
  hasData: boolean;
  requestProgress?: RequestProgress;
  onRetry: () => void;
  /** Limpa o erro no estado do pai ao fechar o toast. */
  onDismissError?: () => void;
  /** Título do toast de erro. */
  errorTitle?: string;
  /** Título do loading inicial (quando ainda não há dados). */
  loadingTitle?: string;
  loadingDescription?: string;
};

/**
 * Erros de página → `FloatingNotice` (mesmo componente de sucesso/export).
 * Erro/aviso não somem com o tempo — só com fechar ou «Tentar novamente».
 * Loading inicial continua no card inline.
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
  const { notifyError, dismissPageError } = useFloatingNotice();
  const onRetryRef = useRef(onRetry);
  const onDismissErrorRef = useRef(onDismissError);
  onRetryRef.current = onRetry;
  onDismissErrorRef.current = onDismissError;

  useEffect(() => {
    if (!error) {
      dismissPageError();
      return;
    }
    notifyError(error, {
      id: PAGE_ERROR_NOTICE_ID,
      title: errorTitle,
      actionLabel: "Tentar novamente",
      onAction: () => {
        onDismissErrorRef.current?.();
        dismissPageError();
        onRetryRef.current();
      },
      onClose: () => {
        onDismissErrorRef.current?.();
      },
    });
  }, [error, errorTitle, notifyError, dismissPageError]);

  return (
    <>
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
