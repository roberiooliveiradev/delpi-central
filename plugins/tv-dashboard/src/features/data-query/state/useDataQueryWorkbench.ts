import {
  isDataTransformV1,
  isDataTransformV2,
  serializeComunicadoConfig,
  type ComunicadoBlock,
  type ComunicadoConfig,
  type ComunicadoDataSourceBlock,
} from "@delpi/tv-dashboard-presentation";
import { useCallback, useEffect, useReducer, useRef, useState } from "react";

import { dataQueryApi, type DataQueryApi } from "../data/dataQueryApi";
import {
  LEGACY_SAFE_CAPABILITIES,
} from "../domain/dataQueryCapabilities";
import type {
  DataQueryCapabilities,
  DataQueryDraft,
  DataQueryFunction,
  DataQueryMutationAction,
} from "../domain/dataQueryTypes";
import {
  dataQueryDraftReducer,
  INITIAL_WORKBENCH_STATE,
} from "./dataQueryDraftReducer";
import { applyDataQueryDraftsAtomically } from "./dataQueryTransaction";

function queryName(query: ComunicadoDataSourceBlock): string {
  return (
    query.dataBinding?.label?.trim() ||
    query.dataBinding?.operationId?.trim() ||
    `Fonte ${query.id.slice(0, 6)}`
  );
}

function draftFor(query: ComunicadoDataSourceBlock): DataQueryDraft {
  const v2 = isDataTransformV2(query.dataTransform) ? query.dataTransform : undefined;
  return {
    sourceId: query.id,
    queryName: queryName(query),
    persistedTransform: v2,
    persistedBinding: query.dataBinding,
    legacySteps: isDataTransformV1(query.dataTransform) ? query.dataTransform.steps : [],
    script: v2?.script ?? "",
    compiled: null,
    selectedStepName: null,
    dirty: false,
    queryNameDirty: false,
    undoStack: [],
    redoStack: [],
  };
}

export function useDataQueryCapabilities(api: DataQueryApi = dataQueryApi) {
  const [capabilities, setCapabilities] =
    useState<DataQueryCapabilities>(LEGACY_SAFE_CAPABILITIES);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const controller = new AbortController();
    void api
      .capabilities(controller.signal)
      .then(setCapabilities)
      .catch(() => setCapabilities(LEGACY_SAFE_CAPABILITIES))
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [api]);
  return { capabilities, loading };
}

export function useDataQueryFunctions(enabled: boolean, api: DataQueryApi = dataQueryApi) {
  const [items, setItems] = useState<DataQueryFunction[]>([]);
  const [loading, setLoading] = useState(false);
  const sequence = useRef(0);
  useEffect(() => {
    if (!enabled) return;
    const controller = new AbortController();
    const request = ++sequence.current;
    setLoading(true);
    void api
      .functions(controller.signal)
      .then((result) => {
        if (request === sequence.current) setItems(result);
      })
      .catch(() => {
        if (!controller.signal.aborted && request === sequence.current) setItems([]);
      })
      .finally(() => {
        if (request === sequence.current) setLoading(false);
      });
    return () => controller.abort();
  }, [api, enabled]);
  return { items, loading };
}

type Options = {
  open: boolean;
  queries: ComunicadoDataSourceBlock[];
  config: ComunicadoConfig;
  playlistId: string;
  initialSourceId?: string | null;
  api?: DataQueryApi;
};

