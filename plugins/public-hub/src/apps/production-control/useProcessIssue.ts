import { useCallback, useRef, useState } from "react";
import {
  ApiError,
  createProcessIssue,
  isAuthError,
  type PublicProcessIssueConfirmation,
} from "./api.ts";
import {
  beginProcessIssueAttempt,
  processIssueSubmitErrorMessage,
  submitKeyForDraft,
  type ProcessIssueAttempt,
  type ProcessIssueDraft,
} from "./processIssue.ts";

type Options = {
  token: string;
  productionOrder: string;
  operationCode: string;
  /** sessionToken da bench session; null enquanto não identificado. */
  sessionToken: string | null;
  /** 401 → descarta a sessão local no provider. */
  onAuthError?: () => void;
  /** Injetável em testes — default é o client real da P2. */
  submitApi?: (
    token: string,
    sessionToken: string,
    idempotencyKey: string,
    body: {
      productionOrder: string;
      operationCode: string;
      issueCode: string;
      toolCode?: string | null;
      materialCode?: string | null;
      note?: string | null;
    },
  ) => Promise<PublicProcessIssueConfirmation>;
  generateKey?: () => string;
};

export type ProcessIssueSubmitResult = {
  ok: boolean;
  message: string | null;
};

export type ProcessIssueConfirmation = {
  requestNumber: string | null;
};

export type ProcessIssueState = {
  submitting: boolean;
  /** Confirmação do último envio — banner na central; sem acompanhamento. */
  confirmation: ProcessIssueConfirmation | null;
  /** Abre uma tentativa lógica (modal abre) — gera a Idempotency-Key. */
  beginAttempt: () => void;
  /** Encerra a tentativa sem sucesso (cancelar/fechar) — descarta a chave. */
  cancelAttempt: () => void;
  clearConfirmation: () => void;
  submit: (draft: ProcessIssueDraft) => Promise<ProcessIssueSubmitResult>;
};

/**
 * Envio de «Problema de Processo» (P3). Sem polling/realtime/acompanhamento:
 * o operador reporta e segue trabalhando. A Idempotency-Key é gerada por
 * tentativa (beginAttempt) e reutilizada apenas em retry do MESMO payload —
 * o backend permanece soberano na dedup ponta a ponta.
 */
export function useProcessIssue({
  token,
  productionOrder,
  operationCode,
  sessionToken,
  onAuthError,
  submitApi = createProcessIssue,
  generateKey,
}: Options): ProcessIssueState {
  const [submitting, setSubmitting] = useState(false);
  const [confirmation, setConfirmation] =
    useState<ProcessIssueConfirmation | null>(null);
  const attemptRef = useRef<ProcessIssueAttempt | null>(null);
  // Guard síncrono — `submitting` (state) não protege dois cliques no mesmo tick.
  const submittingRef = useRef(false);

  const beginAttempt = useCallback(() => {
    attemptRef.current = beginProcessIssueAttempt(generateKey);
  }, [generateKey]);

  const cancelAttempt = useCallback(() => {
    attemptRef.current = null;
  }, []);

  const clearConfirmation = useCallback(() => {
    setConfirmation(null);
  }, []);

  const submit = useCallback(
    async (draft: ProcessIssueDraft): Promise<ProcessIssueSubmitResult> => {
      if (!sessionToken || submittingRef.current) {
        return { ok: false, message: null };
      }
      submittingRef.current = true;
      if (!attemptRef.current) {
        attemptRef.current = beginProcessIssueAttempt(generateKey);
      }
      const resolved = submitKeyForDraft(
        attemptRef.current,
        draft,
        generateKey,
      );
      attemptRef.current = resolved.attempt;

      setSubmitting(true);
      try {
        const created = await submitApi(token, sessionToken, resolved.key, {
          productionOrder,
          operationCode,
          issueCode: draft.issueCode,
          toolCode: draft.toolCode ?? null,
          materialCode: draft.materialCode ?? null,
          note: draft.note ?? null,
        });
        // Sucesso encerra a tentativa — nova abertura gerará outra chave.
        attemptRef.current = null;
        setConfirmation({ requestNumber: created.requestNumber });
        return { ok: true, message: null };
      } catch (err) {
        if (isAuthError(err)) {
          onAuthError?.();
          return { ok: false, message: processIssueSubmitErrorMessage(401) };
        }
        const status = err instanceof ApiError ? err.status : null;
        return {
          ok: false,
          message: processIssueSubmitErrorMessage(
            status,
            err instanceof Error ? err.message : null,
          ),
        };
      } finally {
        submittingRef.current = false;
        setSubmitting(false);
      }
    },
    [
      token,
      sessionToken,
      productionOrder,
      operationCode,
      submitApi,
      generateKey,
      onAuthError,
    ],
  );

  return {
    submitting,
    confirmation,
    beginAttempt,
    cancelAttempt,
    clearConfirmation,
    submit,
  };
}
