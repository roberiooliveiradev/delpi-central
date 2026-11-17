/** Routing Study V2 — estado do rascunho de sessão.
 *
 * Responsabilidades:
 * - montar a chave por identidade+contexto (produto/filial/estágio);
 * - restaurar rascunho válido após refresh (`restored`), descartar
 *   inválidos com aviso honesto (`restore_invalid`, `stale_reference`);
 * - autosave com debounce + flush em `visibilitychange`/unmount,
 *   comunicando `saving/saved/save_error` somente após escrita real;
 * - operações de cenário (A/B/C… — Novo cenário preserva o anterior)
 *   e de postos hipotéticos (adicionar/renomear/remover/ordenar/
 *   vincular operações oficiais);
 * - `Limpar estudo`: remove só a chave do contexto e reseta o estado.
 *
 * Resultados de cálculo (`computed`) são transitórios — nunca são
 * persistidos nem restaurados como `CALCULATED` atuais (contrato
 * session-state §1.2/§6 ST-05). */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import type { ProductLineBalanceResult } from "../types";
import {
  buildStorageKey,
  computeSourceFingerprint,
  emptyDraft,
  inputsFingerprint,
  loadDraft,
  emptyInputs,
  newClientId,
  newScenarioDraft,
  parseDraft,
  removeDraft,
  saveDraft,
  SCENARIO_LABELS,
  STUDY_MAX_POSTS,
  STUDY_MAX_SCENARIOS,
  type HypotheticalPost,
  type RoutingStudyDraft,
  type StudyDraftContext,
  type StudyInputs,
  type StudyMode,
  type StudyScenarioDraft,
} from "./routingStudyDraft";
import type { RoutingStageView } from "./routingGrouping";

export type BalanceRunParams = {
  demand: number;
  available_minutes: number;
  num_stations?: number;
  batch_size?: number;
  branch?: string;
};

/** Resultado transitório — vive só em memória; marcado STALE quando os
 * inputs divergem dos parâmetros que o geraram. */
export type ScenarioComputed = {
  params: BalanceRunParams;
  result: ProductLineBalanceResult;
  fingerprint: string;
};

export type ScenarioState = StudyScenarioDraft & {
  computed: ScenarioComputed | null;
};

export type DraftSaveStatus =
  | "idle"
  | "saving"
  | "saved"
  | "save_error"
  | "storage_unavailable";

export type DraftRestoreNotice = "restored" | "restore_invalid" | "stale_reference" | null;

const AUTOSAVE_DEBOUNCE_MS = 400;

function safeSessionStorage(): Storage | null {
  try {
    return typeof window !== "undefined" ? window.sessionStorage : null;
  } catch {
    /* SecurityError (cookies/storage bloqueados) — edição continua em
     * memória com aviso honesto. */
    return null;
  }
}

function patchActive(
  scenarios: ScenarioState[],
  activeId: string,
  patch: (s: ScenarioState) => ScenarioState,
): ScenarioState[] {
  return scenarios.map((s) => (s.clientId === activeId ? patch(s) : s));
}

