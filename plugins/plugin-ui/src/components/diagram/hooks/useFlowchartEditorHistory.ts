import { useCallback, useRef, useState } from "react";

import type { FlowchartV1 } from "../types/diagram";
import {
  emptyFlowchartHistory,
  pushFlowchartHistoryPast,
  redoFlowchartHistory,
  undoFlowchartHistory,
  type FlowchartHistoryStacks,
} from "./flowchartEditorHistory";

export {
  cloneFlowchartSnapshot,
  FLOWCHART_EDITOR_HISTORY_LIMIT,
} from "./flowchartEditorHistory";

/**
 * Pilha local past/future para o editor de diagrama (padrão TV Dashboard / comunicado).
 * Snapshots são FlowchartV1 completos — sem persistência remota.
 */
export function useFlowchartEditorHistory() {
  const [historyTick, setHistoryTick] = useState(0);
  const stacksRef = useRef<FlowchartHistoryStacks>(emptyFlowchartHistory());
  const applyingRef = useRef(false);

  const bump = useCallback(() => {
    setHistoryTick((tick) => tick + 1);
  }, []);

  const pushPast = useCallback(
    (snapshot: FlowchartV1) => {
      if (applyingRef.current) return;
      stacksRef.current = pushFlowchartHistoryPast(stacksRef.current, snapshot);
      bump();
    },
    [bump],
  );

  const undo = useCallback(
    (current: FlowchartV1, apply: (next: FlowchartV1) => void) => {
      const result = undoFlowchartHistory(stacksRef.current, current);
      if (!result) return;
      stacksRef.current = result.stacks;
      applyingRef.current = true;
      try {
        apply(result.next);
      } finally {
        applyingRef.current = false;
      }
      bump();
    },
    [bump],
  );

  const redo = useCallback(
    (current: FlowchartV1, apply: (next: FlowchartV1) => void) => {
      const result = redoFlowchartHistory(stacksRef.current, current);
      if (!result) return;
      stacksRef.current = result.stacks;
      applyingRef.current = true;
      try {
        apply(result.next);
      } finally {
        applyingRef.current = false;
      }
      bump();
    },
    [bump],
  );

  const reset = useCallback(() => {
    stacksRef.current = emptyFlowchartHistory();
    bump();
  }, [bump]);

  void historyTick;

  return {
    pushPast,
    undo,
    redo,
    reset,
    canUndo: stacksRef.current.past.length > 0,
    canRedo: stacksRef.current.future.length > 0,
    applyingRef,
    historyTick,
  };
}
