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
  clearPendingHandoffIntent,
  handoffConflictView,
  handoffIntentSignature,
  isUncertainHandoffError,
  newHandoffRequestId,
  pendingHandoffIntentFor,
  registerPendingHandoffIntent,
  type HandoffConflictView,
  type RunHandoffIntent,
} from "./runHandoff.ts";

export type RunHandoffPhase =
  | "closed"
  | "previewing"
  | "ready"
  | "submitting"
  | "uncertain";

const UNCERTAIN_MESSAGE =
  "A resposta não chegou — a troca pode ter sido concluída. " +
  "Tente novamente com o mesmo pedido ou atualize o painel.";

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
 *
 * A intenção pendente (resultado desconhecido) NÃO vive só neste hook:
 * `pendingHandoffIntents` em runHandoff.ts é module-level e sobrevive a
 * remount ao alternar card ↔ detalhe — reabrir a finalização restaura a
 * tela de retry com o mesmo requestId em vez de iniciar uma nova intenção.
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
  /**
   * Identidade imutável: o modal fica vinculado ao run que o abriu.
   * Se uma reconciliação substituir o run ativo, a decisão antiga é
   * invalidada — o Stop do sheet nunca pode atingir o novo run.
   */
  const [boundRunId, setBoundRunId] = useState<string | null>(null);
  const runIdRef = useRef<string | null>(null);
  const intentRef = useRef<RunHandoffIntent | null>(null);
  const submitInFlightRef = useRef(false);
  const requestRef = useRef({ token, branch, workCenter });

  useEffect(() => {
    requestRef.current = { token, branch, workCenter };
  }, [token, branch, workCenter]);

  /**
   * Há intenção com resultado desconhecido para ESTE run — bloqueia
   * escritas contraditórias (Pause/Resume/Stop) mesmo com o modal
   * fechado. Derivado do registro do módulo: sobrevive a remount e a F5
   * (o registro reidrata do sessionStorage), e toda mutação do registro
   * neste hook vem acompanhada de setState — a derivação é consistente.
   */
  const unresolvedIntent =
    run != null && pendingHandoffIntentFor(run.id) != null;

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
    // Identidade vinculada: a decisão vale apenas para este run.
    setBoundRunId(run.id);
    setPreview(null);
    setPreviewError(null);
    setConflict(null);
    setNotice(null);
    // Intenção pendente (resultado desconhecido) sobrevive a fechar a
    // tela, a remounts e a F5: reabrir a finalização restaura a tela de
    // retry com o MESMO requestId — nunca inicia intenção nova por cima.
    const pending = pendingHandoffIntentFor(run.id);
    if (pending) {
      intentRef.current = pending;
      setUncertainMessage(UNCERTAIN_MESSAGE);
      setPhase("uncertain");
      return;
    }
    intentRef.current = null;
    setUncertainMessage(null);
    setPhase("previewing");
    void loadPreview();
  }, [run, loadPreview]);

  const refreshPreview = useCallback(() => {
    if (phase === "uncertain" || submitInFlightRef.current) return;
    setConflict(null);
    setNotice(null);
    setPhase("previewing");
    void loadPreview();
  }, [phase, loadPreview]);

  /**
   * Fechamento seguro: durante o envio o modal não fecha (intenção em
   * voo); em resultado incerto reconcilia antes de sair e MANTÉM a
   * intenção no registro module-level — reabrir a finalização retoma o
   * retry com o mesmo requestId (E2.RQ-06).
   */
  const close = useCallback(() => {
    if (submitInFlightRef.current) return;
    if (phase === "uncertain") {
      void onReconcile?.();
    }
    runIdRef.current = null;
    intentRef.current = null;
    setBoundRunId(null);
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
    if (!runId || !sessionToken || submitInFlightRef.current) return;

    let intent: RunHandoffIntent | null;
    if (phase === "uncertain") {
      // Resultado desconhecido: a ÚNICA escrita permitida é reenviar a
      // intenção guardada — mesmo requestId, mesmo payload. A prévia
      // (que pode estar velha) nunca define o alvo do retry.
      intent =
        intentRef.current ?? pendingHandoffIntentFor(runId) ?? null;
      if (!intent) return;
    } else {
      // Validação interna — não basta o `disabled` do botão: só a fase
      // ready, com prévia elegível e sem conflito impeditivo, autoriza
      // a escrita. Conflitos impeditivos exigem a recuperação prevista
      // no contrato (classificar, reconciliar, prévia nova).
      if (phase !== "ready") return;
      if (previewError != null) return;
      if (preview == null || preview.available !== true) return;
      if (conflict?.blocksNext) return;
      const next = preview.nextOperation;
      if (!next) return;

      // Nova escolha explícita = nova intenção; mesma assinatura reusa
      // a intenção corrente (mesmo requestId).
      const signature = handoffIntentSignature({ expectedNext: next });
      if (
        intentRef.current &&
        handoffIntentSignature(intentRef.current) === signature
      ) {
        intent = intentRef.current;
      } else {
        const requestId = newHandoffRequestId();
        if (!requestId) {
          // Sem Web Crypto não há chave segura — falha recuperável,
          // nenhuma escrita é enviada com identificador fraco.
          setPreviewError(
            "Este dispositivo não gerou um identificador seguro. " +
              "Atualize o aplicativo do painel e tente novamente.",
          );
          return;
        }
        const request = requestRef.current;
        intent = {
          requestId,
          expectedNext: {
            productionOrder: next.productionOrder,
            operationCode: next.operationCode,
          },
          branch: request.branch,
          workCenter: request.workCenter,
        };
        intentRef.current = intent;
      }
    }

    // Marca a intenção como pendente ANTES do POST: se a interface
    // fechar ou remontar com a resposta desconhecida, a intenção não
    // se perde — reabrir restaura o retry da mesma chave.
    registerPendingHandoffIntent(runId, intent);
    submitInFlightRef.current = true;
    setPhase("submitting");
    setUncertainMessage(null);
    setConflict(null);
    try {
      // O POST usa o contexto CONGELADO da intenção — uma troca de CT
      // durante o retry não muda o payload original.
      const result = await confirmRunHandoff(
        requestRef.current.token,
        sessionToken,
        runId,
        {
          requestId: intent.requestId,
          branch: intent.branch,
          workCenter: intent.workCenter,
          expectedNext: intent.expectedNext,
        },
      );
      clearPendingHandoffIntent(runId);
      intentRef.current = null;
      runIdRef.current = null;
      setBoundRunId(null);
      setPhase("closed");
      setPreview(null);
      // O run novo já nasceu running — reconcilia contagem/fila e navega.
      // Falha do GET posterior ≠ falha da mutação: a troca já foi
      // confirmada pelo backend e o resultado é preservado; a atualização
      // visual é recuperada pela leitura, nunca por um novo POST.
      try {
        await onReconcile?.();
      } catch {
        /* readback falhou — atualização pendente fica com o cockpit */
      }
      onHandoffCompleted?.(result);
    } catch (err) {
      dropStaleSession(err);
      if (isUncertainHandoffError(err)) {
        // Rede/timeout/502/503: a transação pode ter commitado. A
        // intenção fica registrada; o retry repete o MESMO requestId
        // (replay devolve o resultado gravado). Nenhuma outra escrita
        // é permitida até a resolução.
        setUncertainMessage(UNCERTAIN_MESSAGE);
        setPhase("uncertain");
        return;
      }
      const apiErr = err as { code?: string; message?: string };
      const view = handoffConflictView(apiErr.code, apiErr.message);
      // Resposta definitiva: a intenção morre e a próxima escolha
      // explícita gerará nova chave.
      clearPendingHandoffIntent(runId);
      intentRef.current = null;
      if (view.action === "refresh_preview") {
        // Prévia nova + nova escolha explícita = nova intenção.
        setNotice(view.message);
        setPhase("previewing");
        void loadPreview();
        return;
      }
      if (view.action === "reconcile") {
        // O run não está mais ativo nesta posição: a prévia velha é
        // descartada e o estado autoritativo é relido.
        setPreview(null);
        setConflict(view);
        void onReconcile?.();
        setPhase("ready");
        return;
      }
      // "classify"/"none": conflito impeditivo — `blocksNext` trava
      // qualquer nova escrita até a recuperação prevista.
      setConflict(view);
      setPhase("ready");
    } finally {
      submitInFlightRef.current = false;
    }
  }, [
    phase,
    preview,
    previewError,
    conflict,
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
    /** Run ao qual a decisão do modal está vinculada — imutável. */
    boundRunId,
    /** Intenção com resultado desconhecido — bloqueia escritas fora do modal. */
    unresolvedIntent,
    open,
    refreshPreview,
    close,
    confirmNext,
  };
}
