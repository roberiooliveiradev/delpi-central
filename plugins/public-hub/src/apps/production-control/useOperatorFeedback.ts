import { useCallback, useEffect, useRef, useState } from "react";
import {
  ApiError,
  createOperatorFeedback,
  fetchActiveOperatorFeedbacks,
  isAuthError,
  type PublicOperatorFeedback,
} from "./api.ts";
import {
  DEFAULT_FEEDBACK_REASON,
  DEFAULT_FEEDBACK_TYPE,
  feedbackSubmitErrorMessage,
  firstActiveFeedback,
  isFeedbackEventForOperation,
} from "./operatorFeedback.ts";
import type { MachineLoadRealtimeEvent } from "./usePublicMachineLoadRealtime.ts";

const OFFLINE_POLL_MS = 30_000;

type Options = {
  token: string;
  productionOrder: string;
  operationCode: string;
  /** sessionToken da bench session; null enquanto não identificado. */
  sessionToken: string | null;
  realtimeConnected: boolean;
  /** Hint realtime do cockpit — filtrado por OP/operação antes de refetch. */
  feedbackRealtimeEvent: MachineLoadRealtimeEvent | null;
  /** Sinal de ressincronização (ex.: socket reconectou após hints perdidos). */
  resyncSignal: number;
  /** 401 em qualquer chamada → descarta a sessão local no provider. */
  onAuthError?: () => void;
};

export type FeedbackSubmitResult = {
  /** true = impedimento registrado (ou já existente — 409 convergido). */
  ok: boolean;
  /** Mensagem amigável quando ok=false; null em sucesso. */
  message: string | null;
};

export type OperatorFeedbackState = {
  active: PublicOperatorFeedback | null;
  loading: boolean;
  error: string | null;
  submitting: boolean;
  /** Mensagem amigável transitória (409, 404, sessão expirada). */
  notice: string | null;
  refresh: () => Promise<void>;
  submit: (note: string | null) => Promise<FeedbackSubmitResult>;
  dismissNotice: () => void;
};

/**
 * Estado do Operator Feedback da operação aberta. Só consulta quando há
 * sessão; protege contra resposta obsoleta na troca rápida de OP e faz
 * polling leve apenas enquanto o WebSocket estiver offline.
 */
export function useOperatorFeedback({
  token,
  productionOrder,
  operationCode,
  sessionToken,
  realtimeConnected,
  feedbackRealtimeEvent,
  resyncSignal,
  onAuthError,
}: Options): OperatorFeedbackState {
  const [active, setActive] = useState<PublicOperatorFeedback | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const requestSeq = useRef(0);

  const handleAuth = useCallback(
    (err: unknown): boolean => {
      if (!isAuthError(err)) return false;
      setNotice(feedbackSubmitErrorMessage(401));
      onAuthError?.();
      return true;
    },
    [onAuthError],
  );

  const refresh = useCallback(async () => {
    if (!sessionToken) return;
    const seq = ++requestSeq.current;
    const order = productionOrder;
    const code = operationCode;
    try {
      const items = await fetchActiveOperatorFeedbacks(
        token,
        sessionToken,
        order,
        code,
      );
      // OP mudou enquanto o request voava — a resposta é da operação anterior.
      if (
        seq !== requestSeq.current ||
        order !== productionOrder ||
        code !== operationCode
      ) {
        return;
      }
      setActive(firstActiveFeedback(items));
      setError(null);
    } catch (err) {
      if (handleAuth(err)) return;
      if (seq === requestSeq.current) {
        setError(
          err instanceof Error ? err.message : "Avisos ao PCP indisponíveis.",
        );
      }
    }
  }, [token, sessionToken, productionOrder, operationCode, handleAuth]);

  // Troca de OP ou de sessão: limpa o estado da operação anterior e recarrega.
  useEffect(() => {
    requestSeq.current += 1;
    queueMicrotask(() => {
      setActive(null);
      setError(null);
      setNotice(null);
      if (!sessionToken) {
        setLoading(false);
        return;
      }
      setLoading(true);
      void refresh().finally(() => setLoading(false));
    });
  }, [sessionToken, productionOrder, operationCode, refresh]);

  // Hint realtime: só refetch quando o evento é desta OP/operação.
  useEffect(() => {
    if (!feedbackRealtimeEvent || !sessionToken) return;
    if (
      isFeedbackEventForOperation(
        feedbackRealtimeEvent,
        productionOrder,
        operationCode,
      )
    ) {
      queueMicrotask(() => void refresh());
    }
  }, [
    feedbackRealtimeEvent,
    sessionToken,
    productionOrder,
    operationCode,
    refresh,
  ]);

  // Reconexão do socket: hints podem ter se perdido — ressincroniza via HTTP.
  const firstResync = useRef(true);
  useEffect(() => {
    if (firstResync.current) {
      firstResync.current = false;
      return;
    }
    if (sessionToken) queueMicrotask(() => void refresh());
  }, [resyncSignal, sessionToken, refresh]);

  // Fallback leve: WS offline → polling 30s só desta OP; HTTP segue a verdade.
  useEffect(() => {
    if (realtimeConnected || !sessionToken) return;
    const timer = window.setInterval(() => {
      if (document.visibilityState === "hidden") return;
      void refresh();
    }, OFFLINE_POLL_MS);
    return () => window.clearInterval(timer);
  }, [realtimeConnected, sessionToken, refresh]);

  const submit = useCallback(
    async (note: string | null): Promise<FeedbackSubmitResult> => {
      if (!sessionToken || submitting) {
        return { ok: false, message: null };
      }
      setSubmitting(true);
      setNotice(null);
      try {
        const created = await createOperatorFeedback(token, sessionToken, {
          productionOrder,
          operationCode,
          feedbackType: DEFAULT_FEEDBACK_TYPE,
          reasonCode: DEFAULT_FEEDBACK_REASON,
          note,
        });
        setActive(created);
        setError(null);
        return { ok: true, message: null };
      } catch (err) {
        if (handleAuth(err)) {
          return { ok: false, message: feedbackSubmitErrorMessage(401) };
        }
        const status = err instanceof ApiError ? err.status : null;
        const message = feedbackSubmitErrorMessage(status);
        setNotice(message);
        if (status === 409) {
          // Constraint da C1 venceu: o impedimento já existe — ressincroniza.
          void refresh();
          return { ok: true, message };
        }
        return { ok: false, message };
      } finally {
        setSubmitting(false);
      }
    },
    [
      token,
      sessionToken,
      submitting,
      productionOrder,
      operationCode,
      handleAuth,
      refresh,
    ],
  );

  return {
    active,
    loading,
    error,
    submitting,
    notice,
    refresh,
    submit,
    dismissNotice: () => setNotice(null),
  };
}
