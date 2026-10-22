import { useCallback, useEffect, useRef, useState } from "react";
import {
  confirmRunHandoff,
  fetchRunHandoffPreview,
  isAuthError,
  type BenchSessionSnapshot,
  type ProductionRunSnapshot,
  type RunHandoffPreview,
  type RunHandoffResult,
} from "./api.ts";
import {
  handoffConflictView,
  handoffIntentSignature,
  isUncertainHandoffError,
  newHandoffRequestId,
  type HandoffConflictView,
  type RunHandoffIntent,
} from "./runHandoff.ts";

export type RunHandoffPhase =
  | "closed"
  | "previewing"
  | "ready"
  | "submitting"
  | "uncertain";

type Options = {
  token: string;
  branch: string;
  workCenter: string;
  /** Run ativo no contador deste posto — alvo do handoff. */
  run: ProductionRunSnapshot | null;
  session: BenchSessionSnapshot | null;
  /** 401 da E1: delega à invalidação de sessão já existente. */
  onAuthError?: () => void;
  /** Releitura do estado autoritativo (run ativo + fila) no owner do run. */
  onReconcile?: () => Promise<void> | void;
  /** Sucesso confirmado pelo POST (inclui replay idempotente). */
  onHandoffCompleted?: (result: RunHandoffResult) => void;
};

/**
 * Controlador da troca guiada (E2): prévia oficial + confirmação atômica
 * E1 com requestId por intenção. O mesmo controlador serve o card
 * "Agora nesta bancada" e o detalhe da operação (E2.RQ-01).
 */
