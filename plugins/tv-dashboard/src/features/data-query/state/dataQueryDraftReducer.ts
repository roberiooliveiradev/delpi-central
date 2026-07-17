import type {
  DataQueryCompileResult,
  DataQueryDraft,
  DataQueryPreview,
} from "../domain/dataQueryTypes";
import { reconcileSelectedStepName } from "./dataQuerySelection";

export type AsyncState<T> =
  | { status: "idle"; value: T | null; error: null; sequence: number }
  | { status: "loading"; value: T | null; error: null; sequence: number }
  | { status: "success"; value: T; error: null; sequence: number }
  | { status: "error"; value: T | null; error: string; sequence: number };

export type DataQueryWorkbenchState = {
  activeQueryId: string | null;
  draftByQueryId: Record<string, DataQueryDraft>;
  selectedColumnKey: string | null;
  compile: AsyncState<DataQueryCompileResult>;
  preview: AsyncState<DataQueryPreview>;
};

export type DataQueryDraftAction =
  | { type: "reset"; drafts: Record<string, DataQueryDraft>; activeQueryId: string | null }
  | { type: "select_query"; queryId: string }
  | { type: "select_step"; stepName: string | null }
  | { type: "select_column"; columnKey: string | null }
  | { type: "request"; kind: "compile" | "preview"; sequence: number }
  | {
      type: "compiled";
      queryId: string;
      sequence: number;
      result: DataQueryCompileResult;
      dirty: boolean;
    }
  | { type: "previewed"; sequence: number; result: DataQueryPreview }
  | { type: "failed"; kind: "compile" | "preview"; sequence: number; error: string };

export const INITIAL_WORKBENCH_STATE: DataQueryWorkbenchState = {
  activeQueryId: null,
  draftByQueryId: {},
  selectedColumnKey: null,
  compile: { status: "idle", value: null, error: null, sequence: 0 },
  preview: { status: "idle", value: null, error: null, sequence: 0 },
};

export function dataQueryDraftReducer(
  state: DataQueryWorkbenchState,
  action: DataQueryDraftAction,
): DataQueryWorkbenchState {
  if (action.type === "reset") {
    return {
      ...INITIAL_WORKBENCH_STATE,
      activeQueryId: action.activeQueryId,
      draftByQueryId: action.drafts,
    };
  }
  if (action.type === "select_query") {
    return { ...state, activeQueryId: action.queryId, selectedColumnKey: null };
  }
  if (action.type === "select_column") {
    return { ...state, selectedColumnKey: action.columnKey };
  }
  if (action.type === "select_step") {
    if (!state.activeQueryId) return state;
    const draft = state.draftByQueryId[state.activeQueryId];
    if (!draft) return state;
    return {
      ...state,
      draftByQueryId: {
        ...state.draftByQueryId,
        [draft.sourceId]: { ...draft, selectedStepName: action.stepName },
      },
    };
  }
  if (action.type === "request") {
    return {
      ...state,
      [action.kind]: {
        status: "loading",
        value: state[action.kind].value,
        error: null,
        sequence: action.sequence,
      },
    };
  }
  if (action.type === "compiled") {
    if (action.sequence !== state.compile.sequence) return state;
    const draft = state.draftByQueryId[action.queryId];
    if (!draft) return state;
    const selectedStepName = reconcileSelectedStepName(
      draft.selectedStepName,
      action.result.steps,
    );
    return {
      ...state,
      draftByQueryId: {
        ...state.draftByQueryId,
        [action.queryId]: {
          ...draft,
          script: action.result.canonicalScript ?? draft.script,
          compiled: action.result,
          selectedStepName,
          dirty: draft.dirty || action.dirty,
        },
      },
      compile: {
        status: action.result.diagnostics.some((item) => item.severity === "error")
          ? "error"
          : "success",
        value: action.result,
        error: action.result.diagnostics.find((item) => item.severity === "error")?.message ?? null,
        sequence: action.sequence,
      } as AsyncState<DataQueryCompileResult>,
    };
  }
  if (action.type === "previewed") {
    if (action.sequence !== state.preview.sequence) return state;
    return {
      ...state,
      preview: {
        status: "success",
        value: action.result,
        error: null,
        sequence: action.sequence,
      },
    };
  }
  if (action.sequence !== state[action.kind].sequence) return state;
  return {
    ...state,
    [action.kind]: {
      status: "error",
      value: state[action.kind].value,
      error: action.error,
      sequence: action.sequence,
    },
  };
}
