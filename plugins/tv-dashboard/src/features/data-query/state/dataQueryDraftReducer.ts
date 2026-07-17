import type { DataTableSelection } from "@delpi/plugin-ui/index";

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
  selection: DataTableSelection | null;
  compile: AsyncState<DataQueryCompileResult>;
  preview: AsyncState<DataQueryPreview>;
};

export type DataQueryDraftAction =
  | { type: "reset"; drafts: Record<string, DataQueryDraft>; activeQueryId: string | null }
  | { type: "select_query"; queryId: string }
  | { type: "select_step"; stepName: string | null }
  | { type: "select_column"; columnKey: string | null }
  | { type: "set_selection"; selection: DataTableSelection | null }
  | { type: "edit_script"; queryId: string; script: string }
  | { type: "undo_script"; queryId: string }
  | { type: "redo_script"; queryId: string }
  | { type: "rename_query"; queryId: string; queryName: string }
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
  selection: null,
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
    return {
      ...state,
      activeQueryId: action.queryId,
      selectedColumnKey: null,
      selection: null,
    };
  }
  if (action.type === "select_column") {
    const columnKey = action.columnKey || null;
    return {
      ...state,
      selectedColumnKey: columnKey,
      selection: columnKey ? { kind: "column", keys: [columnKey] } : null,
    };
  }
  if (action.type === "set_selection") {
    const selectedColumnKey =
      action.selection?.kind === "column"
        ? action.selection.keys[0] ?? null
        : action.selection?.kind === "cell"
          ? action.selection.cells[0]?.columnKey ?? null
          : action.selection?.kind === "row"
            ? null
            : state.selectedColumnKey;
    return { ...state, selection: action.selection, selectedColumnKey };
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
  if (
    action.type === "edit_script" ||
    action.type === "undo_script" ||
    action.type === "redo_script" ||
    action.type === "rename_query"
  ) {
    const draft = state.draftByQueryId[action.queryId];
    if (!draft) return state;
    let next = draft;
    if (action.type === "edit_script" && action.script !== draft.script) {
      next = {
        ...draft,
        script: action.script,
        compiled: null,
        dirty: true,
        undoStack: [...draft.undoStack, draft.script].slice(-100),
        redoStack: [],
      };
    } else if (action.type === "undo_script" && draft.undoStack.length > 0) {
      const script = draft.undoStack[draft.undoStack.length - 1]!;
      next = {
        ...draft,
        script,
        compiled: null,
        dirty: true,
        undoStack: draft.undoStack.slice(0, -1),
        redoStack: [draft.script, ...draft.redoStack].slice(0, 100),
      };
    } else if (action.type === "redo_script" && draft.redoStack.length > 0) {
      const [script, ...redoStack] = draft.redoStack;
      next = {
        ...draft,
        script: script!,
        compiled: null,
        dirty: true,
        undoStack: [...draft.undoStack, draft.script].slice(-100),
        redoStack,
      };
    } else if (action.type === "rename_query" && action.queryName !== draft.queryName) {
      next = { ...draft, queryName: action.queryName, queryNameDirty: true, dirty: true };
    }
    return next === draft
      ? state
      : { ...state, draftByQueryId: { ...state.draftByQueryId, [action.queryId]: next } };
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