export function useRunHandoff({
  token,
  branch,
  workCenter,
  run,
  session,
  onAuthError,
  onReconcile,
  onHandoffCompleted,
}: Options) {
  const [phase, setPhase] = useState<RunHandoffPhase>("closed");
  const [preview, setPreview] = useState<RunHandoffPreview | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  /** 409 estruturado do último POST — ação sugerida em `action`. */
  const [conflict, setConflict] = useState<HandoffConflictView | null>(null);
  /** Aviso informativo após revalidação automática (stale/queue_changed). */
  const [notice, setNotice] = useState<string | null>(null);
  const [uncertainMessage, setUncertainMessage] = useState<string | null>(null);
  const runIdRef = useRef<string | null>(null);
  const intentRef = useRef<RunHandoffIntent | null>(null);
  const submitInFlightRef = useRef(false);
  const requestRef = useRef({ token, branch, workCenter });

  useEffect(() => {
    requestRef.current = { token, branch, workCenter };
  }, [token, branch, workCenter]);

  const dropStaleSession = useCallback(
    (err: unknown) => {
      if (!isAuthError(err)) return;
      onAuthError?.();
    },
    [onAuthError],
  );

  const loadPreview = useCallback(async () => {
    const runId = runIdRef.current;
    const sessionToken = session?.sessionToken;
    if (!runId || !sessionToken) return;
    const request = requestRef.current;
    try {
      const data = await fetchRunHandoffPreview(
        request.token,
        sessionToken,
        runId,
        { branch: request.branch, workCenter: request.workCenter },
      );
      if (runIdRef.current !== runId) return;
      setPreview(data);
      setPreviewError(null);
      setPhase("ready");
    } catch (err) {
      if (runIdRef.current !== runId) return;
      dropStaleSession(err);
      setPreviewError(
        err instanceof Error ? err.message : "Prévia da troca indisponível.",
      );
      // Falha da prévia não impede o encerramento tradicional (E2.RQ-03).
      setPhase("ready");
    }
  }, [session?.sessionToken, dropStaleSession]);

  const open = useCallback(() => {
    if (!run) return;
    runIdRef.current = run.id;
    intentRef.current = null;
    setPreview(null);
    setPreviewError(null);
    setConflict(null);
    setNotice(null);
    setUncertainMessage(null);
    setPhase("previewing");
    void loadPreview();
  }, [run, loadPreview]);

  const refreshPreview = useCallback(() => {
    setConflict(null);
    setNotice(null);
    setPhase("previewing");
    void loadPreview();
  }, [loadPreview]);

  /**
   * Fechamento seguro: durante o envio o modal não fecha (intenção em
   * voo); em resultado incerto reconcilia antes de sair — nunca gera
   * nova chave para contornar resposta desconhecida (E2.RQ-06).
   */
  const close = useCallback(() => {
    if (submitInFlightRef.current) return;
    if (phase === "uncertain") {
      void onReconcile?.();
    }
    runIdRef.current = null;
    intentRef.current = null;
    setPhase("closed");
    setPreview(null);
    setPreviewError(null);
    setConflict(null);
    setNotice(null);
    setUncertainMessage(null);
  }, [phase, onReconcile]);

  const confirmNext = useCallback(async () => {
    const runId = runIdRef.current;
    const sessionToken = session?.sessionToken;
    const next = preview?.nextOperation ?? null;
    if (!runId || !sessionToken || !next || submitInFlightRef.current) return;

    // Nova escolha explícita = nova intenção; mesma assinatura após
    // resultado incerto = retry da MESMA intenção (mesmo requestId).
    const signature = handoffIntentSignature({ expectedNext: next });
    if (
      !intentRef.current ||
      handoffIntentSignature(intentRef.current) !== signature
    ) {
      intentRef.current = {
        requestId: newHandoffRequestId(),
        expectedNext: {
          productionOrder: next.productionOrder,
          operationCode: next.operationCode,
        },
      };
    }
    const intent = intentRef.current;

    submitInFlightRef.current = true;
    setPhase("submitting");
    setUncertainMessage(null);
    setConflict(null);
    const request = requestRef.current;
    try {
      const result = await confirmRunHandoff(request.token, sessionToken, runId, {
        requestId: intent.requestId,
        branch: request.branch,
        workCenter: request.workCenter,
        expectedNext: intent.expectedNext,
      });
      intentRef.current = null;
      runIdRef.current = null;
      setPhase("closed");
      setPreview(null);
      // O run novo já nasceu running — reconcilia contagem/fila e navega.
      try {
        await onReconcile?.();
      } finally {
        onHandoffCompleted?.(result);
      }
    } catch (err) {
      dropStaleSession(err);
      if (isUncertainHandoffError(err)) {
        // Rede/timeout/502/503: a transação pode ter commitado. Retry
        // com o mesmo requestId resolve (replay devolve o resultado).
        setUncertainMessage(
          "A resposta não chegou — a troca pode ter sido concluída. " +
            "Tente novamente com o mesmo pedido ou atualize o painel.",
        );
        setPhase("uncertain");
        return;
      }
      const apiErr = err as { code?: string; message?: string };
      const view = handoffConflictView(apiErr.code, apiErr.message);
      if (view.action === "refresh_preview") {
        // Prévia nova + nova escolha explícita = nova intenção.
        intentRef.current = null;
        setNotice(view.message);
        setPhase("previewing");
        void loadPreview();
        return;
      }
      if (view.action === "reconcile") {
        intentRef.current = null;
        setConflict(view);
        void onReconcile?.();
        setPhase("ready");
        return;
      }
      // "classify"/"none": conflito final — nova escolha = nova chave.
      intentRef.current = null;
      setConflict(view);
      setPhase("ready");
    } finally {
      submitInFlightRef.current = false;
    }
  }, [
    preview,
    session?.sessionToken,
    loadPreview,
    dropStaleSession,
    onReconcile,
    onHandoffCompleted,
  ]);

  return {
    phase,
    isOpen: phase !== "closed",
    preview,
    previewError,
    previewing: phase === "previewing",
    submitting: phase === "submitting",
    uncertain: phase === "uncertain",
    conflict,
    notice,
    uncertainMessage,
    open,
    refreshPreview,
    close,
    confirmNext,
  };
}