export function useRoutingStudyDraft({
  identity,
  productCode,
  branch,
  stage,
}: {
  identity: string | null;
  productCode: string;
  branch: string;
  stage: RoutingStageView | null;
}) {
  const context = useMemo<StudyDraftContext | null>(
    () =>
      stage
        ? {
            productCode,
            branch,
            stageKey: stage.key,
            sourceFingerprint: computeSourceFingerprint(stage),
          }
        : null,
    [productCode, branch, stage],
  );

  const storageRef = useRef<Storage | null | undefined>(undefined);
  const storage = () => {
    if (storageRef.current === undefined) {
      storageRef.current = safeSessionStorage();
    }
    return storageRef.current;
  };

  const [draft, setDraft] = useState<RoutingStudyDraft | null>(null);
  const [computed, setComputed] = useState<Record<string, ScenarioComputed>>({});
  const [status, setStatus] = useState<DraftSaveStatus>("idle");
  const [notice, setNotice] = useState<DraftRestoreNotice>(null);

  const storageKey = useMemo(
    () => (context ? buildStorageKey(identity, context) : null),
    [identity, context],
  );

  /* Restauração — só quando a chave do contexto muda (produto/filial/
   * estágio/identidade). AuthZ live já foi provada pelo fetch do
   * roteiro: se a consulta falhou, este componente nem monta o estudo. */
  useEffect(() => {
    setComputed({});
    if (!context || !storageKey) {
      setDraft(null);
      return;
    }
    const store = storage();
    if (!store) {
      setDraft(emptyDraft(context));
      setStatus("storage_unavailable");
      setNotice(null);
      return;
    }
    const raw = loadDraft(store, storageKey);
    if (!raw) {
      setDraft(emptyDraft(context));
      setStatus("idle");
      setNotice(null);
      return;
    }
    const parsed = parseDraft(raw, context);
    if (!parsed.ok) {
      if (parsed.reason !== "invalid_json") {
        /* schema/contexto divergente — descarta com aviso, nada de
         * falha silenciosa; storage do contexto anterior NÃO é
         * removido (pode pertencer a outra seleção legítima). */
        removeDraft(store, storageKey);
      }
      setDraft(emptyDraft(context));
      setStatus("idle");
      setNotice("restore_invalid");
      return;
    }
    /* Vínculos de operações: mantém só refs que ainda existem no
     * roteiro reconsultado — fonte autoridade sempre vence. */
    const opKeys = new Set(stage?.operations.map((o) => o.key) ?? []);
    const staleSource =
      parsed.draft.context.sourceFingerprint !== context.sourceFingerprint;
    const scenarios = parsed.draft.scenarios.map((s) => ({
      ...s,
      posts: s.posts.map((p) => ({
        ...p,
        operationRefs: p.operationRefs.filter((r) => opKeys.has(r)),
      })),
    }));
    setDraft({ ...parsed.draft, scenarios });
    setStatus("idle");
    setNotice(staleSource ? "stale_reference" : "restored");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [storageKey]);

  /* Autosave — debounce + flush em visibilitychange/unmount. Status só
   * mostra "salvo" depois da escrita confirmada pelo navegador. */
  const dirtyRef = useRef(false);
  const flushRef = useRef<() => void>(() => undefined);

  const flush = useCallback(() => {
    if (!dirtyRef.current || !draft || !storageKey) return;
    dirtyRef.current = false;
    const store = storage();
    const outcome = saveDraft(store, storageKey, {
      ...draft,
      savedAt: new Date().toISOString(),
    });
    setStatus(
      outcome === "saved"
        ? "saved"
        : outcome === "unavailable"
          ? "storage_unavailable"
          : "save_error",
    );
  }, [draft, storageKey]);

  flushRef.current = flush;

  useEffect(() => {
    if (!draft || !storageKey) return undefined;
    const timer = setTimeout(() => flushRef.current(), AUTOSAVE_DEBOUNCE_MS);
    const onVisibility = () => {
      if (document.visibilityState === "hidden") flushRef.current();
    };
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      clearTimeout(timer);
      document.removeEventListener("visibilitychange", onVisibility);
      flushRef.current();
    };
  }, [draft, storageKey]);

  const mutate = useCallback((fn: (d: RoutingStudyDraft) => RoutingStudyDraft) => {
    dirtyRef.current = true;
    setStatus("saving");
    setDraft((d) => (d ? fn(d) : d));
  }, []);

  /* --- cenários -------------------------------------------------------- */

  const updateInputs = useCallback(
    (patch: Partial<StudyInputs>) =>
      mutate((d) => ({
        ...d,
        scenarios: patchActive(d.scenarios, d.activeScenarioId, (s) => ({
          ...s,
          inputs: { ...s.inputs, ...patch },
        })),
      })),
    [mutate],
  );

  const setMode = useCallback(
    (mode: StudyMode) =>
      mutate((d) => ({
        ...d,
        scenarios: patchActive(d.scenarios, d.activeScenarioId, (s) => ({
          ...s,
          mode,
        })),
      })),
    [mutate],
  );

  const addScenario = useCallback(() => {
    mutate((d) => {
      if (d.scenarios.length >= STUDY_MAX_SCENARIOS) return d;
      const current = d.scenarios.find((s) => s.clientId === d.activeScenarioId);
      const next: StudyScenarioDraft = {
        ...newScenarioDraft(SCENARIO_LABELS[d.scenarios.length] ?? "?"),
        /* Novo cenário = nova configuração comparável a partir do estudo
         * atual — o anterior é preservado intacto na lista. */
        mode: current?.mode ?? "quick",
        inputs: { ...(current?.inputs ?? emptyInputs()) },
        posts: (current?.posts ?? []).map((p) => ({ ...p })),
      };
      return {
        ...d,
        activeScenarioId: next.clientId,
        scenarios: [...d.scenarios, next],
      };
    });
  }, [mutate]);

  const selectScenario = useCallback(
    (clientId: string) =>
      mutate((d) =>
        d.scenarios.some((s) => s.clientId === clientId)
          ? { ...d, activeScenarioId: clientId }
          : d,
      ),
    [mutate],
  );

  /* --- postos hipotéticos ----------------------------------------------- */

  const mutatePosts = useCallback(
    (fn: (posts: HypotheticalPost[]) => HypotheticalPost[]) =>
      mutate((d) => ({
        ...d,
        scenarios: patchActive(d.scenarios, d.activeScenarioId, (s) => ({
          ...s,
          posts: fn(s.posts),
        })),
      })),
    [mutate],
  );

  const addPost = useCallback(
    () =>
      mutatePosts((posts) =>
        posts.length >= STUDY_MAX_POSTS
          ? posts
          : [
              ...posts,
              {
                clientId: newClientId("post"),
                name: `Posto ${String(posts.length + 1).padStart(2, "0")}`,
                operationRefs: [],
                operators: null,
                parallelPositions: null,
                note: "",
              },
            ],
      ),
    [mutatePosts],
  );

  const patchPost = useCallback(
    (clientId: string, patch: Partial<HypotheticalPost>) =>
      mutatePosts((posts) =>
        posts.map((p) => (p.clientId === clientId ? { ...p, ...patch } : p)),
      ),
    [mutatePosts],
  );

  const removePost = useCallback(
    (clientId: string) =>
      mutatePosts((posts) => posts.filter((p) => p.clientId !== clientId)),
    [mutatePosts],
  );

  /** Ordenação local da hipótese — NUNCA altera a sequência oficial do
   * roteiro (a ordem de `stage.operations` não é tocada). */
  const movePost = useCallback(
    (clientId: string, direction: -1 | 1) =>
      mutatePosts((posts) => {
        const i = posts.findIndex((p) => p.clientId === clientId);
        const j = i + direction;
        if (i < 0 || j < 0 || j >= posts.length) return posts;
        const next = [...posts];
        [next[i], next[j]] = [next[j], next[i]];
        return next;
      }),
    [mutatePosts],
  );

  /* --- resultado transitório -------------------------------------------- */

  const attachResult = useCallback(
    (scenarioId: string, params: BalanceRunParams, result: ProductLineBalanceResult) =>
      setComputed((prev) => ({
        ...prev,
        [scenarioId]: { params, result, fingerprint: inputsFingerprint(params) },
      })),
    [],
  );

  /* --- limpar estudo ------------------------------------------------------ */

  /** Remove apenas a chave do contexto atual — nunca toca rascunhos de
   * outro produto/filial/usuário. Retorna false se a remoção não foi
   * confirmada (UI não pode afirmar limpeza de bytes não apagados). */
  const clearStudy = useCallback((): boolean => {
    const store = storage();
    const removed = storageKey ? removeDraft(store, storageKey) : false;
    if (!context) return false;
    setComputed({});
    const fresh = emptyDraft(context);
    setDraft(fresh);
    dirtyRef.current = false;
    setStatus(removed ? "idle" : store ? "save_error" : "storage_unavailable");
    setNotice(null);
    return removed;
  }, [context, storageKey]);

  /* --- seleção ------------------------------------------------------------ */

  const active: ScenarioState | null = useMemo(() => {
    if (!draft) return null;
    const s = draft.scenarios.find((x) => x.clientId === draft.activeScenarioId);
    return s ? { ...s, computed: computed[s.clientId] ?? null } : null;
  }, [draft, computed]);

  const scenarios: ScenarioState[] = useMemo(
    () =>
      (draft?.scenarios ?? []).map((s) => ({
        ...s,
        computed: computed[s.clientId] ?? null,
      })),
    [draft, computed],
  );

  return {
    ready: draft !== null,
    status,
    notice,
    clearNotice: () => setNotice(null),
    scenarios,
    active,
    activeScenarioId: draft?.activeScenarioId ?? null,
    updateInputs,
    setMode,
    addScenario,
    selectScenario,
    addPost,
    patchPost,
    removePost,
    movePost,
    attachResult,
    clearStudy,
    maxScenarios: STUDY_MAX_SCENARIOS,
    maxPosts: STUDY_MAX_POSTS,
  };
}

export type RoutingStudyDraftState = ReturnType<typeof useRoutingStudyDraft>;