export function useDataQueryWorkbench({
  open,
  queries,
  config,
  playlistId,
  initialSourceId = null,
  api = dataQueryApi,
}: Options) {
  const [state, dispatch] = useReducer(dataQueryDraftReducer, INITIAL_WORKBENCH_STATE);
  const stateRef = useRef(state);
  stateRef.current = state;
  const configRef = useRef(config);
  configRef.current = config;
  const compileSequence = useRef(0);
  const previewSequence = useRef(0);
  const compileController = useRef<AbortController | null>(null);
  const previewController = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!open) {
      compileController.current?.abort();
      previewController.current?.abort();
      return;
    }
    const drafts = Object.fromEntries(queries.map((query) => [query.id, draftFor(query)]));
    const active =
      (initialSourceId && drafts[initialSourceId] ? initialSourceId : null) ??
      queries[0]?.id ??
      null;
    dispatch({ type: "reset", drafts, activeQueryId: active });
  }, [open, queries, initialSourceId]);

  const activeDraft = state.activeQueryId
    ? state.draftByQueryId[state.activeQueryId] ?? null
    : null;

  const currentQueryBindings = useCallback(
    () =>
      Object.values(stateRef.current.draftByQueryId).map((draft) => ({
        name: draft.queryName,
        sourceId: draft.sourceId,
      })),
    [],
  );

  const compileInput = useCallback(
    (script: string, targetStepName: string | null) => ({
      script,
      queryBindings: currentQueryBindings(),
      sourceSchema: stateRef.current.preview.value?.columns ?? [],
      targetStepName,
    }),
    [currentQueryBindings],
  );

  const nativeConfigWithDrafts = useCallback(() => {
    const drafts = stateRef.current.draftByQueryId;
    return serializeComunicadoConfig({
      ...configRef.current,
      blocks: (configRef.current.blocks ?? []).map((block) => {
        const draft = drafts[block.id];
        return draft?.script
          ? {
              ...block,
              dataTransform: {
                version: 2 as const,
                language: "m-delpi-v1" as const,
                script: draft.script,
              },
            }
          : block;
      }),
    });
  }, []);

  const preview = useCallback(
    async (queryId: string, forceRefresh = false) => {
      const draft = stateRef.current.draftByQueryId[queryId];
      const query = queries.find((item) => item.id === queryId);
      if (!draft || !query || !draft.script) return;
      previewController.current?.abort();
      const controller = new AbortController();
      previewController.current = controller;
      const sequence = ++previewSequence.current;
      dispatch({ type: "request", kind: "preview", sequence });
      try {
        const { resolved: _resolved, ...block } = query;
        const result = await api.preview(
          {
            block: {
              ...block,
              dataTransform: {
                version: 2,
                language: "m-delpi-v1",
                script: draft.script,
              },
            },
            nativeConfig: nativeConfigWithDrafts(),
            playlistId,
            targetStepName: draft.selectedStepName ?? "Fonte",
            forceRefresh,
          },
          controller.signal,
        );
        dispatch({ type: "previewed", sequence, result });
      } catch (error) {
        if (controller.signal.aborted) return;
        dispatch({
          type: "failed",
          kind: "preview",
          sequence,
          error: error instanceof Error ? error.message : "Falha ao carregar prévia.",
        });
      }
    },
    [api, nativeConfigWithDrafts, playlistId, queries],
  );

  const compileOrConvert = useCallback(
    async (queryId: string, dirty = false) => {
      const draft = stateRef.current.draftByQueryId[queryId];
      if (!draft) return null;
      compileController.current?.abort();
      const controller = new AbortController();
      compileController.current = controller;
      const sequence = ++compileSequence.current;
      dispatch({ type: "request", kind: "compile", sequence });
      try {
        const result = draft.script
          ? await api.compile(compileInput(draft.script, draft.selectedStepName), controller.signal)
          : await api.mutate(
              { script: "", queryBindings: currentQueryBindings() },
              { type: "convert_legacy", legacySteps: draft.legacySteps },
              controller.signal,
            );
        dispatch({ type: "compiled", queryId, sequence, result, dirty });
        window.setTimeout(() => void preview(queryId), 0);
        return result;
      } catch (error) {
        if (controller.signal.aborted) return null;
        dispatch({
          type: "failed",
          kind: "compile",
          sequence,
          error: error instanceof Error ? error.message : "Falha ao compilar consulta.",
        });
        return null;
      }
    },
    [api, compileInput, currentQueryBindings, preview],
  );

  const compileScript = useCallback(
    async (script: string) => {
      const draft = stateRef.current.activeQueryId
        ? stateRef.current.draftByQueryId[stateRef.current.activeQueryId]
        : null;
      if (!draft || !script.trim()) return null;
      dispatch({ type: "edit_script", queryId: draft.sourceId, script });
      compileController.current?.abort();
      const controller = new AbortController();
      compileController.current = controller;
      const sequence = ++compileSequence.current;
      dispatch({ type: "request", kind: "compile", sequence });
      try {
        const result = await api.compile(
          compileInput(script, draft.selectedStepName),
          controller.signal,
        );
        dispatch({
          type: "compiled",
          queryId: draft.sourceId,
          sequence,
          result,
          dirty: true,
        });
        window.setTimeout(() => void preview(draft.sourceId), 0);
        return result;
      } catch (error) {
        if (controller.signal.aborted) return null;
        dispatch({
          type: "failed",
          kind: "compile",
          sequence,
          error: error instanceof Error ? error.message : "Falha ao compilar consulta.",
        });
        return null;
      }
    },
    [api, compileInput, preview],
  );

  useEffect(() => {
    if (!open || !state.activeQueryId) return;
    const draft = state.draftByQueryId[state.activeQueryId];
    if (!draft || draft.compiled) return;
    void compileOrConvert(draft.sourceId);
  }, [compileOrConvert, open, state.activeQueryId, state.draftByQueryId]);

  const mutate = useCallback(
    async (action: DataQueryMutationAction) => {
      const draft = stateRef.current.activeQueryId
        ? stateRef.current.draftByQueryId[stateRef.current.activeQueryId]
        : null;
      if (!draft) return;
      let script = draft.script;
      if (!script) {
        const converted = await compileOrConvert(draft.sourceId);
        script = converted?.canonicalScript ?? "";
      }
      if (!script) return;
      compileController.current?.abort();
      const controller = new AbortController();
      compileController.current = controller;
      const sequence = ++compileSequence.current;
      dispatch({ type: "request", kind: "compile", sequence });
      try {
        const result = await api.mutate(
          {
            ...compileInput(script, draft.selectedStepName),
          },
          action,
          controller.signal,
        );
        dispatch({
          type: "compiled",
          queryId: draft.sourceId,
          sequence,
          result,
          dirty: true,
        });
        window.setTimeout(() => void preview(draft.sourceId), 0);
      } catch (error) {
        if (controller.signal.aborted) return;
        dispatch({
          type: "failed",
          kind: "compile",
          sequence,
          error: error instanceof Error ? error.message : "Falha ao alterar consulta.",
        });
      }
    },
    [api, compileInput, compileOrConvert, preview],
  );

  const renameQuery = useCallback(
    async (newName: string) => {
      const activeId = stateRef.current.activeQueryId;
      const active = activeId ? stateRef.current.draftByQueryId[activeId] : null;
      const normalized = newName.trim();
      if (!active || !normalized || normalized === active.queryName) return;
      if (
        Object.values(stateRef.current.draftByQueryId).some(
          (draft) => draft.sourceId !== active.sourceId && draft.queryName === normalized,
        )
      ) {
        throw new Error("Já existe uma consulta com esse nome.");
      }
      compileController.current?.abort();
      const controller = new AbortController();
      compileController.current = controller;
      const sequence = ++compileSequence.current;
      dispatch({ type: "request", kind: "compile", sequence });
      const bindings = currentQueryBindings().map((item) =>
        item.sourceId === active.sourceId ? { ...item, name: normalized } : item,
      );
      try {
        const drafts = Object.values(stateRef.current.draftByQueryId);
        const results = await Promise.all(
          drafts.map(async (draft) => {
            const script = draft.script
              ? draft.script
              : (
                  await api.mutate(
                    { script: "", queryBindings: bindings },
                    { type: "convert_legacy", legacySteps: draft.legacySteps },
                    controller.signal,
                  )
                ).canonicalScript ?? "";
            return api.mutate(
              {
                script,
                queryBindings: bindings,
                sourceSchema:
                  draft.sourceId === active.sourceId
                    ? stateRef.current.preview.value?.columns ?? []
                    : [],
                targetStepName: draft.selectedStepName,
              },
              { type: "rename_query", from: active.queryName, to: normalized },
              controller.signal,
            );
          }),
        );
        dispatch({ type: "rename_query", queryId: active.sourceId, queryName: normalized });
        results.forEach((result, index) => {
          const draft = drafts[index];
          if (!draft) return;
          dispatch({
            type: "compiled",
            queryId: draft.sourceId,
            sequence,
            result,
            dirty: result.canonicalScript !== draft.script || draft.sourceId === active.sourceId,
          });
        });
      } catch (error) {
        if (controller.signal.aborted) return;
        dispatch({
          type: "failed",
          kind: "compile",
          sequence,
          error: error instanceof Error ? error.message : "Falha ao renomear consulta.",
        });
        throw error;
      }
    },
    [api, currentQueryBindings],
  );

  const apply = useCallback(
    async (
      updateBlocksAtomically: (
        patches: ReadonlyArray<{ blockId: string; patch: Partial<ComunicadoBlock> }>,
      ) => void,
    ) => {
      return applyDataQueryDraftsAtomically(
        Object.values(stateRef.current.draftByQueryId),
        (draft) =>
          api.compile({ script: draft.script, queryBindings: currentQueryBindings(), targetStepName: null }),
        updateBlocksAtomically,
      );
    },
    [api, currentQueryBindings],
  );

  const selectStep = useCallback(
    (stepName: string | null) => {
      dispatch({ type: "select_step", stepName });
      const queryId = stateRef.current.activeQueryId;
      if (queryId) window.setTimeout(() => void preview(queryId), 0);
    },
    [preview],
  );

  return {
    state,
    activeDraft,
    dispatch,
    mutate,
    compileScript,
    renameQuery,
    preview: (force = false) =>
      stateRef.current.activeQueryId
        ? preview(stateRef.current.activeQueryId, force)
        : Promise.resolve(),
    selectStep,
    apply,
  };
}
